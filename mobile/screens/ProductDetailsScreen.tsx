import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Text, Surface, IconButton, useTheme } from 'react-native-paper';
import { useInventoryItem } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { PRODUCT_ICONS } from '../constants/config';
import { LoadingState, ErrorState } from '../components/FeedbackStates';

export default function ProductDetailsScreen({ route, navigation }: any) {
  const inventoryId = route.params?.inventoryId as number;
  const theme = useTheme();
  const { data: item, isLoading, error } = useInventoryItem(inventoryId);

  if (isLoading) {
    return <LoadingState message="Loading inventory record..." />;
  }

  if (error || !item) {
    return (
      <ErrorState
        title="Record not found"
        description="This inventory row does not exist or was removed."
        onRetry={() => navigation.goBack()}
        icon="alert-octagon"
      />
    );
  }

  const emoji = PRODUCT_ICONS[item.category ?? ''] || PRODUCT_ICONS.Default;

  return (
    <View style={styles.container}>
      <View style={styles.headerBar}>
        <IconButton icon="arrow-left" size={24} onPress={() => navigation.goBack()} />
        <Text style={styles.headerTitle}>Inventory Detail</Text>
        <View style={{ width: 48 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Surface style={styles.visualSection} elevation={1}>
          <Text style={styles.visualEmoji}>{emoji}</Text>
          <Text style={styles.visualName}>{item.productName}</Text>
          <Text style={styles.visualRef}>Article: {item.articleNumber}</Text>
        </Surface>

        <Text style={styles.sectionHeader}>Product Details</Text>
        <View style={styles.gridSection}>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Category</Text>
            <Text style={styles.cellValue}>{item.category ?? '—'}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Brand</Text>
            <Text style={styles.cellValue}>{item.brand}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Quantity</Text>
            <Text style={styles.cellValue}>{item.quantityAvailable}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Status</Text>
            <Text style={styles.cellValue}>{item.status}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Serial Number</Text>
            <Text style={styles.cellValue} numberOfLines={2}>{item.serialNumber ?? '—'}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Purchase Order</Text>
            <Text style={styles.cellValue}>{item.poNumber ?? item.purchaseOrderId ?? '—'}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Received by</Text>
            <Text style={styles.cellValue}>{item.receivedBy}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Received at</Text>
            <Text style={styles.cellValue}>
              {item.receivedAt ? new Date(item.receivedAt).toLocaleString() : '—'}
            </Text>
          </View>
        </View>

        <Surface style={styles.idCard} elevation={1}>
          <Text style={styles.cellLabel}>Inventory ID</Text>
          <Text style={styles.idValue}>#{item.id}</Text>
          <Text style={styles.cellLabel}>Product type ID</Text>
          <Text style={styles.idValue}>#{item.productId}</Text>
        </Surface>
      </ScrollView>
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
    paddingHorizontal: Spacing.xs,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.text,
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingBottom: 40,
  },
  visualSection: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  visualEmoji: {
    fontSize: 48,
    marginBottom: Spacing.sm,
  },
  visualName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.text,
    textAlign: 'center',
  },
  visualRef: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    letterSpacing: 0.5,
  },
  gridSection: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: Spacing.lg,
  },
  gridCell: {
    width: '50%',
    paddingVertical: Spacing.sm,
    paddingRight: Spacing.sm,
  },
  cellLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  cellValue: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
  },
  idCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
  },
  idValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: Spacing.sm,
  },
});
