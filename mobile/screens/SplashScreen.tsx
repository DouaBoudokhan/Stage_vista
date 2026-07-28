import React, { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import { Text, ActivityIndicator } from 'react-native-paper';
import { Colors } from '../constants/theme';
import { APP_NAME, APP_TAGLINE } from '../constants/config';

export default function SplashScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.logoBox}>
        <Text style={styles.logoLetters}>SI</Text>
      </View>
      <Text style={styles.title}>{APP_NAME}</Text>
      <Text style={styles.tagline}>{APP_TAGLINE}</Text>
      <ActivityIndicator size="small" color="#FFF" style={styles.loader} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoBox: {
    width: 90,
    height: 90,
    backgroundColor: '#FFF',
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 8,
  },
  logoLetters: {
    color: Colors.primary,
    fontSize: 42,
    fontWeight: '900',
    letterSpacing: -1,
  },
  title: {
    color: '#FFF',
    fontSize: 28,
    fontWeight: '900',
    marginTop: 20,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  tagline: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 10,
    fontWeight: 'bold',
    marginTop: 6,
    letterSpacing: 2,
    textTransform: 'uppercase',
    fontFamily: 'monospace',
  },
  loader: {
    marginTop: 40,
  },
});
