import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Text, Surface, IconButton, Divider, useTheme } from 'react-native-paper';
import { useProduct } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { PRODUCT_ICONS } from '../constants/config';
import { PrimaryButton, SecondaryButton } from '../components/AppButtons';
import { LoadingState, ErrorState } from '../components/FeedbackStates';

export default function ProductDetailsScreen({ route, navigation }: any) {
  const { productId } = route.params;
  const theme = useTheme();
  const { data: product, isLoading, error, refetch } = useProduct(productId);

  if (isLoading) {
    return <LoadingState message="Connecting to asset registry..." />;
  }

  if (error || !product) {
    return (
      <ErrorState 
        title="Asset Not Found" 
        description="This hardware record has been removed or unregistered from central catalog."
        onRetry={() => navigation.goBack()}
        icon="alert-octagon"
      />
    );
  }

  const emoji = PRODUCT_ICONS[product.category] || PRODUCT_ICONS.Default;

  return (
    <View style={styles.container}>
      {/* Header bar */}
      <View style={styles.headerBar}>
        <IconButton icon="arrow-left" size={24} onPress={() => navigation.goBack()} />
        <Text style={styles.headerTitle}>Hardware Detail</Text>
        <IconButton icon="dots-vertical" size={24} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Visual overview */}
        <Surface style={styles.visualSection} elevation={1}>
          <Text style={styles.visualEmoji}>{emoji}</Text>
          <Text style={styles.visualName}>{product.name}</Text>
          <Text style={styles.visualRef}>SKU: {product.ref}</Text>
        </Surface>

        {/* Detailed stats grids */}
        <Text style={styles.sectionHeader}>Registry Details</Text>
        <View style={styles.gridSection}>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Category</Text>
            <Text style={styles.cellValue}>{product.category}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Brand</Text>
            <Text style={styles.cellValue}>{product.brand}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Warehouse Location</Text>
            <Text style={styles.cellValue}>{product.warehouse}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Shelving Unit</Text>
            <Text style={styles.cellValue}>{product.shelf}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Unit Valuation</Text>
            <Text style={styles.cellValue}>€{product.price}</Text>
          </View>
          <View style={styles.gridCell}>
            <Text style={styles.cellLabel}>Suppliers Source</Text>
            <Text style={styles.cellValue} numberOfLines={1}>{product.supplier}</Text>
          </View>
        </View>

        {/* Allocation totals */}
        <Text style={styles.sectionHeader}>Stock Allocation</Text>
        <Surface style={styles.allocationCard} elevation={1}>
          <View style={styles.allocationRow}>
            <View>
              <Text style={styles.allocationLabel}>Available Count</Text>
              <Text style={[styles.allocationValue, { color: theme.colors.primary }]}>
                {product.quantity} Units
              </Text>
            </View>
            <Divider style={styles.verticalDivider} />
            <View>
              <Text style={styles.allocationLabel}>Reserved Tickets</Text>
              <Text style={[styles.allocationValue, { color: Colors.text }]}>
                {product.reserved} Units
              </Text>
            </View>
          </View>
        </Surface>

        {/* Action Panel */}
        <View style={styles.actionPanel}>
          <PrimaryButton 
            title="Assign To Support Ticket" 
            onPress={() => navigation.navigate('WorkflowAssign', { preselectedProduct: product })}
          />
          <SecondaryButton 
            title="Receive Box Shipments" 
            onPress={() => navigation.navigate('WorkflowReceive', { preselectedProduct: product })}
          />
        </View>
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
    paddingTop: Spacing.xl + 20,
    backgroundColor: '#FFF',
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    paddingHorizontal: Spacing.sm,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.text,
  },
  scrollContent: {
    padding: Spacing.lg,
  },
  visualSection: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    paddingVertical: Spacing.xl,
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  visualEmoji: {
    fontSize: 56,
    marginBottom: Spacing.md,
  },
  visualName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.text,
    textAlign: 'center',
    paddingHorizontal: Spacing.md,
  },
  visualRef: {
    fontSize: 11,
    fontFamily: 'monospace',
    color: Colors.textSecondary,
    marginTop: 4,
  },
  sectionHeader: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginTop: Spacing.md,
    marginBottom: Spacing.sm,
    letterSpacing: 0.5,
  },
  gridSection: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -4,
  },
  gridCell: {
    width: '50%',
    padding: 4,
  },
  cellLabel: {
    fontSize: 9,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textMuted,
  },
  cellValue: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: 2,
    backgroundColor: '#FFF',
    padding: 10,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  allocationCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginTop: Spacing.xs,
  },
  allocationRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  verticalDivider: {
    width: 1,
    height: 40,
    backgroundColor: Colors.border,
  },
  allocationLabel: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    textAlign: 'center',
  },
  allocationValue: {
    fontSize: 18,
    fontWeight: '900',
    marginTop: 4,
    textAlign: 'center',
  },
  actionPanel: {
    marginTop: Spacing.xl,
    marginBottom: Spacing.xxl,
  },
});
