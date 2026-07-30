import React, { useState } from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity } from 'react-native';
import { TextInput, Text, useTheme } from 'react-native-paper';
import { useHistory } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { HistoryCard } from '../components/Cards';
import { LoadingState, EmptyState } from '../components/FeedbackStates';

type HistoryFilter = 'all' | 'IN' | 'OUT';

export default function HistoryScreen() {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<HistoryFilter>('all');

  const actionParam = filter === 'all' ? undefined : filter;
  const { data: history, isLoading, error, refetch, isFetching } = useHistory(actionParam);

  if (isLoading) {
    return <LoadingState message="Loading stock history from database..." />;
  }

  if (error) {
    return (
      <EmptyState
        title="Failed to load history"
        description="Could not fetch stock_entries / stock_exits from the FastAPI backend."
        icon="wifi-off"
      />
    );
  }

  const filteredHistory =
    history?.filter((h) => {
      const q = searchQuery.toLowerCase();
      return (
        h.productName.toLowerCase().includes(q) ||
        h.comment.toLowerCase().includes(q) ||
        h.technician.toLowerCase().includes(q) ||
        h.type.toLowerCase().includes(q) ||
        (h.poId ?? '').toLowerCase().includes(q)
      );
    }) ?? [];

  const filters: { key: HistoryFilter; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'IN', label: 'Received' },
    { key: 'OUT', label: 'Taken out' },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.filterRow}>
        {filters.map((f) => {
          const active = filter === f.key;
          return (
            <TouchableOpacity
              key={f.key}
              onPress={() => setFilter(f.key)}
              style={[
                styles.filterChip,
                active && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
              ]}
            >
              <Text style={[styles.filterChipText, active && { color: '#FFF' }]}>{f.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <View style={styles.searchSection}>
        <TextInput
          mode="outlined"
          placeholder="Filter by product, technician, PO..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          style={styles.searchBar}
          outlineStyle={styles.searchBarOutline}
          dense
          left={<TextInput.Icon icon="magnify" color={Colors.textSecondary} />}
          right={
            searchQuery ? (
              <TextInput.Icon icon="close" onPress={() => setSearchQuery('')} color={Colors.textSecondary} />
            ) : null
          }
        />
      </View>

      <Text style={styles.hintText}>
        Received = stock_entries • Taken out = stock_exits (when assign workflow runs)
      </Text>

      <FlatList
        data={filteredHistory}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <HistoryCard movement={item} />}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <EmptyState
            title={filter === 'OUT' ? 'No stock taken out yet' : 'No movements found'}
            description={
              filter === 'OUT'
                ? 'Stock exits appear here after Workflow 2 (Assign) is used.'
                : 'Receive stock via Workflow 1 to see entries here.'
            }
            icon="card-bulleted-off-outline"
          />
        }
        refreshing={isFetching}
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
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.sm,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BorderRadius.full,
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  filterChipText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.textSecondary,
  },
  searchSection: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
  },
  searchBar: {
    backgroundColor: '#FFF',
  },
  searchBarOutline: {
    borderRadius: BorderRadius.md,
    borderColor: Colors.border,
  },
  hintText: {
    fontSize: 9,
    color: Colors.textSecondary,
    paddingHorizontal: Spacing.lg,
    marginBottom: Spacing.xs,
    fontStyle: 'italic',
  },
  listContainer: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
});
