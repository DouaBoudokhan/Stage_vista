// Root Component Entry Point
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PaperProvider } from 'react-native-paper';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Contexts & Theme
import { AuthProvider } from './contexts/AuthContext';
import { AppProvider, useApp } from './contexts/AppContext';
import { LightTheme, DarkTheme } from './constants/theme';
import Navigation from './navigation';

// Initialize React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

function MainAppContent() {
  const { darkMode } = useApp();
  const activeTheme = darkMode ? DarkTheme : LightTheme;

  return (
    <PaperProvider theme={activeTheme}>
      <NavigationContainer theme={activeTheme as any}>
        <StatusBar style={darkMode ? 'light' : 'dark'} />
        <Navigation />
      </NavigationContainer>
    </PaperProvider>
  );
}

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <AppProvider>
            <AuthProvider>
              <MainAppContent />
            </AuthProvider>
          </AppProvider>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
