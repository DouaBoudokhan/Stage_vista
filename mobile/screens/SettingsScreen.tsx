import React, { useState } from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Text, Switch, List, TextInput, Button, Surface, useTheme } from 'react-native-paper';
import { useApp } from '../contexts/AppContext';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { PrimaryButton } from '../components/AppButtons';
import { API_BASE_URL } from '../constants/config';
import { NotificationService } from '../services/notification';

export default function SettingsScreen() {
  const { darkMode, setDarkMode, language, setLanguage } = useApp();
  const theme = useTheme();
  const [baseUrlInput, setBaseUrlInput] = useState(API_BASE_URL);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  const handleSaveBaseUrl = () => {
    NotificationService.show('Configuration Updated', 'FastAPI target URL reconfigured: ' + baseUrlInput);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.sectionHeader}>System Preferences</Text>
      <Surface style={styles.card} elevation={1}>
        <List.Item
          title="Support Dark Mode"
          description="Switch system visual colors"
          left={(props) => <List.Icon {...props} icon="theme-light-dark" />}
          right={() => (
            <Switch
              value={darkMode}
              onValueChange={setDarkMode}
              color={theme.colors.primary}
            />
          )}
        />
        <List.Item
          title="Push Stock Notifications"
          description="Alert on low levels & PO checkins"
          left={(props) => <List.Icon {...props} icon="bell-outline" />}
          right={() => (
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              color={theme.colors.primary}
            />
          )}
        />
        <List.Item
          title="Language Settings"
          description={language}
          left={(props) => <List.Icon {...props} icon="translate" />}
          onPress={() => {
            const nextLang = language === 'English' ? 'Français' : 'English';
            setLanguage(nextLang);
          }}
        />
      </Surface>

      <Text style={styles.sectionHeader}>Developer Gateway Configuration</Text>
      <Surface style={styles.card} elevation={1}>
        <View style={styles.gatewaySection}>
          <Text style={styles.gatewayLabel}>FastAPI Telemetry Base URL</Text>
          <TextInput
            mode="outlined"
            placeholder="http://10.0.2.2:8000"
            value={baseUrlInput}
            onChangeText={setBaseUrlInput}
            style={styles.gatewayInput}
            outlineStyle={styles.textInputOutline}
          />
          <PrimaryButton title="Save Gateway URL" onPress={handleSaveBaseUrl} />
        </View>
      </Surface>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.lg,
  },
  sectionHeader: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    marginTop: Spacing.md,
    letterSpacing: 0.5,
  },
  card: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
    marginBottom: Spacing.md,
  },
  gatewaySection: {
    padding: Spacing.md,
  },
  gatewayLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: 'bold',
    marginBottom: Spacing.xs,
  },
  gatewayInput: {
    backgroundColor: '#FFF',
    marginBottom: Spacing.sm,
  },
  textInputOutline: {
    borderRadius: 12,
    borderColor: Colors.border,
  },
});
