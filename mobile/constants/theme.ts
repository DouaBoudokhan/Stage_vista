// Theme constants for StockIT mobile application
import { MD3DarkTheme, MD3LightTheme } from 'react-native-paper';

export const Colors = {
  primary: '#0F3D91',
  primaryLight: '#2563EB',
  secondary: '#6366F1',
  background: '#F8FAFC',
  backgroundDark: '#0F172A',
  surface: '#FFFFFF',
  surfaceDark: '#1E293B',
  card: '#FFFFFF',
  cardDark: '#1E293B',
  text: '#0F172A',
  textDark: '#F1F5F9',
  textSecondary: '#64748B',
  textMuted: '#94A3B8',
  border: '#E2E8F0',
  borderDark: '#334155',
  success: '#10B981',
  successLight: '#ECFDF5',
  warning: '#F59E0B',
  warningLight: '#FFFBEB',
  error: '#EF4444',
  errorLight: '#FEF2F2',
  info: '#3B82F6',
  infoLight: '#EFF6FF',
  accent: '#8B5CF6',
} as const;

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
} as const;

export const BorderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  full: 9999,
} as const;

export const FontSize = {
  xs: 10,
  sm: 12,
  md: 14,
  lg: 16,
  xl: 18,
  xxl: 22,
  xxxl: 28,
} as const;

export const LightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: Colors.primary,
    secondary: Colors.secondary,
    background: Colors.background,
    surface: Colors.surface,
    error: Colors.error,
    onPrimary: '#FFFFFF',
    onBackground: Colors.text,
    onSurface: Colors.text,
    outline: Colors.border,
  },
};

export const DarkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: Colors.primaryLight,
    secondary: Colors.secondary,
    background: Colors.backgroundDark,
    surface: Colors.surfaceDark,
    error: Colors.error,
    onPrimary: '#FFFFFF',
    onBackground: Colors.textDark,
    onSurface: Colors.textDark,
    outline: Colors.borderDark,
  },
};
