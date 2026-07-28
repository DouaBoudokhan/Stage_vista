import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Text, Surface, ProgressBar, useTheme } from 'react-native-paper';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { StatisticCard } from '../components/Cards';

export default function ReportsScreen() {
  const theme = useTheme();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.sectionHeader}>Analytics Reports Overview</Text>

      <View style={styles.statsGrid}>
        <StatisticCard
          title="Total Valuation"
          value="€28,500"
          subtitle="Enterprise IT assets"
          icon="currency-eur"
          iconColor={Colors.primary}
        />
        <StatisticCard
          title="Fulfillment Rate"
          value="94.2%"
          subtitle="PO received vs requested"
          icon="chart-donut"
          iconColor={Colors.success}
        />
      </View>

      <Text style={styles.sectionHeader}>Category Allocations</Text>
      <Surface style={styles.card} elevation={1}>
        <View style={styles.barRow}>
          <View style={styles.barLabelRow}>
            <Text style={styles.barLabel}>Laptops & Workstations</Text>
            <Text style={styles.barVal}>18 left (65%)</Text>
          </View>
          <ProgressBar progress={0.65} color={theme.colors.primary} style={styles.bar} />
        </View>

        <View style={styles.barRow}>
          <View style={styles.barLabelRow}>
            <Text style={styles.barLabel}>Audio & Headsets</Text>
            <Text style={styles.barVal}>20 left (85%)</Text>
          </View>
          <ProgressBar progress={0.85} color={theme.colors.primary} style={styles.bar} />
        </View>

        <View style={styles.barRow}>
          <View style={styles.barLabelRow}>
            <Text style={styles.barLabel}>Networking Equipment</Text>
            <Text style={styles.barVal}>1 left (10%)</Text>
          </View>
          <ProgressBar progress={0.1} color={Colors.error} style={styles.bar} />
        </View>
      </Surface>
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
  bar: {
    height: 8,
    borderRadius: 4,
  },
});
