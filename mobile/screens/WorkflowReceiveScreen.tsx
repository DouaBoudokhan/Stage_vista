import React, { useState } from 'react';
import { StyleSheet, View, ScrollView, TouchableOpacity, Alert, Image } from 'react-native';
import { Text, Surface, Divider, useTheme, IconButton } from 'react-native-paper';
import { usePurchaseOrders, useReceiveStock } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { PrimaryButton, SecondaryButton } from '../components/AppButtons';
import { YOLOCameraHUD } from '../components/YOLOCameraHUD';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import type { ScanResult, PurchaseOrder } from '../types';

export default function WorkflowReceiveScreen({ navigation }: any) {
  const theme = useTheme();
  
  // APIs
  const { data: purchaseOrders } = usePurchaseOrders();
  const receiveStockMutation = useReceiveStock();

  // Workflow State
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [cameraVisible, setCameraVisible] = useState(false);
  const [cameraMode, setCameraMode] = useState<'product' | 'invoice' | 'label'>('product');

  // Collected scan data
  const [productScan, setProductScan] = useState<ScanResult | null>(null);
  const [invoiceScan, setInvoiceScan] = useState<ScanResult | null>(null);
  const [selectedPO, setSelectedPO] = useState<PurchaseOrder | null>(null);
  const [labelScan, setLabelScan] = useState<ScanResult | null>(null);

  const handleOpenScanner = async (mode: 'product' | 'invoice' | 'label') => {
    console.log(`🎯 Opening camera for mode: ${mode}`);
    setCameraMode(mode);
    setCameraVisible(true);
  };

  const handleCameraResult = async (result: any) => {
    console.log('📸 Camera result received:', result);
    setCameraVisible(false);
    
    if (cameraMode === 'product') {
      console.log('🤖 Setting product scan result');
      setProductScan(result);
    } else if (cameraMode === 'invoice') {
      const formattedResult = {
        mode: 'invoice',
        supplier: result.supplier || result.document?.supplier || 'Unknown Supplier',
        invoiceNumber: result.invoiceNumber || result.document?.invoice_number || 'Unknown Invoice',
        purchaseOrderSuggested: result.purchaseOrderSuggested || result.purchase_orders?.[0]?.po_number,
        serialNumbers: result.serialNumbers || result.purchase_orders?.flatMap((po: any) => po.serial_numbers || []) || [],
        confidence: result.confidence || 95,
        detectedItems: result.detectedItems || result.purchase_orders?.map((po: any) => ({
          name: po.description || po.po_number,
          ref: po.po_number,
          quantity: po.serial_numbers?.length || 1,
          matched: po.cached,
          serialNumbers: (po.serial_numbers || []) as string[],
        })) || [],
        quantity: 1
      };
      setInvoiceScan(formattedResult);

      // Auto-suggest purchase order matching & select top PO
      const topPoNumber = formattedResult.purchaseOrderSuggested || formattedResult.detectedItems?.[0]?.ref;
      if (topPoNumber) {
        const topItem = formattedResult.detectedItems?.[0];
        const topItemSerials = (topItem as any)?.serialNumbers || [];
        setSelectedPO({
          id: topPoNumber,
          supplier: formattedResult.supplier,
          date: new Date().toISOString().split('T')[0],
          status: 'Pending',
          serialNumbers: topItemSerials,
          items: [
            {
              ref: topItem?.ref || topPoNumber,
              name: topItem?.name || `Equipment PO ${topPoNumber}`,
              brand: 'Equipment',
              quantity: topItem?.quantity || 1,
              received: 0,
              serialNumbers: topItemSerials,
            },
          ],
        });
      }
    } else if (cameraMode === 'label') {
      setLabelScan(result);
    }
  };

  // Compute active roster of POs (combining POs extracted from invoice scan + DB roster)
  const displayPOs: PurchaseOrder[] = React.useMemo(() => {
    const list: PurchaseOrder[] = [];

    // 1. Include POs extracted from the invoice scan
    if (invoiceScan?.detectedItems && invoiceScan.detectedItems.length > 0) {
      invoiceScan.detectedItems.forEach((item) => {
        const itemSerials = (item as any).serialNumbers ?? [];
        list.push({
          id: item.ref,
          supplier: invoiceScan.supplier || 'Lactech plus',
          date: new Date().toISOString().split('T')[0],
          status: 'Pending',
          serialNumbers: itemSerials,
          items: [
            {
              ref: item.ref,
              name: item.name,
              brand: productScan?.brand || 'Equipment',
              quantity: item.quantity,
              received: 0,
              serialNumbers: itemSerials,
            },
          ],
        });
      });
    }

    // 2. Include DB POs if available
    if (purchaseOrders && purchaseOrders.length > 0) {
      purchaseOrders.forEach((po) => {
        if (!list.some((existing) => existing.id === po.id)) {
          list.push(po);
        }
      });
    }

    // 3. Fallback demo PO if list is empty
    if (list.length === 0) {
      list.push({
        id: '2000234706',
        supplier: invoiceScan?.supplier || 'Lactech plus',
        date: new Date().toISOString().split('T')[0],
        status: 'Pending',
        serialNumbers: [],
        items: [
          {
            ref: '2000234706',
            name: 'MacBook Pro 16" M5 18 CPU and 20 GPU',
            brand: 'Apple',
            quantity: 1,
            received: 0,
            serialNumbers: [],
          },
        ],
      });
    }

    return list;
  }, [purchaseOrders, invoiceScan, productScan]);

  const handleNextStep = () => {
    if (step === 1 && productScan) setStep(2);
    else if (step === 2 && invoiceScan) setStep(3);
    else if (step === 3 && selectedPO) setStep(4);
    else if (step === 4 && labelScan) setStep(5);
  };

  const handlePreviousStep = () => {
    // Step 5 (success) → back to review (step 4) — this discards nothing since save already happened
    // For steps 2..4: move back; previous scan results are preserved in state
    if (step > 1 && step <= 5) setStep((step - 1) as 1 | 2 | 3 | 4 | 5);
  };

  // Allow the technician to jump DIRECTLY to any already-completed step by clicking the stepper bar.
  // Forward jumps are blocked (require scans); backward jumps and same-step are fine.
  const handleJumpToStep = (targetStep: number) => {
    const t = targetStep as 1 | 2 | 3 | 4 | 5;
    if (t === step) return;

    // Going BACK is always allowed (data for earlier steps is already captured)
    if (t < step) {
      setStep(t);
      return;
    }

    // Going FORWARD is allowed only if all intermediate scans are present (mirror handleNextStep guards)
    if (t === 2 && productScan) setStep(2);
    else if (t === 3 && productScan && invoiceScan) setStep(3);
    else if (t === 4 && productScan && invoiceScan && selectedPO) setStep(4);
    else if (t === 5 && productScan && invoiceScan && selectedPO && labelScan) setStep(5);
  };

  const handleConfirmReceive = async () => {
    if (!productScan || !selectedPO || !labelScan) return;
    
    try {
      const articleNumber = labelScan.articleNumber ?? labelScan.reference ?? productScan.reference ?? 'UNKNOWN';
      const labelSerialNumbers = labelScan.serialNumbers ?? [];
      // Critical fix: use serials from the SELECTED PO (not global invoice.serialNumbers which has ALL POs' serials)
      const selectedPoSerialNumbers = selectedPO.serialNumbers ?? selectedPO.items?.[0]?.serialNumbers ?? [];
      const allSerialNumbers = labelSerialNumbers.length > 0 ? labelSerialNumbers : selectedPoSerialNumbers;
      await receiveStockMutation.mutateAsync({
        ref: articleNumber,
        quantity: labelScan.quantity ?? productScan.quantity ?? 1,
        poId: selectedPO.id,
        technician: 'admin',
        category: productScan.category ?? 'Laptop',
        brand: labelScan.brand ?? 'Unknown',
        productName: labelScan.productName ?? productScan.detectedObject ?? productScan.category ?? articleNumber,
        articleNumber,
        serialNumbers: allSerialNumbers,
      });
      // Skip to final success
      setStep(5);
    } catch (e) {
      Alert.alert('FastAPI Update Failed', 'Failed to register received items on FastAPI backend.');
    }
  };

  const handleCancel = () => {
    navigation.goBack();
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerBar}>
        <View>
          <Text style={styles.workflowTag}>Workflow 1/2</Text>
          <Text style={styles.headerTitle}>Receive Equipment</Text>
        </View>
        <TouchableOpacity onPress={handleCancel}>
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      </View>

      {/* Stepper bar — clickable: tap any completed/current step to jump back */}
      <View style={styles.stepperRow}>
        {[1, 2, 3, 4, 5].map((s) => {
          const isActive = s === step;
          const isCompleted = s < step;
          const isInactive = !isActive && !isCompleted;
          return (
            <TouchableOpacity
              key={s}
              activeOpacity={isInactive ? 1 : 0.6}
              onPress={() => handleJumpToStep(s)}
              style={{ flex: 1, marginHorizontal: 2 }}
              disabled={isInactive}
            >
              <View
                style={[
                  styles.stepIndicator,
                  isActive ? styles.stepActive : isCompleted ? styles.stepCompleted : styles.stepInactive
                ]}
              />
            </TouchableOpacity>
          );
        })}
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* STEP 1: Scan Product */}
        {step === 1 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 1: Scan Product</Text>
            <Text style={styles.stepDesc}>
              Use the camera to scan the actual product (not the box). The AI will identify the equipment type and category.
            </Text>

            {productScan ? (
              <Surface style={styles.dataCard} elevation={1}>
                <View style={styles.cardHeader}>
                  <View style={styles.avatarEmojiBox}>
                    <Text style={{ fontSize: 24 }}>🤖</Text>
                  </View>
                  <View>
                    <View style={styles.yoloBadge}>
                      <Text style={styles.yoloBadgeText}>YOLO11 Detected</Text>
                    </View>
                    <Text style={styles.detectedTitle}>{productScan.category} Equipment</Text>
                    <Text style={styles.detectedRef}>Type: {productScan.equipment_type || productScan.category}</Text>
                  </View>
                </View>
                
                {/* Captured Image with YOLO Bounding Boxes */}
                {productScan.capturedImageUri && productScan.boundingBox && (
                  <View style={styles.capturedImageContainer}>
                    <Text style={styles.capturedImageTitle}>Captured Detection</Text>
                    <View style={styles.capturedImageWrapper}>
                      <Image 
                        source={{ uri: productScan.capturedImageUri }} 
                        style={styles.capturedImageDisplay} 
                        resizeMode="cover"
                      />
                      <View 
                        style={[
                          styles.capturedBoundingBox,
                          {
                            left: `${(productScan.boundingBox.x / (productScan.imageWidth || 640)) * 100}%`,
                            top: `${(productScan.boundingBox.y / (productScan.imageHeight || 480)) * 100}%`,
                            width: `${(productScan.boundingBox.width / (productScan.imageWidth || 640)) * 100}%`,
                            height: `${(productScan.boundingBox.height / (productScan.imageHeight || 480)) * 100}%`,
                          }
                        ]}
                      >
                        <View style={styles.capturedConfidenceLabel}>
                          <Text style={styles.capturedConfidenceText}>
                            {productScan.category} {productScan.confidence}%
                          </Text>
                        </View>
                      </View>
                    </View>
                  </View>
                )}
                
                <Divider style={styles.cardDivider} />
                <View style={styles.metaRow}>
                  <Text style={styles.metaLabel}>YOLO Confidence</Text>
                  <Text style={[styles.metaVal, { color: Colors.success }]}>{productScan.confidence}%</Text>
                </View>
                <View style={styles.metaRow}>
                  <Text style={styles.metaLabel}>Processing Time</Text>
                  <Text style={styles.metaVal}>{productScan.processing_time_ms || 180}ms</Text>
                </View>
                {productScan.detected_features && (
                  <View style={styles.featuresContainer}>
                    <Text style={styles.featuresTitle}>Detected Features</Text>
                    <View style={styles.featuresGrid}>
                      {productScan.detected_features.map((feature: string, idx: number) => (
                        <View key={idx} style={styles.featureBadge}>
                          <Text style={styles.featureBadgeText}>{feature}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                )}
              </Surface>
            ) : (
              <TouchableOpacity style={styles.scanPlaceholder} onPress={() => handleOpenScanner('product')}>
                <MaterialCommunityIcons name="camera" size={48} color={Colors.primaryLight} />
                <Text style={styles.scanPlaceholderText}>Scan Product with Camera</Text>
                <Text style={styles.scanPlaceholderSub}>Tap to open camera and scan the actual product</Text>
              </TouchableOpacity>
            )}

            {productScan && (
              <PrimaryButton title="Continue to Step 2" onPress={handleNextStep} icon="arrow-right" />
            )}
          </View>
        )}

        {/* STEP 2: Scan Invoice */}
        {step === 2 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 2: Scan Vendor Invoice</Text>
            <Text style={styles.stepDesc}>
              Scan vendor paper commercial receipt. Extracted supplier names will suggest Purchase Order references.
            </Text>

            {invoiceScan ? (
              <Surface style={styles.dataCard} elevation={1}>
                <View style={styles.cardHeader}>
                  <View style={styles.avatarEmojiBox}>
                    <Text style={{ fontSize: 24 }}>📄</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.detectedTitle}>{invoiceScan.supplier}</Text>
                    <Text style={styles.detectedRef}>Invoice: {invoiceScan.invoiceNumber}</Text>
                  </View>
                </View>

                {invoiceScan.purchaseOrderSuggested && (
                  <View style={styles.suggestionBanner}>
                    <MaterialCommunityIcons name="clipboard-check" size={16} color={Colors.primaryLight} />
                    <Text style={styles.suggestionText}>
                      PO Suggestion: {invoiceScan.purchaseOrderSuggested}
                    </Text>
                  </View>
                )}

                <Divider style={styles.cardDivider} />
                <Text style={styles.invoiceItemsHeader}>Invoice Line Items</Text>
                {(invoiceScan.detectedItems || []).map((item, idx) => {
                  const itemSerials = (item as any).serialNumbers || [];
                  return (
                    <View key={idx} style={[styles.invoiceItemRow, { paddingBottom: Spacing.sm }]}>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.invoiceItemName} numberOfLines={1}>{item.name}</Text>
                        <Text style={styles.invoiceItemQty}>Qty: {item.quantity}</Text>
                        {itemSerials.length > 0 && (
                          <View style={{ marginTop: Spacing.xs }}>
                            <Text style={{ fontSize: 11, color: Colors.textSecondary, marginBottom: 4 }}>
                              Serials ({itemSerials.length}):
                            </Text>
                            <View style={styles.serialBoxGrid}>
                              {itemSerials.slice(0, 5).map((sn: string, snIdx: number) => (
                                <View key={snIdx} style={styles.serialBadge}>
                                  <Text style={styles.serialBadgeText}>{sn}</Text>
                                </View>
                              ))}
                              {itemSerials.length > 5 && (
                                <Text style={{ fontSize: 11, color: Colors.textSecondary, alignSelf: 'center' }}>
                                  +{itemSerials.length - 5} more
                                </Text>
                              )}
                            </View>
                          </View>
                        )}
                      </View>
                    </View>
                  );
                })}
              </Surface>
            ) : (
              <TouchableOpacity style={styles.scanPlaceholder} onPress={() => handleOpenScanner('invoice')}>
                <MaterialCommunityIcons name="camera" size={48} color={Colors.primaryLight} />
                <Text style={styles.scanPlaceholderText}>Scan Invoice with Camera</Text>
                <Text style={styles.scanPlaceholderSub}>Tap to photograph the commercial invoice</Text>
              </TouchableOpacity>
            )}

            <View style={styles.navButtonRow}>
              <SecondaryButton title="Back to Step 1" onPress={handlePreviousStep} icon="arrow-left" style={{ flex: 1, marginRight: 8 }} />
              {invoiceScan && (
                <PrimaryButton title="Confirm PO → Step 3" onPress={handleNextStep} icon="arrow-right" style={{ flex: 1, marginLeft: 8 }} />
              )}
            </View>
          </View>
        )}

        {/* STEP 3: Confirm PO */}
        {step === 3 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 3: Select Purchase Order</Text>
            <Text style={styles.stepDesc}>
              Select the matching Purchase Order from the active roster. Confirm items match scanned records.
            </Text>

            {displayPOs.map((po) => {
              const isSuggested = invoiceScan?.purchaseOrderSuggested === po.id || selectedPO?.id === po.id;
              const isSelected = selectedPO?.id === po.id;
              const poItems = po.items || [];
              return (
                <TouchableOpacity
                  key={po.id}
                  onPress={() => setSelectedPO(po)}
                  style={[
                    styles.poOptionCard,
                    isSelected && { borderColor: theme.colors.primary, borderWidth: 1.5, backgroundColor: Colors.primary + '08' }
                  ]}
                >
                  <View style={styles.poCardHeader}>
                    <Text style={styles.poCardTitle}>{po.id}</Text>
                    {isSuggested && (
                      <View style={styles.suggestedBadge}>
                        <Text style={styles.suggestedBadgeText}>Suggested Match</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.poCardMeta}>Supplier: {po.supplier}</Text>
                  <Text style={styles.poCardMeta}>Order Date: {po.date}</Text>

                  {/* Llama 3.3 Generated Description */}
                  {poItems[0]?.name && (
                    <View style={styles.llamaDescBox}>
                      <Text style={styles.llamaTag}>🦙 Llama 3.3 Description</Text>
                      <Text style={styles.llamaDescText}>{poItems[0].name}</Text>
                    </View>
                  )}

                  <Divider style={{ marginVertical: Spacing.sm }} />
                  {poItems.map((item, idx) => (
                    <View key={idx} style={styles.poItemRow}>
                      <Text style={styles.poItemName}>Items: {item.quantity} Unit(s)</Text>
                      {(item.serialNumbers && item.serialNumbers.length > 0) && (
                        <View style={{ marginTop: Spacing.xs }}>
                          <Text style={{ fontSize: 11, color: Colors.textSecondary, marginBottom: 4 }}>
                            PO Serial Numbers ({item.serialNumbers.length}):
                          </Text>
                          <View style={styles.serialBoxGrid}>
                            {item.serialNumbers.slice(0, 4).map((sn, snIdx) => (
                              <View key={snIdx} style={styles.serialBadge}>
                                <Text style={styles.serialBadgeText}>{sn}</Text>
                              </View>
                            ))}
                            {item.serialNumbers.length > 4 && (
                              <Text style={{ fontSize: 11, color: Colors.textSecondary, alignSelf: 'center' }}>
                                +{item.serialNumbers.length - 4} more
                              </Text>
                            )}
                          </View>
                        </View>
                      )}
                    </View>
                  ))}
                </TouchableOpacity>
              );
            })}

            <View style={styles.navButtonRow}>
              <SecondaryButton title="Back to Step 2" onPress={handlePreviousStep} icon="arrow-left" style={{ flex: 1, marginRight: 8 }} />
              {selectedPO && (
                <PrimaryButton title="Continue to Step 4" onPress={handleNextStep} icon="arrow-right" style={{ flex: 1, marginLeft: 8 }} />
              )}
            </View>
          </View>
        )}

        {/* STEP 4: Scan Shipping Label */}
        {step === 4 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 4: Scan Box Shipping Label</Text>
            <Text style={styles.stepDesc}>
              Scan the box shipping label tracking codes. FastAPI compares quantity metadata before final checkin.
            </Text>

            {labelScan ? (
              <Surface style={styles.dataCard} elevation={1}>
                <View style={styles.cardHeader}>
                  <View style={styles.avatarEmojiBox}>
                    <Text style={{ fontSize: 24 }}>📦</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.detectedTitle}>{labelScan.brand || 'EPOS'} {labelScan.productName || 'Equipment'}</Text>
                    <Text style={styles.detectedRef}>Art.-No: {labelScan.articleNumber || labelScan.reference || '1001421'}</Text>
                  </View>
                </View>
                <Divider style={styles.cardDivider} />
                <View style={styles.metaRow}>
                  <Text style={styles.metaLabel}>Label Quantity (QTY)</Text>
                  <Text style={[styles.metaVal, { color: Colors.success, fontWeight: 'bold' }]}>{labelScan.quantity ?? 20} Units</Text>
                </View>
                {labelScan.poNumber && (
                  <View style={styles.metaRow}>
                    <Text style={styles.metaLabel}>PO Reference</Text>
                    <Text style={styles.metaVal}>{labelScan.poNumber}</Text>
                  </View>
                )}
                <Divider style={styles.cardDivider} />
                <Text style={styles.invoiceItemsHeader}>Extracted Serial Numbers</Text>
                <View style={styles.serialBoxGrid}>
                  {(labelScan.serialNumbers && labelScan.serialNumbers.length > 0) ? (
                    labelScan.serialNumbers.map((sn, idx) => (
                      <View key={idx} style={styles.serialBadge}>
                        <Text style={styles.serialBadgeText}>{sn}</Text>
                      </View>
                    ))
                  ) : (
                    <Text style={{ fontSize: 12, color: Colors.textSecondary }}>Data Matrix Code / Serial batch code registered</Text>
                  )}
                </View>
              </Surface>
            ) : (
              <TouchableOpacity style={styles.scanPlaceholder} onPress={() => handleOpenScanner('label')}>
                <MaterialCommunityIcons name="camera" size={48} color={Colors.primaryLight} />
                <Text style={styles.scanPlaceholderText}>Scan Shipping Label with Camera</Text>
                <Text style={styles.scanPlaceholderSub}>Tap to photograph the box shipping label</Text>
              </TouchableOpacity>
            )}

            {productScan && selectedPO && labelScan && (
              <Surface style={styles.summaryCard} elevation={1}>
                <Text style={styles.summaryTitle}>Pre-Save Review</Text>
                <Text style={styles.reviewSubtitle}>
                  Confirm the exact data that will be stored in inventory.
                </Text>

                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Category:</Text>
                  <Text style={styles.summaryVal}>{productScan.category ?? 'Laptop'}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Brand:</Text>
                  <Text style={styles.summaryVal}>{labelScan.brand ?? 'Unknown'}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Product Name:</Text>
                  <Text style={styles.summaryVal}>{labelScan.productName ?? productScan.detectedObject ?? productScan.category ?? 'Unknown'}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Article Number:</Text>
                  <Text style={styles.summaryVal}>{labelScan.articleNumber ?? labelScan.reference ?? productScan.reference ?? 'Unknown'}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>PO:</Text>
                  <Text style={styles.summaryVal}>{selectedPO.id}</Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Quantity:</Text>
                  <Text style={styles.summaryVal}>{labelScan.quantity ?? productScan.quantity ?? 1}</Text>
                </View>

                <View style={styles.reviewSerialSection}>
                  <Text style={styles.invoiceItemsHeader}>Serial Numbers</Text>
                  <View style={styles.serialBoxGrid}>
                    {(() => {
                      const labelSerials = labelScan.serialNumbers ?? [];
                      const selectedPoSerials = selectedPO.serialNumbers ?? selectedPO.items?.[0]?.serialNumbers ?? [];
                      const display = labelSerials.length > 0 ? labelSerials : selectedPoSerials;
                      if (display.length > 0) {
                        return display.map((sn, idx) => (
                          <View key={idx} style={styles.serialBadge}>
                            <Text style={styles.serialBadgeText}>{sn}</Text>
                          </View>
                        ));
                      }
                      return (
                        <Text style={{ fontSize: 12, color: Colors.textSecondary }}>No serial numbers detected on the label or selected PO</Text>
                      );
                    })()}
                  </View>
                </View>
              </Surface>
            )}

            {labelScan && (
              <View style={styles.navButtonRow}>
                <SecondaryButton title="Back to Step 3" onPress={handlePreviousStep} icon="arrow-left" style={{ flex: 1, marginRight: 8 }} />
                <PrimaryButton 
                  title="Register in Stock" 
                  onPress={handleConfirmReceive} 
                  loading={receiveStockMutation.isPending}
                  disabled={receiveStockMutation.isPending}
                  icon="check-circle-outline" 
                  style={{ flex: 1, marginLeft: 8 }}
                />
              </View>
            )}
          </View>
        )}

        {/* STEP 5: Success screen */}
        {step === 5 && (
          <View style={[styles.stepContainer, styles.successContainer]}>
            <View style={styles.successIconBox}>
              <MaterialCommunityIcons name="check-circle" size={48} color={Colors.success} />
            </View>
            <Text style={styles.successTitle}>Equipment Received!</Text>
            <Text style={styles.successDesc}>
              The FastAPI database has registered <Text style={{ fontWeight: 'bold' }}>{labelScan?.quantity ?? 10} units</Text> of {productScan?.brand} {productScan?.reference}. Logistics update dispatched.
            </Text>

            <Surface style={styles.summaryCard} elevation={1}>
              <Text style={styles.summaryTitle}>Movement Summary</Text>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>PO Ref:</Text>
                <Text style={styles.summaryVal}>{selectedPO?.id}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Supplier:</Text>
                <Text style={styles.summaryVal}>{selectedPO?.supplier}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Category:</Text>
                <Text style={styles.summaryVal}>{productScan?.category}</Text>
              </View>
            </Surface>

            <View style={styles.navButtonRow}>
              <SecondaryButton title="Review Details" onPress={handlePreviousStep} icon="arrow-left" style={{ flex: 1, marginRight: 8 }} />
              <PrimaryButton title="Return to Dashboard" onPress={() => navigation.navigate('MainTabs')} icon="home" style={{ flex: 1, marginLeft: 8 }} />
            </View>
          </View>
        )}
      </ScrollView>

      {/* Real-time YOLO Camera HUD */}
      <YOLOCameraHUD
        visible={cameraVisible}
        mode={cameraMode}
        onClose={() => setCameraVisible(false)}
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
    marginTop: Spacing.sm,
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
    height: 180,
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
  dataCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarEmojiBox: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  aiBadge: {
    backgroundColor: '#ECFDF5',
    borderColor: '#A7F3D0',
    borderWidth: 1,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  aiBadgeText: {
    color: Colors.success,
    fontSize: 8,
    fontWeight: 'bold',
  },
  yoloBadge: {
    backgroundColor: '#EFF6FF',
    borderColor: '#BFDBFE',
    borderWidth: 1,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  yoloBadgeText: {
    color: Colors.primaryLight,
    fontSize: 8,
    fontWeight: 'bold',
  },
  boundingBoxContainer: {
    marginTop: Spacing.md,
  },
  boundingBoxTitle: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  capturedImageContainer: {
    marginTop: Spacing.md,
  },
  capturedImageTitle: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  capturedImageWrapper: {
    position: 'relative',
    height: 160,
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  capturedImageDisplay: {
    width: '100%',
    height: '100%',
  },
  capturedBoundingBox: {
    position: 'absolute',
    borderWidth: 2,
    borderColor: Colors.success,
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
  },
  capturedConfidenceLabel: {
    position: 'absolute',
    top: -22,
    left: 0,
    backgroundColor: Colors.success,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
  },
  capturedConfidenceText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: 'bold',
  },
  featuresContainer: {
    marginTop: Spacing.md,
  },
  featuresTitle: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -2,
  },
  featureBadge: {
    backgroundColor: '#F1F5F9',
    borderColor: '#CBD5E1',
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    margin: 2,
  },
  featureBadgeText: {
    fontSize: 8,
    color: Colors.text,
  },
  detectedTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: 4,
  },
  detectedRef: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: Colors.textSecondary,
  },
  cardDivider: {
    marginVertical: Spacing.md,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metaLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  metaVal: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  suggestionBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.infoLight,
    padding: 10,
    borderRadius: BorderRadius.sm,
    marginTop: Spacing.md,
  },
  suggestionText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.primaryLight,
    marginLeft: 6,
  },
  invoiceItemsHeader: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  invoiceItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    backgroundColor: '#F8FAFC',
    paddingHorizontal: 10,
    borderRadius: 6,
    marginVertical: 2,
  },
  invoiceItemName: {
    fontSize: 11,
    color: Colors.text,
    flex: 1,
  },
  invoiceItemQty: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.text,
    fontFamily: 'monospace',
  },
  poOptionCard: {
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginVertical: 4,
  },
  poCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  poCardTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  suggestedBadge: {
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  suggestedBadgeText: {
    color: '#FFF',
    fontSize: 8,
    fontWeight: 'bold',
  },
  poCardMeta: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  poItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 2,
  },
  poItemName: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  poItemQty: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.text,
  },
  serialBoxGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -2,
  },
  serialBadge: {
    backgroundColor: '#F1F5F9',
    borderColor: '#CBD5E1',
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 4,
    margin: 2,
  },
  serialBadgeText: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: Colors.text,
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
  reviewSubtitle: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
    lineHeight: 16,
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
  },
  reviewSerialSection: {
    marginTop: Spacing.md,
  },
  llamaDescBox: {
    backgroundColor: '#F8FAFC',
    borderColor: '#E2E8F0',
    borderWidth: 1,
    borderRadius: BorderRadius.sm,
    padding: Spacing.sm,
    marginTop: Spacing.xs,
  },
  llamaTag: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.primaryLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  llamaDescText: {
    fontSize: 11,
    color: Colors.text,
    lineHeight: 15,
  },
});
