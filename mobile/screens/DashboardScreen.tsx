import React from 'react';
import { StyleSheet, View, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { Text, Avatar, Divider, ProgressBar, IconButton, useTheme } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { useProducts, useTickets, useHistory } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { StatisticCard, HistoryCard } from '../components/Cards';
import { LoadingState, ErrorState } from '../components/FeedbackStates';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

export default function DashboardScreen({ navigation }: any) {
  const { user } = useAuth();
  const theme = useTheme();
  
  // React Query queries
  const { data: products, isLoading: loadingProds, error: errorProds, refetch: refetchProds } = useProducts();
  const { data: tickets, isLoading: loadingTickets, error: errorTickets, refetch: refetchTickets } = useTickets();
  const { data: history, isLoading: loadingHistory, error: errorHistory, refetch: refetchHistory } = useHistory();

  const handleRefresh = async () => {
    await Promise.all([refetchProds(), refetchTickets(), refetchHistory()]);
  };

  const isLoading = loadingProds || loadingTickets || loadingHistory;
  const hasError = errorProds || errorTickets || errorHistory;

  if (isLoading) {
    return <LoadingState message="Connecting to FastAPI inventory telemetry..." />;
  }

  if (hasError) {
    return (
      <ErrorState 
        description="FastAPI service is offline or authentication credentials expired." 
        onRetry={handleRefresh}
      />
    );
  }

  // Calculate metrics
  const totalStockQty = products?.reduce((acc, curr) => acc + curr.quantity, 0) ?? 0;
  const totalValuation = products?.reduce((acc, curr) => acc + (curr.quantity * curr.price), 0) ?? 0;
  const openTicketsCount = tickets?.filter(t => t.status !== 'Assigned').length ?? 0;

  return (
    <ScrollView 
      style={styles.container} 
      contentContainerStyle={styles.contentScroll}
      refreshControl={
        <RefreshControl refreshing={false} onRefresh={handleRefresh} tintColor={Colors.primary} />
      }
    >
      {/* Welcome Header */}
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.greetingText}>Good Morning,</Text>
          <Text style={styles.userNameText}>{user?.name?.split(' ')[0] ?? 'Mariem'}</Text>
        </View>
        <View style={styles.headerRight}>
          <IconButton 
            icon="bell-outline" 
            size={22} 
            iconColor={Colors.textSecondary}
            onPress={() => navigation.navigate('MainDrawer', { screen: 'DashboardTabs', params: { screen: 'Profile' } })} 
          />
          <View style={styles.statusBadge}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>ONLINE</Text>
          </View>
        </View>
      </View>

      {/* Gamification progress */}
      <View style={styles.questCard}>
        <View style={styles.questHeader}>
          <View>
            <Text style={styles.questTag}>Weekly Achievements</Text>
            <Text style={styles.questTitle}>Inspecteur Expert (Level 4)</Text>
          </View>
          <MaterialCommunityIcons name="trophy" size={24} color={Colors.warning} />
        </View>
        <View style={styles.questBody}>
          <View style={styles.questMeta}>
            <Text style={styles.questGoal}>Scan 10 objects with AI</Text>
            <Text style={styles.questCount}>8/10 Scans</Text>
          </View>
          <ProgressBar progress={0.8} color={theme.colors.primary} style={styles.questProgress} />
        </View>
      </View>

      {/* Statistics dashboard */}
      <View style={styles.statsGrid}>
        <StatisticCard
          title="Total Inventory"
          value={`${totalStockQty} Items`}
          subtitle={`€${totalValuation.toLocaleString()} Assets`}
          icon="package-variant"
          iconColor={Colors.primary}
        />
        <StatisticCard
          title="Critical Tickets"
          value={openTicketsCount}
          subtitle="Awaiting allocation"
          icon="alert-circle-outline"
          iconColor={Colors.error}
        />
      </View>

      {/* Quick Action buttons */}
      <View style={styles.actionsSection}>
        <Text style={styles.sectionHeader}>Technician Operations</Text>
        <View style={styles.actionsGrid}>
          <TouchableOpacity 
            onPress={() => navigation.navigate('WorkflowReceive')}
            style={[styles.actionBtn, { backgroundColor: Colors.primary }]}
          >
            <MaterialCommunityIcons name="arrow-down-left" size={26} color="#FFF" />
            <Text style={styles.actionBtnText}>RECEIVE STOCK</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            onPress={() => navigation.navigate('WorkflowAssign')}
            style={[styles.actionBtn, { backgroundColor: Colors.error }]}
          >
            <MaterialCommunityIcons name="arrow-up-right" size={26} color="#FFF" />
            <Text style={styles.actionBtnText}>ASSIGN TICKET</Text>
          </TouchableOpacity>
        </View>
      </View>

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
            history.slice(0, 3).map((item) => (
              <HistoryCard key={item.id} movement={item} />
            ))
          ) : (
            <Text style={styles.emptyHistoryText}>No recent movements logs available.</Text>
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
  questCard: {
    backgroundColor: '#EEF2F6',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  questHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  questTag: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  questTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: 2,
  },
  questBody: {
    marginTop: Spacing.md,
  },
  questMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.xs,
  },
  questGoal: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  questCount: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.text,
  },
  questProgress: {
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(0,0,0,0.05)',
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.md,
  },
  actionsSection: {
    marginBottom: Spacing.lg,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    letterSpacing: 0.5,
  },
  actionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionBtn: {
    flex: 1,
    marginHorizontal: 4,
    height: 70,
    borderRadius: BorderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionBtnText: {
    color: '#FFF',
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 0.5,
    marginTop: 4,
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
