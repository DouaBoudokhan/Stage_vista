import React, { useState, useEffect } from 'react';
import { StyleSheet, View, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { Text, Surface, TextInput, IconButton, Divider, useTheme } from 'react-native-paper';
import { useProducts, useTickets, useAssignStock, useRecommendTicket } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { YOLOCameraHUD } from '../components/YOLOCameraHUD';
import { TicketCard } from '../components/Cards';
import { PrimaryButton, SecondaryButton } from '../components/AppButtons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import type { Product, Ticket, ScanResult } from '../types';

// ─── Workflow Steps ───────────────────────────────────
// 1: Scan Item (YOLO detection)
// 2: Choose Quantity
// 3: Choose Assignment Method (AI / Manual List / Ticket ID)
// 4: Review & Confirm
// 5: Success

type WorkflowStep = 1 | 2 | 3 | 4 | 5;

export default function WorkflowAssignScreen({ route, navigation }: any) {
  const theme = useTheme();

  // Route params for preselected items (coming from product details)
  const preselected = route.params?.preselectedProduct as Product | undefined;

  // API calls
  const { data: products } = useProducts();
  const {
    data: tickets,
    isLoading: ticketsLoading,
    isFetching: ticketsFetching,
    isError: ticketsIsError,
    error: ticketsError,
  } = useTickets();
  const assignStockMutation = useAssignStock();
  const recommendTicketMutation = useRecommendTicket();

  // Workflow State
  const [step, setStep] = useState<WorkflowStep>(preselected ? 2 : 1);
  const [hudVisible, setHudVisible] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(preselected ?? null);
  const [productScan, setProductScan] = useState<ScanResult | null>(null);
  const [quantity, setQuantity] = useState<number>(1);
  const [method, setMethod] = useState<'ai' | 'list' | 'id'>('ai');
  const [availableQuantity, setAvailableQuantity] = useState<number>(preselected?.quantity ?? 0);

  // Assignment tracking
  const [targetTicket, setTargetTicket] = useState<Ticket | null>(null);
  const [aiRecommendation, setAiRecommendation] = useState<any>(null);
  const [recommendationList, setRecommendationList] = useState<any[]>([]);
  const [ticketIdInput, setTicketIdInput] = useState('');
  const [idValidationMsg, setIdValidationMsg] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  // Multi-unit assignment tracking
  const [assignedRecords, setAssignedRecords] = useState<any[]>([]);
  const [pendingAssignment, setPendingAssignment] = useState<any>(null);
  const [totalRequested, setTotalRequested] = useState<number>(1);
  
  // Check for Jira errors
  useEffect(() => {
    if (ticketsIsError && ticketsError) {
      console.error('[workflow2] Jira error:', ticketsError);
      const errorMsg = (ticketsError as any)?.response?.data?.detail || (ticketsError as any)?.message || 'Failed to fetch tickets from Jira';
      Alert.alert(
        'Jira Service Unavailable',
        `Cannot fetch tickets from Jira: ${errorMsg}\n\nPlease check:\n- Jira credentials are configured\n- Jira service is accessible\n- Network connection is active`,
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    }
  }, [ticketsIsError, ticketsError]);

  useEffect(() => {
    console.log('[workflow2] tickets query state:', {
      isLoading: ticketsLoading,
      isFetching: ticketsFetching,
      isError: ticketsIsError,
      error: ticketsError,
      ticketsLength: tickets ? tickets.length : undefined,
    });
  }, [tickets, ticketsLoading, ticketsFetching, ticketsIsError, ticketsError]);

  // ─── Product Detection (YOLO) ─────────────────────────
  const handleCameraResult = async (result: any) => {
    setHudVisible(false);
    if (!result) return;

    setProductScan({
      ...result,
      capturedImageUri: result.capturedImageUri,
      confidence: result.confidence,
    } as ScanResult);

    // Fuzzy matching against the product catalog
    const normalize = (s: any) => String(s ?? '').toLowerCase().trim();
    const rRef = normalize(result.reference);
    const rCat = normalize(result.category || result.detectedObject || result.equipment_type);

    console.log('[workflow2] handleCameraResult - rRef:', rRef, 'rCat:', rCat);

    let found: Product | undefined;
    if (products && products.length > 0) {
      // Exact-ish match first
      for (const p of products) {
        const nRef = normalize(p.ref);
        const nCat = normalize(p.category);
        const nName = normalize(p.name);
        const refCond = !!(rRef && nRef && (nRef === rRef || nRef.includes(rRef) || rRef.includes(nRef)));
        const catCond = !!(rCat && (nCat === rCat || nName.includes(rCat) || nCat.includes(rCat)));
        if (refCond || catCond) {
          found = p;
          break;
        }
      }

      // Fallback: score by partial matches
      if (!found) {
        let best: { p: Product; score: number } | null = null;
        for (const p of products) {
          let score = 0;
          const nName = normalize(p.name);
          const nCat = normalize(p.category);
          const nBrand = normalize(p.brand);
          if (rCat && nName.includes(rCat)) score += 3;
          if (rCat && nCat.includes(rCat)) score += 2;
          if (rCat && nBrand.includes(rCat)) score += 1;
          if (rRef && normalize(p.ref || '').includes(rRef)) score += 4;
          if (score > 0 && (!best || score > best.score)) best = { p, score };
        }
        if (best && best.score >= 2) {
          found = best.p;
        }
      }
    }

    if (found) {
      console.log('[workflow2] matched product:', found.name, 'qty:', found.quantity);
      setSelectedProduct(found);
      setAvailableQuantity(found.quantity ?? 0);
      setQuantity(1);
    } else {
      console.log('[workflow2] no product matched');
      setSelectedProduct(null);
    }
  };

  // ─── Quantity Handling ─────────────────────────────────
  const handleQuantityChange = (text: string) => {
    const n = parseInt(text.replace(/[^0-9]/g, ''), 10);
    if (Number.isNaN(n) || n <= 0) setQuantity(1);
    else setQuantity(n);
  };

  // ─── AI Recommendation ────────────────────────────────
  const getAiRecommendation = async () => {
    if (!selectedProduct) return;
    
    // Check if tickets are available
    if (ticketsIsError) {
      Alert.alert(
        'Jira Service Error',
        'Cannot fetch tickets from Jira. Please ensure Jira service is configured and accessible.',
        [{ text: 'OK' }]
      );
      return;
    }
    
    if (!tickets || tickets.length === 0) {
      Alert.alert(
        'No Tickets Available',
        'No open tickets found in Jira. Please create a ticket in Jira first.',
        [{ text: 'OK' }]
      );
      return;
    }
    
    setAiLoading(true);
    setAiRecommendation(null);
    setRecommendationList([]);
    console.log('[workflow2] getAiRecommendation called:', {
      step,
      method,
      selectedProductId: selectedProduct.id,
      selectedProductRef: selectedProduct.ref,
      selectedProductCategory: selectedProduct.category,
      selectedProductBrand: selectedProduct.brand,
      ticketsLength: tickets.length,
    });
    try {
      const rec = await recommendTicketMutation.mutateAsync({
        productRef: selectedProduct.ref,
        category: selectedProduct.category,
        brand: selectedProduct.brand,
        quantity,
        availableQuantity,
        tickets: tickets || [],
      });
      setAiRecommendation(rec);
      setRecommendationList(rec.recommendations || []);
      if (rec.ticket) {
        setTargetTicket(rec.ticket);
      }
    } catch (e: any) {
      console.error('[workflow2] AI Recommendation failed:', e);
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to generate recommendations';
      Alert.alert(
        'AI Recommendation Failed',
        `Could not analyze tickets: ${errorMsg}`,
        [{ text: 'OK' }]
      );
    } finally {
      setAiLoading(false);
    }
  };

  // Trigger AI when entering step 3 with method='ai'
  useEffect(() => {
    if (step === 3 && method === 'ai' && selectedProduct && !aiRecommendation) {
      console.log('[workflow2] step/method effect firing getAiRecommendation:', {
        step,
        method,
        selectedProductId: selectedProduct.id,
        ticketsLoading,
        ticketsFetching,
        ticketsLength: tickets ? tickets.length : undefined,
      });
      getAiRecommendation();
    }
  }, [step, method, selectedProduct, aiRecommendation, ticketsLoading, ticketsFetching, tickets]);

  // ─── Ticket ID Validation ─────────────────────────────
  const handleValidateId = () => {
    const allTickets = tickets || [];
    const found = allTickets.find(
      (t) => t.id.toLowerCase() === ticketIdInput.trim().toLowerCase()
    );
    if (found) {
      setTargetTicket(found);
      setIdValidationMsg('✅ Valid Ticket Found!');
    } else {
      setIdValidationMsg('❌ Ticket Not Found.');
      setTargetTicket(null);
    }
  };

  // ─── Review Assignment ─────────────────────────────────
  const handleReviewAssignment = () => {
    if (!selectedProduct || !targetTicket) {
      Alert.alert('Select a ticket', 'Choose a ticket before reviewing the assignment.');
      return;
    }
    setStep(4);
  };

  // ─── Confirm Assignment ────────────────────────────────
  const handleConfirmAssignment = async () => {
    if (!selectedProduct || !targetTicket) return;

    // Assign 1 unit at a time for multi-unit assignment
    const qtyToAssign = quantity > 1 ? 1 : quantity;

    try {
      await assignStockMutation.mutateAsync({
        productId: selectedProduct.id,
        quantity: qtyToAssign,
        ticketId: targetTicket.id,
        technician: 'admin',
      });

      const record = { product: selectedProduct, ticket: targetTicket, quantity: qtyToAssign };
      setAssignedRecords((prev) => [...prev, record]);
      setPendingAssignment(record);

      const remaining = quantity - qtyToAssign;
      if (remaining > 0) {
        // Step 7: Multiple Quantity Handling — loop back
        Alert.alert(
          'Unit Assigned!',
          `${qtyToAssign} ${selectedProduct.name} assigned to ticket ${targetTicket.id}.\n\n${remaining} unit(s) remaining to be assigned.`,
          [
            {
              text: 'Assign Next Unit',
              onPress: () => {
                setQuantity(remaining);
                setTargetTicket(null);
                setAiRecommendation(null);
                setRecommendationList([]);
                setStep(3); // Loop back to ticket selection
              },
            },
          ]
        );
      } else {
        // All units assigned → Step 5: Success
        setStep(5);
      }
    } catch (e: any) {
      const serverDetail =
        e?.response?.data?.detail || e?.message || 'Failed to assign stock.';
      Alert.alert(
        'Assignment Failed',
        typeof serverDetail === 'string' ? serverDetail : JSON.stringify(serverDetail)
      );
    }
  };

  // ─── Navigation Helpers ────────────────────────────────
  const handleBackToScan = () => {
    setSelectedProduct(null);
    setProductScan(null);
    setQuantity(1);
    setAvailableQuantity(0);
    setTargetTicket(null);
    setAiRecommendation(null);
    setRecommendationList([]);
    setStep(1);
  };

  const handleJumpToStep = (targetStep: number) => {
    const t = targetStep as WorkflowStep;
    if (t === step) return;
    if (t < step) { setStep(t); return; }
    // Forward jumps require guards
    if (t === 2 && selectedProduct) setStep(2);
    else if (t === 3 && selectedProduct) setStep(3);
    else if (t === 4 && selectedProduct && targetTicket) setStep(4);
    else if (t === 5 && pendingAssignment) setStep(5);
  };

  // ─── Helper: display ticket name ──────────────────────
  const getTicketDisplayTitle = (t: any) => {
    return t?.title ?? t?.requestedEquipment ?? t?.id ?? 'Unknown';
  };

  const getTicketRequester = (t: any) => {
    return t?.requester ?? 'Unknown';
  };

  const getTicketDepartment = (t: any) => {
    return t?.category ?? t?.department ?? '';
  };

  const STEP_COUNT = 5;

  return (
    <View style={styles.container}>
      {/* ── Header ─────────────────────────────── */}
      <View style={styles.headerBar}>
        <View>
          <Text style={styles.workflowTag}>Workflow 2/2</Text>
          <Text style={styles.headerTitle}>Assign Equipment</Text>
        </View>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      </View>

      {/* ── Step Indicator ─────────────────────── */}
      <View style={styles.stepperRow}>
        {[1, 2, 3, 4, 5].map((s) => {
          const isActive = s === step;
          const isCompleted = s < step;
          return (
            <TouchableOpacity
              key={s}
              activeOpacity={isCompleted ? 0.6 : 1}
              onPress={() => handleJumpToStep(s)}
              style={{ flex: 1, marginHorizontal: 2 }}
              disabled={!isCompleted}
            >
              <View
                style={[
                  styles.stepIndicator,
                  isActive ? styles.stepActive : isCompleted ? styles.stepCompleted : styles.stepInactive,
                ]}
              />
            </TouchableOpacity>
          );
        })}
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* ═══════════════════════════════════════════
            STEP 1: Scan Item
            ═══════════════════════════════════════════ */}
        {step === 1 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 1: Scan Equipment</Text>
            <Text style={styles.stepDesc}>
              Point the camera at the equipment. YOLO AI will identify the product category.
            </Text>

            {productScan && selectedProduct ? (
              <Surface style={styles.dataCard} elevation={1}>
                <View style={styles.cardHeader}>
                  <Text style={styles.visualEmoji}>{selectedProduct.image ?? '🤖'}</Text>
                  <View style={{ flex: 1 }}>
                    <View style={styles.yoloBadge}>
                      <Text style={styles.yoloBadgeText}>YOLO Detected</Text>
                    </View>
                    <Text style={styles.productName}>
                      {productScan.category ?? selectedProduct.name ?? 'Detected Item'}
                    </Text>
                    <Text style={styles.productRef}>
                      Confidence: {productScan.confidence ?? 0}%
                    </Text>
                    <Text style={[styles.productStockText, { color: Colors.success }]}>
                      Available: {selectedProduct.quantity} units
                    </Text>
                  </View>
                </View>

                <View style={styles.navButtonRow}>
                  <SecondaryButton
                    title="Scan Again"
                    onPress={() => {
                      setProductScan(null);
                      setSelectedProduct(null);
                      setHudVisible(true);
                    }}
                    icon="camera-retake"
                    style={{ flex: 1, marginRight: 8 }}
                  />
                  <PrimaryButton
                    title="Choose Quantity"
                    onPress={() => {
                      setAvailableQuantity(selectedProduct.quantity);
                      setStep(2);
                    }}
                    icon="arrow-right"
                    style={{ flex: 1, marginLeft: 8 }}
                  />
                </View>
              </Surface>
            ) : productScan && !selectedProduct ? (
              <Surface style={styles.dataCard} elevation={1}>
                <View style={styles.cardHeader}>
                  <Text style={styles.visualEmoji}>⚠️</Text>
                  <View style={{ flex: 1 }}>
                    <View style={styles.yoloBadge}>
                      <Text style={styles.yoloBadgeText}>YOLO Detected</Text>
                    </View>
                    <Text style={styles.productName}>
                      {productScan.category ?? productScan.detectedObject ?? 'Unknown Item'}
                    </Text>
                    <Text style={styles.productRef}>
                      Confidence: {productScan.confidence ?? 0}%
                    </Text>
                  </View>
                </View>
                <Text style={{ color: '#DC2626', fontSize: 12, marginTop: Spacing.sm }}>
                  No matching product found in inventory. Try scanning again.
                </Text>
                <SecondaryButton
                  title="Scan Again"
                  onPress={() => {
                    setProductScan(null);
                    setHudVisible(true);
                  }}
                  icon="camera-retake"
                  style={{ marginTop: Spacing.md }}
                />
              </Surface>
            ) : (
              <TouchableOpacity style={styles.scanPlaceholder} onPress={() => setHudVisible(true)}>
                <MaterialCommunityIcons name="robot" size={48} color={Colors.primaryLight} />
                <Text style={styles.scanPlaceholderText}>Scan Equipment</Text>
                <Text style={styles.scanPlaceholderSub}>
                  Point the camera at the asset — AI will identify the product.
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* ═══════════════════════════════════════════
            STEP 2: Choose Quantity
            ═══════════════════════════════════════════ */}
        {step === 2 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 2: Choose Quantity</Text>
            <Text style={styles.stepDesc}>
              How many units do you want to remove from stock?
            </Text>

            <Surface style={styles.dataCard} elevation={1}>
              <View style={styles.cardHeader}>
                <Text style={styles.visualEmoji}>{selectedProduct?.image ?? '📦'}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.productName}>
                    {selectedProduct?.name ?? productScan?.category ?? 'Selected Item'}
                  </Text>
                  <Text style={styles.productRef}>Available: {availableQuantity} units</Text>
                </View>
              </View>

              <Divider style={styles.cardDivider} />
              <Text style={styles.quantityLabel}>Requested Quantity</Text>
              <View style={styles.quantityRow}>
                <IconButton
                  icon="minus"
                  mode="contained"
                  containerColor="#F1F5F9"
                  onPress={() => setQuantity(Math.max(1, quantity - 1))}
                />
                <TextInput
                  mode="outlined"
                  value={String(quantity)}
                  onChangeText={handleQuantityChange}
                  keyboardType="numeric"
                  style={{ width: 100, height: 40, backgroundColor: '#FFF', textAlign: 'center' }}
                />
                <IconButton
                  icon="plus"
                  mode="contained"
                  containerColor="#F1F5F9"
                  onPress={() => setQuantity(quantity + 1)}
                />
              </View>

              <View style={{ marginTop: Spacing.md }}>
                <View style={styles.navButtonRow}>
                  <SecondaryButton
                    title="Back to Scan"
                    onPress={handleBackToScan}
                    icon="arrow-left"
                    style={{ flex: 1, marginRight: 8 }}
                  />
                  <PrimaryButton
                    title="Choose Assignment"
                    onPress={() => {
                      if (quantity <= availableQuantity) {
                        setTotalRequested(quantity);
                        setStep(3);
                      } else {
                        Alert.alert(
                          'Insufficient Stock',
                          `Only ${availableQuantity} ${selectedProduct?.name ?? 'units'} available. Requested: ${quantity}.`,
                          [
                            {
                              text: `Continue with ${availableQuantity}`,
                              onPress: () => {
                                setQuantity(availableQuantity);
                                setTotalRequested(availableQuantity);
                                setStep(3);
                              },
                            },
                            { text: 'Cancel', style: 'cancel' },
                          ]
                        );
                      }
                    }}
                    icon="arrow-right"
                    style={{ flex: 1, marginLeft: 8 }}
                  />
                </View>
              </View>
            </Surface>
          </View>
        )}

        {/* ═══════════════════════════════════════════
            STEP 3: Choose Assignment Method
            ═══════════════════════════════════════════ */}
        {step === 3 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 3: Choose Ticket Assignment</Text>
            <Text style={styles.stepDesc}>
              Select how you want to assign {quantity} × {selectedProduct?.name ?? 'item'} to a Jira ticket.
            </Text>

            {/* Assignment method tabs */}
            <View style={styles.tabsRow}>
              <TouchableOpacity
                onPress={() => {
                  setMethod('ai');
                  setTargetTicket(null);
                  if (!aiRecommendation) getAiRecommendation();
                }}
                style={[styles.tabBtn, method === 'ai' && styles.tabBtnActive]}
              >
                <Text style={[styles.tabBtnText, method === 'ai' && styles.tabBtnTextActive]}>
                  AI Recommendation
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => { setMethod('list'); setTargetTicket(null); }}
                style={[styles.tabBtn, method === 'list' && styles.tabBtnActive]}
              >
                <Text style={[styles.tabBtnText, method === 'list' && styles.tabBtnTextActive]}>
                  All Tickets
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => { setMethod('id'); setTargetTicket(null); }}
                style={[styles.tabBtn, method === 'id' && styles.tabBtnActive]}
              >
                <Text style={[styles.tabBtnText, method === 'id' && styles.tabBtnTextActive]}>
                  Ticket ID
                </Text>
              </TouchableOpacity>
            </View>

            {/* ── AI Recommendation Tab ─── */}
            {method === 'ai' && (
              <View>
                {aiLoading ? (
                  <Surface style={styles.aiLoadingCard} elevation={1}>
                    <ActivityIndicator size="large" color={Colors.primaryLight} />
                    <Text style={styles.aiLoadingText}>Computing optimal ticket matches...</Text>
                  </Surface>
                ) : aiRecommendation ? (
                  <View>
                    <Surface style={styles.dataCard} elevation={1}>
                      <View style={styles.aiBrainHeader}>
                        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                          <MaterialCommunityIcons name="robot" size={20} color={Colors.primaryLight} style={{ marginRight: 6 }} />
                          <Text style={styles.aiBrainTitle}>AI Best Match</Text>
                        </View>
                        <View style={styles.aiConfidenceBadge}>
                          <Text style={styles.aiConfidenceText}>{aiRecommendation.confidence}% Match</Text>
                        </View>
                      </View>

                      {aiRecommendation.ticket && (
                        <TicketCard
                          ticket={aiRecommendation.ticket}
                          isSelected={targetTicket?.id === aiRecommendation.ticket?.id}
                          onPress={() => setTargetTicket(aiRecommendation.ticket)}
                        />
                      )}

                      {aiRecommendation.reason && (
                        <View style={styles.aiReasonBox}>
                          <Text style={styles.aiReasonText}>"{aiRecommendation.reason}"</Text>
                        </View>
                      )}
                    </Surface>

                    {/* Other AI recommendations */}
                    {recommendationList.length > 1 && (
                      <View style={{ marginBottom: Spacing.md }}>
                        <Text style={styles.sectionHeader}>Other Recommendations</Text>
                        {recommendationList.slice(1).map((item: any, index: number) => (
                          <TouchableOpacity
                            key={item.ticket?.id || index}
                            onPress={() => setTargetTicket(item.ticket)}
                          >
                            <TicketCard
                              ticket={item.ticket}
                              isSelected={targetTicket?.id === item.ticket?.id}
                              onPress={() => setTargetTicket(item.ticket)}
                            />
                          </TouchableOpacity>
                        ))}
                      </View>
                    )}

                    {recommendationList.length === 0 && !aiRecommendation.ticket && (
                      <Text style={{ color: '#DC2626', fontSize: 12, marginTop: Spacing.sm }}>
                        No matching tickets found. Try manual search.
                      </Text>
                    )}
                  </View>
                ) : (
                  <Surface style={styles.aiLoadingCard} elevation={1}>
                    <MaterialCommunityIcons name="robot-off" size={32} color={Colors.textSecondary} />
                    <Text style={styles.aiLoadingText}>No AI results. Tap to retry.</Text>
                    <PrimaryButton
                      title="Retry"
                      onPress={getAiRecommendation}
                      icon="refresh"
                      style={{ marginTop: Spacing.md }}
                    />
                  </Surface>
                )}
              </View>
            )}

            {/* ── All Tickets Tab ─── */}
            {method === 'list' && (
              <View>
                {ticketsIsError ? (
                  <Surface style={styles.dataCard} elevation={1}>
                    <MaterialCommunityIcons name="alert-circle-outline" size={48} color={Colors.error} style={{ alignSelf: 'center', marginBottom: Spacing.md }} />
                    <Text style={{ color: Colors.error, fontSize: 14, fontWeight: 'bold', textAlign: 'center', marginBottom: Spacing.sm }}>
                      Jira Service Unavailable
                    </Text>
                    <Text style={{ color: Colors.textSecondary, fontSize: 12, textAlign: 'center', lineHeight: 18 }}>
                      Cannot fetch tickets from Jira. Please check your Jira credentials and network connection.
                    </Text>
                  </Surface>
                ) : ticketsLoading ? (
                  <Surface style={styles.aiLoadingCard} elevation={1}>
                    <ActivityIndicator size="large" color={Colors.primaryLight} />
                    <Text style={styles.aiLoadingText}>Fetching tickets from Jira...</Text>
                  </Surface>
                ) : tickets && tickets.length > 0 ? (
                  tickets
                    .filter((t) => {
                      const s = ((t as any).status ?? '').toLowerCase();
                      return s !== 'assigned' && s !== 'closed';
                    })
                    .map((ticket) => (
                      <TicketCard
                        key={ticket.id}
                        ticket={ticket}
                        isSelected={targetTicket?.id === ticket.id}
                        onPress={() => setTargetTicket(ticket)}
                      />
                    ))
                ) : (
                  <Surface style={styles.dataCard} elevation={1}>
                    <MaterialCommunityIcons name="ticket-outline" size={48} color={Colors.textSecondary} style={{ alignSelf: 'center', marginBottom: Spacing.md }} />
                    <Text style={{ color: Colors.textSecondary, fontSize: 12, textAlign: 'center' }}>
                      No open tickets available in Jira.
                    </Text>
                  </Surface>
                )}
              </View>
            )}

            {/* ── Ticket ID Tab ─── */}
            {method === 'id' && (
              <Surface style={styles.dataCard} elevation={1}>
                <TextInput
                  mode="outlined"
                  placeholder="Enter Jira Ticket ID"
                  value={ticketIdInput}
                  onChangeText={(text) => {
                    setTicketIdInput(text);
                    setIdValidationMsg('');
                  }}
                  autoCapitalize="characters"
                  style={{ backgroundColor: '#FFF' }}
                />
                {idValidationMsg ? (
                  <Text style={styles.idValidationText}>{idValidationMsg}</Text>
                ) : null}
                <TouchableOpacity style={styles.validateBtn} onPress={handleValidateId}>
                  <Text style={styles.validateBtnText}>Verify ID</Text>
                </TouchableOpacity>
              </Surface>
            )}

            {/* Navigation buttons for step 3 */}
            <View style={styles.navButtonRow}>
              <SecondaryButton
                title="Back"
                onPress={() => setStep(2)}
                icon="arrow-left"
                style={{ flex: 1, marginRight: 8 }}
              />
              {targetTicket && (
                <PrimaryButton
                  title="Review Assignment"
                  onPress={handleReviewAssignment}
                  icon="arrow-right"
                  style={{ flex: 1, marginLeft: 8 }}
                />
              )}
            </View>
          </View>
        )}

        {/* ═══════════════════════════════════════════
            STEP 4: Review & Confirm
            ═══════════════════════════════════════════ */}
        {step === 4 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 4: Review Before Confirming</Text>
            <Text style={styles.stepDesc}>
              The AI only recommends. You stay in control of the final assignment decision.
            </Text>

            <Surface style={styles.dataCard} elevation={1}>
              <Text style={styles.summaryTitle}>Assignment Summary</Text>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Product</Text>
                <Text style={styles.summaryVal}>{selectedProduct?.name}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Quantity</Text>
                <Text style={styles.summaryVal}>{quantity}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Ticket</Text>
                <Text style={styles.summaryVal}>{targetTicket?.id}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Ticket Title</Text>
                <Text style={styles.summaryVal} numberOfLines={2}>
                  {getTicketDisplayTitle(targetTicket)}
                </Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Requester</Text>
                <Text style={styles.summaryVal}>{getTicketRequester(targetTicket)}</Text>
              </View>
            </Surface>

            <View style={styles.navButtonRow}>
              <SecondaryButton
                title="Back"
                onPress={() => setStep(3)}
                icon="arrow-left"
                style={{ flex: 1, marginRight: 8 }}
              />
              <PrimaryButton
                title="Confirm Assignment"
                onPress={handleConfirmAssignment}
                loading={assignStockMutation.isPending}
                disabled={assignStockMutation.isPending}
                icon="check-bold"
                style={{ flex: 1, marginLeft: 8 }}
              />
            </View>
          </View>
        )}

        {/* ═══════════════════════════════════════════
            STEP 5: Success
            ═══════════════════════════════════════════ */}
        {step === 5 && (
          <View style={[styles.stepContainer, styles.successContainer]}>
            <View style={styles.successIconBox}>
              <MaterialCommunityIcons name="check-bold" size={48} color={Colors.success} />
            </View>
            <Text style={styles.successTitle}>Equipment Assigned!</Text>
            <Text style={styles.successDesc}>
              The inventory database has been updated successfully.
            </Text>

            <Surface style={styles.summaryCard} elevation={1}>
              <Text style={styles.summaryTitle}>Assignment Summary</Text>
              {assignedRecords.map((rec, idx) => (
                <View key={idx} style={{ marginBottom: Spacing.sm }}>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Product</Text>
                    <Text style={styles.summaryVal}>{rec.product?.name}</Text>
                  </View>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Qty</Text>
                    <Text style={styles.summaryVal}>{rec.quantity}</Text>
                  </View>
                  <View style={styles.summaryRow}>
                    <Text style={styles.summaryLabel}>Ticket</Text>
                    <Text style={styles.summaryVal}>{rec.ticket?.id}</Text>
                  </View>
                  {idx < assignedRecords.length - 1 && <Divider style={{ marginVertical: Spacing.xs }} />}
                </View>
              ))}
            </Surface>

            <View style={styles.navButtonRow}>
              <SecondaryButton
                title="Assign More"
                onPress={handleBackToScan}
                icon="arrow-left"
                style={{ flex: 1, marginRight: 8 }}
              />
              <PrimaryButton
                title="Return to Dashboard"
                onPress={() => navigation.navigate('MainDrawer')}
                icon="home"
                style={{ flex: 1, marginLeft: 8 }}
              />
            </View>
          </View>
        )}
      </ScrollView>

      {/* ── YOLO Camera HUD ───────────────────────── */}
      <YOLOCameraHUD
        visible={hudVisible}
        mode="product"
        onClose={() => setHudVisible(false)}
        onCapture={handleCameraResult}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Spacing.xl + 20,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.sm,
  },
  workflowTag: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.primaryLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: 2,
  },
  cancelText: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontWeight: 'bold',
  },
  stepperRow: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    backgroundColor: '#FFF',
  },
  stepIndicator: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    marginHorizontal: 2,
  },
  stepActive: {
    backgroundColor: Colors.primaryLight,
  },
  stepCompleted: {
    backgroundColor: Colors.success,
  },
  stepInactive: {
    backgroundColor: '#E2E8F0',
  },
  scrollContent: {
    padding: Spacing.lg,
  },
  stepContainer: {
    flex: 1,
  },
  navButtonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: Spacing.md,
  },
  stepTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: Colors.text,
  },
  stepDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
    lineHeight: 16,
    marginBottom: Spacing.md,
  },
  scanPlaceholder: {
    height: 150,
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    borderWidth: 2,
    borderColor: Colors.border,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  scanPlaceholderText: {
    fontSize: 13,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: Spacing.md,
  },
  scanPlaceholderSub: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  sectionHeader: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    letterSpacing: 0.5,
  },
  dataCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  visualEmoji: {
    fontSize: 48,
    marginRight: Spacing.md,
  },
  productName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: Colors.text,
  },
  productRef: {
    fontSize: 11,
    fontFamily: 'monospace',
    color: Colors.textSecondary,
    marginTop: 2,
  },
  productStockText: {
    fontSize: 10,
    fontWeight: 'bold',
    marginTop: 4,
  },
  cardDivider: {
    marginVertical: Spacing.md,
  },
  quantityLabel: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    marginBottom: Spacing.sm,
  },
  quantityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-start',
  },
  tabsRow: {
    flexDirection: 'row',
    backgroundColor: '#E2E8F0',
    borderRadius: BorderRadius.md,
    padding: 2,
    marginBottom: Spacing.md,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: BorderRadius.sm,
  },
  tabBtnActive: {
    backgroundColor: '#FFF',
  },
  tabBtnText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.textSecondary,
  },
  tabBtnTextActive: {
    color: Colors.primary,
  },
  aiBrainHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  aiBrainTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
  },
  aiConfidenceBadge: {
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  aiConfidenceText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: 'bold',
  },
  aiReasonBox: {
    backgroundColor: Colors.infoLight,
    borderColor: Colors.primaryLight + '22',
    borderWidth: 1,
    borderRadius: BorderRadius.md,
    padding: 10,
    marginTop: Spacing.sm,
  },
  aiReasonText: {
    fontSize: 10,
    color: Colors.primaryLight,
    fontStyle: 'italic',
    lineHeight: 14,
  },
  aiLoadingCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  aiLoadingText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: 'bold',
    marginTop: Spacing.md,
  },
  idValidationText: {
    fontSize: 10,
    fontWeight: 'bold',
    marginTop: 6,
  },
  validateBtn: {
    marginTop: Spacing.md,
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: 10,
    alignItems: 'center',
  },
  validateBtnText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  successContainer: {
    alignItems: 'center',
    paddingVertical: Spacing.xl,
  },
  successIconBox: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
    borderColor: '#A7F3D0',
    borderWidth: 4,
    marginBottom: Spacing.lg,
  },
  successTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.text,
  },
  successDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: Spacing.sm,
    lineHeight: 16,
    paddingHorizontal: Spacing.xl,
  },
  summaryCard: {
    width: '100%',
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginVertical: Spacing.xl,
  },
  summaryTitle: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  summaryLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  summaryVal: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.text,
    maxWidth: '60%',
    textAlign: 'right',
  },
  yoloBadge: {
    backgroundColor: '#11182711',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginBottom: 4,
  },
  yoloBadgeText: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontWeight: 'bold',
  },
});
