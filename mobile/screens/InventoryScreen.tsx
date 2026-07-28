import React, { useState } from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity, ScrollView } from 'react-native';
import { TextInput, IconButton, useTheme, Surface, Text } from 'react-native-paper';
import { useProducts } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { ProductCard } from '../components/Cards';
import { LoadingState, EmptyState } from '../components/FeedbackStates';

export default function InventoryScreen({ navigation }: any) {
  const { data: products, isLoading, error, refetch } = useProducts();
  const theme = useTheme();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [isGridView, setIsGridView] = useState(true);
  const [selectedBrand, setSelectedBrand] = useState('All');

  const brands = ['All', 'Dell', 'HP', 'Apple', 'EPOS', 'Logitech'];

  if (isLoading) {
    return <LoadingState message="Loading inventory database..." />;
  }

  if (error) {
    return (
      <EmptyState 
        title="Telemetry Failed" 
        description="Could not download products catalog from FastAPI database."
        icon="alert-octagon"
      />
    );
  }

  // Filter products based on search query & selected brand
  const filteredProducts = products?.filter((p) => {
    const matchesSearch = 
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      p.ref.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.category.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesBrand = 
      selectedBrand === 'All' || 
      p.brand.toLowerCase() === selectedBrand.toLowerCase();

    return matchesSearch && matchesBrand;
  }) ?? [];

  return (
    <View style={styles.container}>
      {/* Search & Layout Actions */}
      <View style={styles.headerSection}>
        <TextInput
          mode="outlined"
          placeholder="Find SKU, reference, category..."
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

      {/* Brand Filters Scroll */}
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
                  isActive && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary }
                ]}
              >
                <Text style={[styles.filterChipText, isActive && { color: '#FFF' }]}>
                  {brand}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      {/* Products list */}
      <FlatList
        data={filteredProducts}
        key={isGridView ? 'grid' : 'list'}
        numColumns={isGridView ? 2 : 1}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ProductCard
            product={item}
            isGrid={isGridView}
            onPress={() => navigation.navigate('ProductDetails', { productId: item.id })}
          />
        )}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <EmptyState 
            title="Product Not Found" 
            description="The searched SKU or query matches no registered hardware configurations."
            icon="clipboard-alert"
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  filterSection: {
    paddingVertical: Spacing.xs,
  },
  filterScroll: {
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.xs,
  },
  filterChip: {
    paddingHorizontal: 16,
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
  listContainer: {
    padding: Spacing.md,
    paddingBottom: 40,
  },
});
