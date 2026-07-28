import React, { useState, useEffect } from 'react';
import { StyleSheet, View, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { Text, Surface, TextInput, IconButton, Divider, useTheme } from 'react-native-paper';
import { useProducts, useTickets, useAssignStock, useRecommendTicket } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { CameraHUD } from '../components/CameraHUD';
import { TicketCard } from '../components/Cards';
import { PrimaryButton } from '../components/AppButtons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import type { Product, Ticket, ScanResult } from '../types';

export default function WorkflowAssignScreen({ route, navigation }: any) {
  const theme = useTheme();
  
  // Route params for preselected items (coming from product details)
  const preselected = route.params?.preselectedProduct as Product | undefined;

  // API calls
  const { data: products } = useProducts();
  const { data: tickets } = useTickets();
  const assignStockMutation = useAssignStock();
  const recommendTicketMutation = useRecommendTicket();

  // Workflow State
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [hudVisible, setHudVisible] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(preselected ?? null);
  const [quantity, setQuantity] = useState<number>(1);
  const [method, setMethod] = useState<'ai' | 'list' | 'id'>('ai');

  // Selected ticket target
  const [targetTicket, setTargetTicket] = useState<Ticket | null>(null);
  const [aiRecommendation, setAiRecommendation] = useState<any>(null);
  const [ticketIdInput, setTicketIdInput] = useState('');
  const [idValidationMsg, setIdValidationMsg] = useState('');

  // Fetch AI recommendation when product is selected
  useEffect(() => {
    if (selectedProduct && method === 'ai') {
      getAiRecommendation();
    }
  }, [selectedProduct, method]);

  const getAiRecommendation = async () => {
    if (!selectedProduct) return;
    try {
      const rec = await recommendTicketMutation.mutateAsync({
        productRef: selectedProduct.ref,
        category: selectedProduct.category,
        brand: selectedProduct.brand,
      });
      setAiRecommendation(rec);
      setTargetTicket(rec.ticket);
    } catch (e) {
      console.error('AI Recommendation fetch failed:', e);
    }
  };

  const handleScanCompleted = (result: ScanResult) => {
    setHudVisible(false);
    // Locate scanned ref in catalog
    const found = products?.find((p) => p.ref.toLowerCase() === result.reference?.toLowerCase());
    if (found) {
      setSelectedProduct(found);
    } else {
      Alert.alert('SKU Unregistered', 'Scanned reference is not in database catalog hierarchy.');
    }
  };

  const handleValidateId = () => {
    const found = tickets?.find((t) => t.id.toLowerCase() === ticketIdInput.trim().toLowerCase());
    if (found) {
      setTargetTicket(found);
      setIdValidationMsg('✅ Valid Ticket Found!');
    } else {
      setIdValidationMsg('❌ Ticket Not Found. Try HR-NEW-2026 or ETXTUN-41');
      setTargetTicket(null);
    }
  };

  const handleConfirmAssignment = async () => {
    if (!selectedProduct || !targetTicket) return;

    try {
      await assignStockMutation.mutateAsync({
        productId: selectedProduct.id,
        quantity,
        ticketId: targetTicket.id,
        technician: 'admin',
      });
      setStep(3); // Go to final confirmation step
    } catch (e) {
      Alert.alert('FastAPI Update Failed', 'Failed to deduct stock or update ticket status on FastAPI backend.');
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerBar}>
        <View>
          <Text style={styles.workflowTag}>Workflow 2/2</Text>
          <Text style={styles.headerTitle}>Assign Equipment</Text>
        </View>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
      </View>

      {/* Steppers */}
      <View style={styles.stepperRow}>
        {[1, 2, 3].map((s) => (
          <View
            key={s}
            style={[
              styles.stepIndicator,
              s === step ? styles.stepActive : s < step ? styles.stepCompleted : styles.stepInactive
            ]}
          />
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* STEP 1: Select Product & Quantity */}
        {step === 1 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 1: Scan or Select Asset</Text>
            <Text style={styles.stepDesc}>
              Scan the computer hardware barcode or select from the active warehouse roster list.
            </Text>

            {selectedProduct ? (
              <Surface style={styles.dataCard} elevation={1}>
                <View style={styles.cardHeader}>
                  <Text style={styles.visualEmoji}>{selectedProduct.image}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.productName}>{selectedProduct.name}</Text>
                    <Text style={styles.productRef}>Ref: {selectedProduct.ref}</Text>
                    <Text style={[styles.productStockText, { color: theme.colors.primary }]}>
                      Available stock: {selectedProduct.quantity} units
                    </Text>
                  </View>
                </View>

                <Divider style={styles.cardDivider} />
                <Text style={styles.quantityLabel}>Assignment Quantity</Text>
                <View style={styles.quantityRow}>
                  <IconButton
                    icon="minus"
                    mode="contained"
                    containerColor="#F1F5F9"
                    onPress={() => setQuantity(Math.max(1, quantity - 1))}
                  />
                  <Text style={styles.quantityText}>{quantity}</Text>
                  <IconButton
                    icon="plus"
                    mode="contained"
                    containerColor="#F1F5F9"
                    onPress={() => setQuantity(Math.min(selectedProduct.quantity, quantity + 1))}
                  />
                </View>
              </Surface>
            ) : (
              <View style={{ flex: 1 }}>
                <TouchableOpacity style={styles.scanPlaceholder} onPress={() => setHudVisible(true)}>
                  <MaterialCommunityIcons name="robot" size={48} color={Colors.primaryLight} />
                  <Text style={styles.scanPlaceholderText}>Scan Product Barcode</Text>
                  <Text style={styles.scanPlaceholderSub}>AI scanner binds SKU metadata instantly</Text>
                </TouchableOpacity>

                <Text style={styles.sectionHeader}>Or Choose manually</Text>
                {products?.map((p) => (
                  <TouchableOpacity
                    key={p.id}
                    onPress={() => setSelectedProduct(p)}
                    style={styles.rosterRow}
                  >
                    <Text style={{ fontSize: 20, marginRight: 10 }}>{p.image}</Text>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.rosterName}>{p.name}</Text>
                      <Text style={styles.rosterRef}>{p.ref}</Text>
                    </View>
                    <View style={styles.rosterBadge}>
                      <Text style={styles.rosterBadgeText}>Stock: {p.quantity}</Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {selectedProduct && (
              <PrimaryButton title="Choose Ticket (Step 2)" onPress={() => setStep(2)} icon="arrow-right" />
            )}
          </View>
        )}

        {/* STEP 2: Choose Assignment Method */}
        {step === 2 && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepTitle}>Step 2: Choose Ticket Allocation</Text>
            <Text style={styles.stepDesc}>
              Link this equipment allocation to a Jira support ticket. AI recommendations rank matches by priority.
            </Text>

            {/* Tabs */}
            <View style={styles.tabsRow}>
              <TouchableOpacity
                onPress={() => setMethod('ai')}
                style={[styles.tabBtn, method === 'ai' && styles.tabBtnActive]}
              >
                <Text style={[styles.tabBtnText, method === 'ai' && styles.tabBtnTextActive]}>AI Recommendation</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setMethod('list')}
                style={[styles.tabBtn, method === 'list' && styles.tabBtnActive]}
              >
                <Text style={[styles.tabBtnText, method === 'list' && styles.tabBtnTextActive]}>All Tickets</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setMethod('id')}
                style={[styles.tabBtn, method === 'id' && styles.tabBtnActive]}
              >
                <Text style={[styles.tabBtnText, method === 'id' && styles.tabBtnTextActive]}>Ticket ID</Text>
              </TouchableOpacity>
            </View>

            {/* TAB CONTENT: AI */}
            {method === 'ai' && (
              <View>
                {aiRecommendation ? (
                  <Surface style={styles.dataCard} elevation={1}>
                    <View style={styles.aiBrainHeader}>
                      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                        <MaterialCommunityIcons name="robot" size={20} color={Colors.primaryLight} style={{ marginRight: 6 }} />
                        <Text style={styles.aiBrainTitle}>AI Brain Match</Text>
                      </View>
                      <View style={styles.aiConfidenceBadge}>
                        <Text style={styles.aiConfidenceText}>{aiRecommendation.confidence}% Match</Text>
                      </View>
                    </View>

                    <TicketCard ticket={aiRecommendation.ticket} isSelected />

                    <View style={styles.aiReasonBox}>
                      <Text style={styles.aiReasonText}>"{aiRecommendation.reason}"</Text>
                    </View>

                    <PrimaryButton 
                      title="Confirm Allocation" 
                      onPress={handleConfirmAssignment} 
                      loading={assignStockMutation.isPending}
                      disabled={assignStockMutation.isPending}
                      icon="check-bold" 
                    />
                  </Surface>
                ) : (
                  <Surface style={styles.aiLoadingCard} elevation={1}>
                    <MaterialCommunityIcons name="sync" size={32} color={Colors.primaryLight} style={styles.spinIcon} />
                    <Text style={styles.aiLoadingText}>Computing optimal ticket matches...</Text>
                  </Surface>
                )}
              </View>
            )}

            {/* TAB CONTENT: List */}
            {method === 'list' && (
              <View>
                {tickets?.filter(t => t.status !== 'Assigned').map((ticket) => (
                  <TicketCard
                    key={ticket.id}
                    ticket={ticket}
                    isSelected={targetTicket?.id === ticket.id}
                    onPress={() => setTargetTicket(ticket)}
                  />
                ))}

                {targetTicket && (
                  <PrimaryButton 
                    title="Confirm Assignment" 
                    onPress={handleConfirmAssignment} 
                    loading={assignStockMutation.isPending}
                    disabled={assignStockMutation.isPending}
                    icon="check" 
                  />
                )}
              </View>
            )}

            {/* TAB CONTENT: ID */}
            {method === 'id' && (
              <View>
                <Surface style={styles.dataCard} elevation={1}>
                  <TextInput
                    mode="outlined"
                    placeholder="Enter Jira Ticket ID (e.g. HR-NEW-2026)"
                    value={ticketIdInput}
                    onChangeText={setTicketIdInput}
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

                {targetTicket && (
                  <PrimaryButton 
                    title="Confirm Assignment" 
                    onPress={handleConfirmAssignment} 
                    loading={assignStockMutation.isPending}
                    disabled={assignStockMutation.isPending}
                    icon="check" 
                  />
                )}
              </View>
            )}
          </View>
        )}

        {/* STEP 3: Success Screen */}
        {step === 3 && (
          <View style={[styles.stepContainer, styles.successContainer]}>
            <View style={styles.successIconBox}>
              <MaterialCommunityIcons name="check-bold" size={48} color={Colors.success} />
            </View>
            <Text style={styles.successTitle}>Equipment Assigned!</Text>
            <Text style={styles.successDesc}>
              The inventory database has been updated. Ticket <Text style={{ fontWeight: 'bold' }}>{targetTicket?.id}</Text> is registered as Assigned.
            </Text>

            <Surface style={styles.summaryCard} elevation={1}>
              <Text style={styles.summaryTitle}>Assignment Summary</Text>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Asset Model:</Text>
                <Text style={styles.summaryVal}>{selectedProduct?.name}</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Recipient:</Text>
                <Text style={styles.summaryVal}>{targetTicket?.requester} ({targetTicket?.department})</Text>
              </View>
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Jira Status:</Text>
                <Text style={[styles.summaryVal, { color: Colors.success }]}>CLOSED / ASSIGNED</Text>
              </View>
            </Surface>

            <PrimaryButton title="Return to Dashboard" onPress={() => navigation.navigate('MainDrawer')} icon="home" />
          </View>
        )}
      </ScrollView>

      {/* Product Camera View */}
      <CameraHUD
        visible={hudVisible}
        mode="product"
        onClose={() => setHudVisible(false)}
        onScanResult={handleScanCompleted}
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
    marginBottom: Spacing.lg,
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
  quantityText: {
    fontSize: 18,
    fontWeight: 'bold',
    marginHorizontal: Spacing.lg,
    width: 30,
    textAlign: 'center',
  },
  rosterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    marginVertical: 3,
  },
  rosterName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
  },
  rosterRef: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontFamily: 'monospace',
  },
  rosterBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  rosterBadgeText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.textSecondary,
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
    marginVertical: Spacing.md,
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
  },
  spinIcon: {
    marginBottom: Spacing.md,
  },
  aiLoadingText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: 'bold',
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
  },
});
