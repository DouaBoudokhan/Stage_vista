// Global Application Settings Context
import React, { createContext, useContext, useState, useEffect } from 'react';
import { storage } from '../services/storage';
import { STORAGE_KEYS } from '../constants/config';

interface AppContextType {
  darkMode: boolean;
  setDarkMode: (value: boolean) => Promise<void>;
  language: string;
  setLanguage: (lang: string) => Promise<void>;
  simulatedError: string | null;
  setSimulatedError: (error: string | null) => void;
  isOnline: boolean;
  setIsOnline: (online: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [darkMode, setDarkModeState] = useState(false);
  const [language, setLanguageState] = useState('English');
  const [simulatedError, setSimulatedError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const mode = await storage.get(STORAGE_KEYS.DARK_MODE);
      const lang = await storage.get(STORAGE_KEYS.LANGUAGE);
      
      if (mode !== null) setDarkModeState(mode === 'true');
      if (lang !== null) setLanguageState(lang);
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
  };

  const setDarkMode = async (value: boolean) => {
    setDarkModeState(value);
    await storage.set(STORAGE_KEYS.DARK_MODE, value ? 'true' : 'false');
  };

  const setLanguage = async (lang: string) => {
    setLanguageState(lang);
    await storage.set(STORAGE_KEYS.LANGUAGE, lang);
  };

  return (
    <AppContext.Provider
      value={{
        darkMode,
        setDarkMode,
        language,
        setLanguage,
        simulatedError,
        setSimulatedError,
        isOnline,
        setIsOnline,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
