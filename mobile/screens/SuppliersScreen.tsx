import React from 'react';
import { StyleSheet, View, FlatList } from 'react-native';
import { Card, Text, Avatar, useTheme } from 'react-native-paper';
import { useSuppliers } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { LoadingState, EmptyState } from '../components/FeedbackStates';

export default function SuppliersScreen() {
  const { data: suppliers, isLoading, error, refetch } = useSuppliers();
  const theme = useTheme();

  if (isLoading) {
    return <LoadingState message="Connecting to suppliers index..." />;
  }

  if (error) {
    // Fallback static seed list when FastAPI is offline/seeding
    const fallbackSuppliers = [
      { id: 's1', name: 'VistaServices Solutions', contact: 'Marc Dupont', email: 'orders@vistaservices.io' },
      { id: 's2', name: 'LogiCorp Distribution', contact: 'John Smith', email: 'sales@logicorp.com' },
      { id: 's3', name: 'Apple Enterprise Store', contact: 'Business Team', email: 'business@apple.com' },
      { id: 's4', name: 'NetWorld Supplies', contact: 'Sarah Jenkins', email: 'support@networld.net' }
    ];

    return (
      <View style={styles.container}>
        <FlatList
          data={fallbackSuppliers}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <Card style={styles.card}>
              <Card.Content style={styles.cardContent}>
                <Avatar.Text size={36} label={item.name[0]} style={{ backgroundColor: theme.colors.primary }} />
                <View style={styles.textSection}>
                  <Text style={styles.name}>{item.name}</Text>
                  <Text style={styles.meta}>Contact: {item.contact} • {item.email}</Text>
                </View>
              </Card.Content>
            </Card>
          )}
          contentContainerStyle={styles.listContainer}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={suppliers}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <Card.Content style={styles.cardContent}>
              <Avatar.Text size={36} label={item.name[0]} style={{ backgroundColor: theme.colors.primary }} />
              <View style={styles.textSection}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.meta}>Contact: {item.contact} • {item.email}</Text>
              </View>
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
  cardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.md,
  },
  textSection: {
    marginLeft: Spacing.md,
    flex: 1,
  },
  name: {
    fontSize: 13,
    fontWeight: 'bold',
    color: Colors.text,
  },
  meta: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },
});
