import React from 'react';
import { StyleSheet, View, FlatList } from 'react-native';
import { Card, Text, useTheme } from 'react-native-paper';
import { usePurchaseOrders } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { LoadingState, EmptyState } from '../components/FeedbackStates';

export default function PurchaseOrdersScreen() {
  const { data: purchaseOrders, isLoading, error, refetch } = usePurchaseOrders();
  const theme = useTheme();

  if (isLoading) {
    return <LoadingState message="Connecting to Purchase Orders..." />;
  }

  // Handle error with fallback data
  const poList = error ? [
    {
      id: 'PO-2026-0042',
      supplier: 'VistaServices Solutions',
      date: '2026-07-10',
      status: 'Pending',
      items: [
        { ref: 'DELL-LAT-5440', name: 'Dell Latitude 5440', brand: 'Dell', quantity: 10, received: 0 },
        { ref: 'EPOS-IMP-100', name: 'IMPACT 100 Stereo', brand: 'EPOS', quantity: 15, received: 0 }
      ]
    }
  ] : purchaseOrders;

  return (
    <View style={styles.container}>
      <FlatList
        data={poList}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <Card.Content>
              <View style={styles.headerRow}>
                <Text style={styles.poId}>{item.id}</Text>
                <View style={[styles.badge, item.status === 'Completed' ? styles.badgeSuccess : styles.badgePending]}>
                  <Text style={[styles.badgeText, item.status === 'Completed' ? styles.badgeTextSuccess : styles.badgeTextPending]}>
                    {item.status}
                  </Text>
                </View>
              </View>
              <Text style={styles.meta}>Supplier: {item.supplier}</Text>
              <Text style={styles.meta}>Date: {item.date}</Text>
            </Card.Content>
          </Card>
        )}
        contentContainerStyle={styles.listContainer}
        refreshing={false}
        onRefresh={refetch}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  listContainer: {
    padding: Spacing.md,
  },
  card: {
    marginVertical: 4,
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.md,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  poId: {
    fontSize: 13,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  meta: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeSuccess: {
    backgroundColor: '#ECFDF5',
  },
  badgePending: {
    backgroundColor: '#FFFBEB',
  },
  badgeText: {
    fontSize: 9,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  badgeTextSuccess: {
    color: Colors.success,
  },
  badgeTextPending: {
    color: Colors.warning,
  },
});
