import React from 'react';
import { StyleSheet, View, TouchableOpacity } from 'react-native';
import { Text } from 'react-native-paper';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

export default function WorkflowSelectionScreen({ navigation }: any) {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Choose Workflow</Text>
        <Text style={styles.subtitle}>Select the operation you want to perform</Text>
      </View>

      <View style={styles.workflowsContainer}>
        {/* Workflow 1: Receive Equipment */}
        <TouchableOpacity
          style={[styles.workflowCard, { backgroundColor: Colors.primary }]}
          onPress={() => navigation.navigate('WorkflowReceive')}
        >
          <View style={styles.iconCircle}>
            <MaterialCommunityIcons name="arrow-down-left" size={40} color={Colors.primary} />
          </View>
          <Text style={styles.workflowTitle}>Workflow 1</Text>
          <Text style={styles.workflowLabel}>RECEIVE EQUIPMENT</Text>
          <Text style={styles.workflowDescription}>
            Scan incoming stock, register new items in inventory
          </Text>
          <View style={styles.badge}>
            <MaterialCommunityIcons name="camera" size={16} color="#FFF" />
            <Text style={styles.badgeText}>Scan Barcode / AI Vision</Text>
          </View>
        </TouchableOpacity>

        {/* Workflow 2: Assign to Ticket */}
        <TouchableOpacity
          style={[styles.workflowCard, { backgroundColor: Colors.error }]}
          onPress={() => navigation.navigate('WorkflowAssign')}
        >
          <View style={styles.iconCircle}>
            <MaterialCommunityIcons name="arrow-up-right" size={40} color={Colors.error} />
          </View>
          <Text style={styles.workflowTitle}>Workflow 2</Text>
          <Text style={styles.workflowLabel}>ASSIGN TO TICKET</Text>
          <Text style={styles.workflowDescription}>
            Allocate inventory items to work tickets
          </Text>
          <View style={styles.badge}>
            <MaterialCommunityIcons name="ticket" size={16} color="#FFF" />
            <Text style={styles.badgeText}>Link to Request</Text>
          </View>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    padding: Spacing.xl,
  },
  header: {
    marginTop: 20,
    marginBottom: 40,
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  workflowsContainer: {
    flex: 1,
    justifyContent: 'center',
    gap: 20,
  },
  workflowCard: {
    borderRadius: BorderRadius.xl,
    padding: Spacing.xl,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
    minHeight: 240,
    justifyContent: 'center',
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#FFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  workflowTitle: {
    fontSize: 12,
    color: '#FFF',
    opacity: 0.9,
    fontWeight: '600',
    marginBottom: 4,
  },
  workflowLabel: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFF',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  workflowDescription: {
    fontSize: 13,
    color: '#FFF',
    opacity: 0.9,
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 20,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
    gap: 6,
  },
  badgeText: {
    fontSize: 11,
    color: '#FFF',
    fontWeight: '600',
  },
});
