import React from 'react';
import { StyleSheet, View, ScrollView, RefreshControl } from 'react-native';
import { Text, Surface, ProgressBar, useTheme } from 'react-native-paper';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { StatisticCard } from '../components/Cards';
import { useDashboard } from '../hooks/useApi';
import { LoadingState, ErrorState } from '../components/FeedbackStates';

export default function ReportsScreen() {
  const theme = useTheme();
  const { data: kpis, isLoading, error, refetch, isFetching } = useDashboard();

  if (isLoading) {
    return <LoadingState message="Loading analytics from database..." />;
  }

  if (error || !kpis) {
    return (
      <ErrorState
        description="Could not load analytics reports from the FastAPI backend."
        onRetry={refetch}
      />
    );
  }

  const sortedCategories = [...kpis.categoryStock].sort(
    (a, b) => b.stockOnHand - a.stockOnHand,
  );
  const maxStock = sortedCategories[0]?.stockOnHand ?? 1;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={Colors.primary} />
      }
    >
      <Text style={styles.sectionHeader}>Analytics Reports Overview</Text>

      <View style={styles.statsGrid}>
        <StatisticCard
          title="Total Inventory"
          value={`${kpis.totalInventoryQuantity} Units`}
          subtitle={`${kpis.totalInventoryRecords} SKU records`}
          icon="package-variant"
          iconColor={Colors.primary}
        />
        <StatisticCard
          title="Ticket Fulfillment"
          value={`${kpis.ticketFulfillmentRate}%`}
          subtitle={`${kpis.openTickets} open of ${kpis.totalTickets}`}
          icon="chart-donut"
          iconColor={Colors.success}
        />
      </View>

      <View style={styles.statsGrid}>
        <StatisticCard
          title="Low Stock Alerts"
          value={kpis.lowStockAlertCount}
          subtitle="Computed from live stock"
          icon="alert-decagram-outline"
          iconColor={Colors.warning}
        />
        <StatisticCard
          title="Weekly Movements"
          value={kpis.movementsThisWeek}
          subtitle={`${kpis.stockInThisWeek} in / ${kpis.stockOutThisWeek} out`}
          icon="swap-vertical"
          iconColor={Colors.primary}
        />
      </View>

      <Text style={styles.sectionHeader}>Stock by Product Type</Text>
      <Surface style={styles.card} elevation={1}>
        {sortedCategories.length > 0 ? (
          sortedCategories.map((category) => {
            const progress = maxStock > 0 ? category.stockOnHand / maxStock : 0;
            const isLow = category.stockOnHand <= 5;
            return (
              <View key={category.productType} style={styles.barRow}>
                <View style={styles.barLabelRow}>
                  <Text style={styles.barLabel}>{category.productType}</Text>
                  <Text style={styles.barVal}>
                    {category.stockOnHand} units ({category.sharePercent}%)
                  </Text>
                </View>
                <ProgressBar
                  progress={progress}
                  color={isLow ? Colors.error : theme.colors.primary}
                  style={styles.bar}
                />
                <Text style={styles.barMeta}>
                  {category.inventoryRecords} inventory record
                  {category.inventoryRecords === 1 ? '' : 's'}
                </Text>
              </View>
            );
          })
        ) : (
          <Text style={styles.emptyText}>No inventory data available yet.</Text>
        )}
      </Surface>

      {kpis.lowStockAlerts.length > 0 && (
        <>
          <Text style={styles.sectionHeader}>Low Stock Alerts</Text>
          <Surface style={styles.card} elevation={1}>
            {kpis.lowStockAlerts.map((alert, index) => (
              <View key={`${alert.alertType}-${alert.inventoryId ?? alert.productType}-${index}`} style={styles.alertRow}>
                <Text style={styles.alertLabel}>
                  {alert.alertType === 'product_type'
                    ? `${alert.productType} (category)`
                    : alert.productName ?? alert.articleNumber ?? `Item #${alert.inventoryId}`}
                </Text>
                <Text style={[styles.alertQty, alert.severity === 'critical' && styles.alertQtyCritical]}>
                  {alert.currentQuantity} / threshold {alert.threshold}
                </Text>
              </View>
            ))}
          </Surface>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.lg,
  },
  sectionHeader: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    marginTop: Spacing.md,
    letterSpacing: 0.5,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.md,
  },
  card: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  barRow: {
    marginVertical: Spacing.sm,
  },
  barLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  barLabel: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.text,
  },
  barVal: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: Colors.textSecondary,
  },
  barMeta: {
    fontSize: 9,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  bar: {
    height: 8,
    borderRadius: 4,
  },
  alertRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  alertLabel: {
    flex: 1,
    fontSize: 11,
    color: Colors.text,
    marginRight: Spacing.sm,
  },
  alertQty: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.warning,
  },
  alertQtyCritical: {
    color: Colors.error,
  },
  emptyText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: Spacing.md,
  },
});
