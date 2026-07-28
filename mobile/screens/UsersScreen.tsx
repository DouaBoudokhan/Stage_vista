import React from 'react';
import { StyleSheet, View, FlatList } from 'react-native';
import { Card, Text, Avatar, useTheme } from 'react-native-paper';
import { Colors, Spacing, BorderRadius } from '../constants/theme';

export default function UsersScreen() {
  const theme = useTheme();

  const usersList = [
    { id: 'u1', name: 'Mariem Alawi', email: 'it-admin@vistaservices.io', role: 'IT Ops Coordinator' },
    { id: 'u2', name: 'Thomas Martin', email: 'thomas@vistaservices.io', role: 'Support Technician' },
    { id: 'u3', name: 'Sarah Conner', email: 'sarah@vistaservices.io', role: 'Infrastructure Lead' }
  ];

  return (
    <View style={styles.container}>
      <FlatList
        data={usersList}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <Card.Content style={styles.cardContent}>
              <Avatar.Text size={36} label={item.name.split(' ').map(n=>n[0]).join('')} style={{ backgroundColor: theme.colors.primary }} />
              <View style={styles.textSection}>
                <Text style={styles.name}>{item.name}</Text>
                <Text style={styles.email}>{item.email}</Text>
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{item.role}</Text>
                </View>
              </View>
            </Card.Content>
          </Card>
        )}
        contentContainerStyle={styles.listContainer}
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
  email: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  badge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.textSecondary,
  },
});
