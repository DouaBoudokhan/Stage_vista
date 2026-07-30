import React from 'react';
import { StyleSheet, View, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { Text, IconButton } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { useDashboard, useHistory } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { StatisticCard, HistoryCard } from '../components/Cards';
import { LoadingState, ErrorState } from '../components/FeedbackStates';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good Morning';
  if (hour < 18) return 'Good Afternoon';
  return 'Good Evening';
}

export default function DashboardScreen({ navigation }: any) {
  const { user } = useAuth();

  const { data: kpis, isLoading, error, refetch, isFetching } = useDashboard();
  const { data: history, refetch: refetchHistory } = useHistory();

  const handleRefresh = async () => {
    await Promise.all([refetch(), refetchHistory()]);
  };

  if (isLoading) {
    return <LoadingState message="Loading dashboard from database..." />;
  }

  if (error || !kpis) {
    return (
      <ErrorState
        description="Could not load dashboard KPIs from the FastAPI backend."
        onRetry={handleRefresh}
      />
    );
  }

  const categoryAlerts = kpis.lowStockAlerts.filter((a) => a.alertType === 'product_type');
  const itemAlerts = kpis.lowStockAlerts.filter((a) => a.alertType === 'inventory_item');

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentScroll}
      refreshControl={
        <RefreshControl refreshing={isFetching} onRefresh={handleRefresh} tintColor={Colors.primary} />
      }
    >
      {/* Welcome Header */}
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.greetingText}>{getGreeting()},</Text>
          <Text style={styles.userNameText}>{user?.name?.split(' ')[0] ?? 'Technician'}</Text>
        </View>
        <View style={styles.headerRight}>
          <IconButton
            icon="bell-outline"
            size={22}
            iconColor={Colors.textSecondary}
            onPress={() =>
              navigation.navigate('MainDrawer', {
                screen: 'DashboardTabs',
                params: { screen: 'Profile' },
              })
            }
          />
          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>LIVE</Text>
          </View>
        </View>
      </View>

      {/* Weekly activity from real movement data */}
      <View style={styles.activityCard}>
        <View style={styles.activityHeader}>
          <View>
            <Text style={styles.activityTag}>This Week</Text>
            <Text style={styles.activityTitle}>{kpis.movementsThisWeek} Stock Movements</Text>
          </View>
          <MaterialCommunityIcons name="chart-timeline-variant" size={24} color={Colors.primary} />
        </View>
        <View style={styles.activityStatsRow}>
          <View style={styles.activityStat}>
            <Text style={styles.activityStatValue}>{kpis.stockInThisWeek}</Text>
            <Text style={styles.activityStatLabel}>Received</Text>
          </View>
          <View style={styles.activityStatDivider} />
          <View style={styles.activityStat}>
            <Text style={styles.activityStatValue}>{kpis.stockOutThisWeek}</Text>
            <Text style={styles.activityStatLabel}>Assigned</Text>
          </View>
          <View style={styles.activityStatDivider} />
          <View style={styles.activityStat}>
            <Text style={styles.activityStatValue}>{kpis.totalPurchaseOrders}</Text>
            <Text style={styles.activityStatLabel}>POs</Text>
          </View>
        </View>
      </View>

      {/* Statistics dashboard */}
      <View style={styles.statsGrid}>
        <StatisticCard
          title="Total Inventory"
          value={`${kpis.totalInventoryQuantity} Units`}
          subtitle={`${kpis.totalInventoryRecords} records`}
          icon="package-variant"
          iconColor={Colors.primary}
        />
        <StatisticCard
          title="Open Tickets"
          value={kpis.openTickets}
          subtitle={`${kpis.totalTickets} total`}
          icon="alert-circle-outline"
          iconColor={Colors.error}
        />
      </View>

      <View style={styles.statsGrid}>
        <StatisticCard
          title="Product Types"
          value={kpis.activeProductTypes}
          subtitle={`${kpis.totalProductTypes} categories`}
          icon="shape-outline"
          iconColor={Colors.success}
        />
        <StatisticCard
          title="Low Stock Alerts"
          value={categoryAlerts.length}
          subtitle={
            itemAlerts.length > 0
              ? `${itemAlerts.length} SKU-level alert${itemAlerts.length === 1 ? '' : 's'}`
              : `${kpis.totalProductTypes} categories tracked`
          }
          icon="alert-decagram-outline"
          iconColor={Colors.warning}
        />
      </View>

      {/* Low stock alerts — all category-level alerts (never truncated) */}
      {(categoryAlerts.length > 0 || itemAlerts.length > 0) && (
        <View style={styles.alertsSection}>
          <Text style={styles.sectionHeader}>Low Stock Alerts</Text>
          {categoryAlerts.map((alert, index) => (
            <View
              key={`category-${alert.productType}-${index}`}
              style={styles.alertRow}
            >
              <MaterialCommunityIcons
                name={alert.severity === 'critical' ? 'alert-circle' : 'alert-outline'}
                size={18}
                color={alert.severity === 'critical' ? Colors.error : Colors.warning}
              />
              <View style={styles.alertTextBlock}>
                <Text style={styles.alertTitle}>{alert.productType} category</Text>
                <Text style={styles.alertMeta}>
                  {alert.currentQuantity} units in stock (threshold: {alert.threshold})
                </Text>
              </View>
            </View>
          ))}
          {itemAlerts.map((alert, index) => (
            <View
              key={`item-${alert.inventoryId ?? index}-${index}`}
              style={styles.alertRow}
            >
              <MaterialCommunityIcons
                name={alert.severity === 'critical' ? 'alert-circle' : 'alert-outline'}
                size={18}
                color={alert.severity === 'critical' ? Colors.error : Colors.warning}
              />
              <View style={styles.alertTextBlock}>
                <Text style={styles.alertTitle}>
                  {alert.productName ?? alert.articleNumber ?? 'Inventory item'}
                </Text>
                <Text style={styles.alertMeta}>
                  {alert.currentQuantity} left (threshold: {alert.threshold}) • {alert.productType}
                </Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Recent History log */}
      <View style={styles.historySection}>
        <View style={styles.historyHeaderRow}>
          <Text style={styles.sectionHeader}>Recent Activity Log</Text>
          <TouchableOpacity onPress={() => navigation.navigate('History')}>
            <Text style={styles.viewAllText}>View All</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.historyList}>
          {history && history.length > 0 ? (
            history.slice(0, 3).map((item) => <HistoryCard key={item.id} movement={item} />)
          ) : (
            <Text style={styles.emptyHistoryText}>No recent movement logs available.</Text>
          )}
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  contentScroll: {
    padding: Spacing.lg,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  greetingText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  userNameText: {
    fontSize: 22,
    fontWeight: '900',
    color: Colors.text,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: '#A7F3D0',
    marginLeft: Spacing.xs,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.success,
    marginRight: 4,
  },
  statusText: {
    fontSize: 8,
    fontWeight: 'bold',
    color: Colors.success,
    letterSpacing: 0.5,
  },
  activityCard: {
    backgroundColor: '#EEF2F6',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  activityTag: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  activityTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: 2,
  },
  activityStatsRow: {
    flexDirection: 'row',
    marginTop: Spacing.md,
    alignItems: 'center',
  },
  activityStat: {
    flex: 1,
    alignItems: 'center',
  },
  activityStatValue: {
    fontSize: 16,
    fontWeight: '900',
    color: Colors.text,
  },
  activityStatLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  activityStatDivider: {
    width: 1,
    height: 28,
    backgroundColor: 'rgba(0,0,0,0.08)',
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.md,
  },
  alertsSection: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: '#FEE2E2',
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    letterSpacing: 0.5,
  },
  alertRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: Spacing.sm,
  },
  alertTextBlock: {
    flex: 1,
    marginLeft: Spacing.sm,
  },
  alertTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
  },
  alertMeta: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  historySection: {
    marginBottom: Spacing.xl,
  },
  historyHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  viewAllText: {
    fontSize: 11,
    color: Colors.primaryLight,
    fontWeight: 'bold',
  },
  historyList: {
    marginTop: 2,
  },
  emptyHistoryText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: Spacing.lg,
  },
});
