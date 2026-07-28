// Application-wide configuration constants
import Constants from 'expo-constants';

// Read API base URL from environment variables (set in app.json or .env)
const extra = Constants.expirationDate ? {} : (Constants as any).expoConfig?.extra ?? {};

export const API_BASE_URL: string =
  extra.apiUrl ?? process.env.EXPO_PUBLIC_API_URL ?? 'http://172.18.221.31:8000';

export const CONFIG = {
  API_BASE_URL,
};

export const APP_NAME = 'StockIT';
export const APP_VERSION = '1.0.0';
export const APP_TAGLINE = 'AI-Powered Inventory Ops';
export const COMPANY_NAME = 'VistaServices Solutions';

// Storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'stockit_access_token',
  REFRESH_TOKEN: 'stockit_refresh_token',
  USER_DATA: 'stockit_user_data',
  DARK_MODE: 'stockit_dark_mode',
  LANGUAGE: 'stockit_language',
  ONBOARDED: 'stockit_onboarded',
} as const;

// Emoji icons used as product images in seed data
export const PRODUCT_ICONS: Record<string, string> = {
  Laptop: '💻',
  Monitor: '🖥️',
  Mouse: '🖱️',
  Headset: '🎧',
  Networking: '🔌',
  Default: '📦',
};

// Priority colors
export const PRIORITY_COLORS: Record<string, string> = {
  Critical: '#EF4444',
  High: '#F97316',
  Medium: '#F59E0B',
  Low: '#6B7280',
};
