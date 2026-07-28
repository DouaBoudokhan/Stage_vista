import React from 'react';
import { StyleSheet } from 'react-native';
import { Button } from 'react-native-paper';
import { Colors } from '../constants/theme';

interface AppButtonProps {
  onPress: () => void;
  title: string;
  loading?: boolean;
  disabled?: boolean;
  icon?: string;
  mode?: 'text' | 'outlined' | 'contained';
  style?: any;
}

export const PrimaryButton: React.FC<AppButtonProps> = ({
  onPress,
  title,
  loading = false,
  disabled = false,
  icon,
  mode = 'contained',
  style,
}) => {
  return (
    <Button
      onPress={onPress}
      loading={loading}
      disabled={disabled}
      icon={icon}
      mode={mode}
      style={[styles.button, styles.primary, style]}
      labelStyle={styles.containedLabel}
      contentStyle={styles.content}
    >
      {title}
    </Button>
  );
};

export const SecondaryButton: React.FC<AppButtonProps> = ({
  onPress,
  title,
  loading = false,
  disabled = false,
  icon,
  style,
}) => {
  return (
    <Button
      onPress={onPress}
      loading={loading}
      disabled={disabled}
      icon={icon}
      mode="outlined"
      style={[styles.button, styles.secondary, style]}
      labelStyle={styles.secondaryLabel}
      contentStyle={styles.content}
    >
      {title}
    </Button>
  );
};

export const DangerButton: React.FC<AppButtonProps> = ({
  onPress,
  title,
  loading = false,
  disabled = false,
  icon,
  style,
}) => {
  return (
    <Button
      onPress={onPress}
      loading={loading}
      disabled={disabled}
      icon={icon}
      mode="contained"
      style={[styles.button, styles.danger, style]}
      labelStyle={styles.containedLabel}
      contentStyle={styles.content}
    >
      {title}
    </Button>
  );
};

const styles = StyleSheet.create({
  button: {
    marginVertical: 6,
    borderRadius: 12,
  },
  primary: {
    backgroundColor: Colors.primary,
  },
  secondary: {
    borderColor: Colors.border,
    borderWidth: 1,
  },
  danger: {
    backgroundColor: Colors.error,
  },
  content: {
    height: 48,
  },
  containedLabel: {
    color: '#FFF',
    fontSize: 13,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  secondaryLabel: {
    color: Colors.text,
    fontSize: 13,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
});
