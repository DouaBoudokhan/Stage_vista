import React, { useMemo, useState } from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity, ScrollView } from 'react-native';
import { TextInput, IconButton, useTheme, Text } from 'react-native-paper';
import { useInventory } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { InventoryItemCard } from '../components/Cards';
import { LoadingState, EmptyState } from '../components/FeedbackStates';

export default function InventoryScreen({ navigation }: any) {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [isGridView, setIsGridView] = useState(true);
  const [selectedBrand, setSelectedBrand] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const { data: items, isLoading, error, refetch, isFetching } = useInventory({
    search: searchQuery.trim() || undefined,
  });

  const brands = useMemo<string[]>(() => {
    const set = new Set((items?.map((i) => i.brand ?? '').filter((b) => !!b) ?? []));
    return ['All', ...Array.from(set).sort()];
  }, [items]);

  const categories = useMemo<string[]>(() => {
    const set = new Set((items?.map((i) => i.category ?? '').filter((c) => !!c) ?? []));
    return ['All', ...Array.from(set).sort()];
  }, [items]);

  if (isLoading) {
    return <LoadingState message="Loading inventory from database..." />;
  }

  if (error) {
    return (
      <EmptyState
        title="Could not load inventory"
        description="Failed to fetch inventory rows from the FastAPI backend."
        icon="alert-octagon"
      />
    );
  }

  const filteredItems =
    items?.filter((item) => {
      const matchesBrand = selectedBrand === 'All' || item.brand === selectedBrand;
      const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory;
      return matchesBrand && matchesCategory;
    }) ?? [];

  return (
    <View style={styles.container}>
      <View style={styles.headerSection}>
        <TextInput
          mode="outlined"
          placeholder="Search name, article, serial, brand..."
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
        <IconButton
          icon={isGridView ? 'view-list' : 'view-grid'}
          mode="contained"
          size={24}
          containerColor="#FFF"
          iconColor={Colors.primary}
          style={styles.toggleBtn}
          onPress={() => setIsGridView(!isGridView)}
        />
      </View>

      <View style={styles.filterSection}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterScroll}>
          {categories.map((cat) => {
            const isActive = selectedCategory === cat;
            return (
              <TouchableOpacity
                key={cat}
                onPress={() => setSelectedCategory(cat)}
                style={[
                  styles.filterChip,
                  isActive && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
                ]}
              >
                <Text style={[styles.filterChipText, isActive && { color: '#FFF' }]}>{cat}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {brands.length > 1 && (
        <View style={styles.filterSection}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterScroll}>
            {brands.map((brand) => {
              const isActive = selectedBrand === brand;
              return (
                <TouchableOpacity
                  key={brand}
                  onPress={() => setSelectedBrand(brand)}
                  style={[
                    styles.filterChip,
                    isActive && { backgroundColor: Colors.textSecondary, borderColor: Colors.textSecondary },
                  ]}
                >
                  <Text style={[styles.filterChipText, isActive && { color: '#FFF' }]}>{brand}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      )}

      <Text style={styles.countLabel}>
        {filteredItems.length} inventory record{filteredItems.length === 1 ? '' : 's'}
      </Text>

      <FlatList
        data={filteredItems}
        key={isGridView ? 'grid' : 'list'}
        numColumns={isGridView ? 2 : 1}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <InventoryItemCard
            item={item}
            isGrid={isGridView}
            onPress={() => navigation.navigate('ProductDetails', { inventoryId: item.id })}
          />
        )}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <EmptyState
            title="No inventory found"
            description="Receive stock via Workflow 1 to add items to inventory."
            icon="package-variant"
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
  headerSection: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
  },
  searchBar: {
    flex: 1,
    backgroundColor: '#FFF',
  },
  searchBarOutline: {
    borderRadius: BorderRadius.md,
    borderColor: Colors.border,
  },
  toggleBtn: {
    marginLeft: Spacing.sm,
    borderColor: Colors.border,
    borderWidth: 1,
    borderRadius: BorderRadius.md,
  },
  filterSection: {
    paddingVertical: Spacing.xs,
  },
  filterScroll: {
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.xs,
  },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: BorderRadius.sm,
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: Colors.border,
    marginRight: 6,
  },
  filterChipText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
  },
  countLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
    paddingHorizontal: Spacing.lg,
    marginBottom: Spacing.xs,
    fontWeight: '600',
  },
  listContainer: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
});
