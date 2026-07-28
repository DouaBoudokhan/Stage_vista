import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Text, Surface } from 'react-native-paper';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { APP_NAME, APP_VERSION, COMPANY_NAME, APP_TAGLINE } from '../constants/config';

export default function AboutScreen() {
  return (
    <View style={styles.container}>
      <Surface style={styles.card} elevation={1}>
        <View style={styles.logoSquare}>
          <Text style={styles.logoSquareText}>SI</Text>
        </View>
        <Text style={styles.title}>{APP_NAME}</Text>
        <Text style={styles.tagline}>{APP_TAGLINE}</Text>
        <Text style={styles.version}>Version: {APP_VERSION}</Text>
        
        <Text style={styles.desc}>
          StockIT is an enterprise mobile application designed for real-time inventory management operations. It integrates with FastAPI backend systems for barcode recognition, PO matching, and smart ticket recommendations.
        </Text>
        
        <Text style={styles.company}>{COMPANY_NAME} © 2026</Text>
      </Surface>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
  },
  card: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.xl,
    alignItems: 'center',
    width: '100%',
  },
  logoSquare: {
    width: 60,
    height: 60,
    backgroundColor: Colors.primary,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  logoSquareText: {
    color: '#FFF',
    fontSize: 28,
    fontWeight: '900',
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.text,
  },
  tagline: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    marginTop: 4,
  },
  version: {
    fontSize: 10,
    color: Colors.textMuted,
    marginTop: 6,
  },
  desc: {
    fontSize: 11,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: Spacing.lg,
    lineHeight: 16,
  },
  company: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: Colors.textMuted,
    marginTop: Spacing.xl,
  },
});
