import React from 'react';
import { StyleSheet, View, FlatList, TouchableOpacity } from 'react-native';
import { Appbar, Card, Text, useTheme } from 'react-native-paper';
import { useNotifications } from '../hooks/useApi';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { LoadingState, EmptyState } from '../components/FeedbackStates';

export default function NotificationsScreen({ navigation }: any) {
  const theme = useTheme();
  const { data: notifications, isLoading, error, refetch } = useNotifications();

  if (isLoading) {
    return <LoadingState message="Connecting to notifications registry..." />;
  }

  if (error) {
    return (
      <EmptyState 
        title="Failed to Load Alerts" 
        description="Could not download notifications feed from FastAPI backend."
        icon="alert-circle-outline"
      />
    );
  }

  return (
    <View style={styles.container}>
      <Appbar.Header style={{ backgroundColor: theme.colors.surface }}>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="IT Center Notifications" titleStyle={styles.headerTitle} />
        <Appbar.Action icon="check-all" onPress={() => {}} />
      </Appbar.Header>

      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Card style={[styles.card, item.unread && styles.unreadCard]}>
            <Card.Content style={styles.cardContent}>
              <View style={[styles.unreadDot, !item.unread && { backgroundColor: 'transparent' }]} />
              <View style={styles.textSection}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>{item.title}</Text>
                  <Text style={styles.cardTime}>{item.time}</Text>
                </View>
                <Text style={styles.cardDesc}>{item.desc}</Text>
              </View>
            </Card.Content>
          </Card>
        )}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <EmptyState 
            title="Clean Inbox" 
            description="You have cleared all urgent telemetry alerts and low-stock indicators."
            icon="bell-ring-outline"
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
  listContainer: {
    padding: Spacing.md,
  },
  card: {
    marginVertical: 4,
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.md,
  },
  unreadCard: {
    backgroundColor: Colors.primary + '0A',
    borderColor: Colors.primary + '33',
    borderWidth: 1,
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.md,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primaryLight,
    marginRight: Spacing.md,
  },
  textSection: {
    flex: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
  },
  cardTime: {
    fontSize: 9,
    color: Colors.textMuted,
    fontFamily: 'monospace',
  },
  cardDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 4,
    lineHeight: 15,
  },
});
