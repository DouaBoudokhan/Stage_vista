import React, { useState } from 'react';
import { StyleSheet, View, FlatList } from 'react-native';
import { TextInput, Appbar, useTheme } from 'react-native-paper';
import { useHistory } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { HistoryCard } from '../components/Cards';
import { LoadingState, EmptyState } from '../components/FeedbackStates';

export default function HistoryScreen({ navigation }: any) {
  const { data: history, isLoading, error, refetch } = useHistory();
  const [searchQuery, setSearchQuery] = useState('');
  const theme = useTheme();

  if (isLoading) {
    return <LoadingState message="Connecting to transaction logs audit..." />;
  }

  if (error) {
    return (
      <EmptyState 
        title="Failed to Sync Logs" 
        description="Could not download activity timeline from FastAPI audit registry."
        icon="wifi-off"
      />
    );
  }

  // Filter logs by search query
  const filteredHistory = history?.filter((h) => {
    return (
      h.productName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      h.comment.toLowerCase().includes(searchQuery.toLowerCase()) ||
      h.technician.toLowerCase().includes(searchQuery.toLowerCase()) ||
      h.type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }) ?? [];

  return (
    <View style={styles.container}>
      {/* Header */}
      <Appbar.Header style={{ backgroundColor: theme.colors.surface }}>
        <Appbar.Action icon="menu" onPress={() => navigation.openDrawer()} />
        <Appbar.Content title="Inventory Logs System" titleStyle={styles.headerTitle} />
        <Appbar.Action icon="refresh" onPress={refetch} />
      </Appbar.Header>

      {/* Search Input */}
      <View style={styles.searchSection}>
        <TextInput
          mode="outlined"
          placeholder="Filter logs by technician, comment, SKU..."
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

      {/* Logs List */}
      <FlatList
        data={filteredHistory}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <HistoryCard movement={item} />}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <EmptyState 
            title="No Movements Found" 
            description="The search keywords matched no entries in the transaction audit trail."
            icon="card-bulleted-off-outline"
          />
        }
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
  headerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  searchSection: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    backgroundColor: '#FFF',
  },
  searchBar: {
    backgroundColor: '#FFF',
  },
  searchBarOutline: {
    borderRadius: BorderRadius.md,
    borderColor: Colors.border,
  },
  listContainer: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
});
