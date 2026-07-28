import React, { useState } from 'react';
import { StyleSheet, View, Image, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Text, TextInput, HelperText, useTheme } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { useForm, Controller } from 'react-hook-form';
import { Colors, Spacing } from '../constants/theme';
import { PrimaryButton, SecondaryButton } from '../components/AppButtons';
import type { LoginRequest } from '../types';

export default function LoginScreen() {
  const { login } = useAuth();
  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { control, handleSubmit, formState: { errors } } = useForm<LoginRequest>({
    defaultValues: {
      email: 'it-admin@vistaservices.io',
      password: '',
    }
  });

  const onSubmit = async (data: LoginRequest) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      await login(data);
    } catch (err: any) {
      console.error(err);
      setErrorMessage(err.response?.data?.detail ?? 'Invalid company email or authorization credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      await login({
        email: 'it-admin@vistaservices.io',
        password: 'password123', // Mock secret validation
      });
    } catch (err: any) {
      setErrorMessage('Biometrics verification failed or credentials mismatch.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        <View style={styles.brandingSection}>
          <View style={styles.logoSquare}>
            <Text style={styles.logoSquareText}>S</Text>
          </View>
          <Text style={styles.welcomeText}>Welcome to StockIT</Text>
          <Text style={styles.subWelcomeText}>Enterprise IT Inventory Hub</Text>
        </View>

        <View style={styles.formSection}>
          {errorMessage && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Company Email</Text>
            <Controller
              control={control}
              name="email"
              rules={{ 
                required: 'Company email is required',
                pattern: {
                  value: /^\S+@\S+$/i,
                  message: 'Must enter a valid email address'
                }
              }}
              render={({ field: { onChange, onBlur, value } }) => (
                <TextInput
                  mode="outlined"
                  placeholder="name@company.com"
                  onBlur={onBlur}
                  onChangeText={onChange}
                  value={value}
                  error={!!errors.email}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  left={<TextInput.Icon icon="email-outline" color={Colors.textSecondary} />}
                  outlineStyle={styles.textInputOutline}
                />
              )}
            />
            {errors.email && (
              <HelperText type="error" visible={true}>
                {errors.email.message}
              </HelperText>
            )}
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Authorization Password</Text>
            <Controller
              control={control}
              name="password"
              rules={{ required: 'Authorization password is required' }}
              render={({ field: { onChange, onBlur, value } }) => (
                <TextInput
                  mode="outlined"
                  placeholder="••••••••"
                  secureTextEntry
                  onBlur={onBlur}
                  onChangeText={onChange}
                  value={value}
                  error={!!errors.password}
                  autoCapitalize="none"
                  left={<TextInput.Icon icon="lock-outline" color={Colors.textSecondary} />}
                  outlineStyle={styles.textInputOutline}
                />
              )}
            />
            {errors.password && (
              <HelperText type="error" visible={true}>
                {errors.password.message}
              </HelperText>
            )}
          </View>

          <PrimaryButton 
            title="Log In" 
            onPress={handleSubmit(onSubmit)} 
            loading={loading}
            disabled={loading}
          />

          <SecondaryButton 
            title="Authorize with Biometrics" 
            onPress={handleBiometricLogin} 
            icon="fingerprint"
            disabled={loading}
          />
        </View>

        <View style={styles.footerSection}>
          <Text style={styles.footerText}>VistaServices Solutions © 2026</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'space-between',
    padding: Spacing.xl,
  },
  brandingSection: {
    alignItems: 'center',
    marginTop: 40,
  },
  logoSquare: {
    width: 60,
    height: 60,
    backgroundColor: Colors.primary,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  logoSquareText: {
    color: '#FFF',
    fontSize: 32,
    fontWeight: '900',
  },
  welcomeText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.text,
    marginTop: Spacing.md,
  },
  subWelcomeText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  formSection: {
    marginVertical: 30,
  },
  errorContainer: {
    backgroundColor: Colors.errorLight,
    borderColor: Colors.error + '4D',
    borderWidth: 1,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
  },
  errorText: {
    color: Colors.error,
    fontSize: 11,
    fontWeight: 'bold',
  },
  inputContainer: {
    marginBottom: Spacing.md,
  },
  inputLabel: {
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
    letterSpacing: 0.5,
  },
  textInputOutline: {
    borderRadius: 12,
    borderColor: Colors.border,
  },
  footerSection: {
    alignItems: 'center',
    marginBottom: 10,
  },
  footerText: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
});
