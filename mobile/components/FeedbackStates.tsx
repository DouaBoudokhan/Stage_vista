import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Text, ActivityIndicator } from 'react-native-paper';
import { Colors, Spacing } from '../constants/theme';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { PrimaryButton } from './AppButtons';

// ─── Loading Skeleton / Spinner ──────────────────────
export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading operations...' }) => {
  return (
    <View style={styles.centerContainer}>
      <ActivityIndicator size="large" color={Colors.primary} />
      <Text style={styles.messageText}>{message}</Text>
    </View>
  );
};

// ─── Empty State ──────────────────────────────────────
interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description = 'Database is currently empty. Scan incoming boxes or add stock details.',
  icon = 'package-variant',
}) => {
  return (
    <View style={styles.centerContainer}>
      <MaterialCommunityIcons name={icon} size={64} color={Colors.textMuted} />
      <Text style={styles.titleText}>{title}</Text>
      <Text style={styles.descText}>{description}</Text>
    </View>
  );
};

// ─── Error State ──────────────────────────────────────
interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  icon?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Connection Timeout',
  description = 'Internal database synchronization timed out. Check connection routing.',
  onRetry,
  icon = 'wifi-off',
}) => {
  return (
    <View style={styles.centerContainer}>
      <MaterialCommunityIcons name={icon} size={64} color={Colors.error} />
      <Text style={styles.titleText}>{title}</Text>
      <Text style={styles.descText}>{description}</Text>
      {onRetry && (
        <PrimaryButton 
          title="Retry Connection" 
          onPress={onRetry} 
          style={styles.retryBtn}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
    backgroundColor: Colors.background,
  },
  messageText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: Spacing.md,
    fontWeight: 'bold',
  },
  titleText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: Spacing.lg,
    textAlign: 'center',
  },
  descText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
    textAlign: 'center',
    lineHeight: 18,
    maxWidth: 260,
  },
  retryBtn: {
    marginTop: Spacing.xl,
    minWidth: 150,
  },
});
