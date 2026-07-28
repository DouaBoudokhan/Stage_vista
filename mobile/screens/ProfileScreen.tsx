import React from 'react';
import { StyleSheet, View, ScrollView, TouchableOpacity } from 'react-native';
import { Text, Avatar, Surface, IconButton, Divider, useTheme } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { useApp } from '../contexts/AppContext';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import { PrimaryButton } from '../components/AppButtons';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

export default function ProfileScreen({ navigation }: any) {
  const { user, logout } = useAuth();
  const { simulatedError, setSimulatedError } = useApp();
  const theme = useTheme();

  const exceptionsList = [
    { key: 'no_internet', label: '🌐 No Internet Connection', icon: 'wifi-off', desc: 'Simulate connection offline' },
    { key: 'camera_denied', label: '📷 Camera Permission Denied', icon: 'camera-off', desc: 'Simulate system permission block' },
    { key: 'product_not_found', label: '🔍 Product Reference Not Found', icon: 'magnify', desc: 'Simulate SKU scan miss' },
    { key: 'invoice_mismatch', label: '⚠️ Invoice Mismatch Alert', icon: 'alert-triangle', desc: 'Simulate PO mismatch' },
    { key: 'low_stock', label: '📉 Critical Low Stock Threshold', icon: 'trending-down', desc: 'Simulate stock outage alert' },
    { key: 'ticket_not_found', label: '🎫 Ticket ID Not Found', icon: 'close-circle-outline', desc: 'Simulate invalid Jira request' },
    { key: 'server_error', label: '💥 Internal Server Error (500)', icon: 'alert-circle', desc: 'Simulate database timeout' },
    { key: 'maintenance', label: '⚙️ System Under Maintenance', icon: 'cog-outline', desc: 'Simulate upgrade telemetry' },
  ];

  // Intercept and show custom exception screen directly inside profile screen
  if (simulatedError) {
    let errorDetails: {
      title: string;
      desc: string;
      icon: string;
      color: string;
    } = {
      title: 'Exception State Active',
      desc: 'Simulated exception triggers.',
      icon: 'alert-circle',
      color: Colors.error
    };

    if (simulatedError === 'no_internet') {
      errorDetails = {
        title: 'No Internet Connection',
        desc: 'Offline cache loaded. StockIT runs server proxy matching via Wi-Fi. Please check company router assignments.',
        icon: 'wifi-off',
        color: Colors.error
      };
    } else if (simulatedError === 'camera_denied') {
      errorDetails = {
        title: 'Camera Permission Blocked',
        desc: 'Go to Settings > Apps > StockIT > Allow camera capabilities for label detection.',
        icon: 'camera-off',
        color: Colors.error
      };
    } else if (simulatedError === 'product_not_found') {
      errorDetails = {
        title: 'SKU Unregistered',
        desc: 'The scanned reference code was not located in VistaServices catalog hierarchy. Assign custom category.',
        icon: 'magnify',
        color: Colors.warning
      };
    } else if (simulatedError === 'invoice_mismatch') {
      errorDetails = {
        title: 'Invoice Mismatch (Critical)',
        desc: 'The supplier quantities scanned on the commercial receipt do not match line items listed in PO-2026-0042.',
        icon: 'alert-triangle',
        color: Colors.error
      };
    } else if (simulatedError === 'low_stock') {
      errorDetails = {
        title: 'Stock Critical Outage',
        desc: 'Available counts for HP Monitor screens are below safe levels (2 remaining). Order suggestion placed.',
        icon: 'trending-down',
        color: Colors.warning
      };
    } else if (simulatedError === 'ticket_not_found') {
      errorDetails = {
        title: 'Ticket ID Not Found',
        desc: 'The manually typed or scanned ticket identifier does not correspond to an active, approved Jira request.',
        icon: 'close-circle-outline',
        color: Colors.error
      };
    } else if (simulatedError === 'server_error') {
      errorDetails = {
        title: 'Internal Server Error (500)',
        desc: 'Database synchronization timed out. Retrying pipeline connection on behalf of administrator.',
        icon: 'alert-circle',
        color: Colors.error
      };
    } else if (simulatedError === 'maintenance') {
      errorDetails = {
        title: 'System Telemetry Maintenance',
        desc: 'StockIT servers are undergoing scheduled v3.5 telemetry updates. Operations resume shortly.',
        icon: 'cog-outline',
        color: Colors.primaryLight
      };
    }

    return (
      <View style={styles.errorFullStage}>
        <View style={[styles.errorIconBox, { backgroundColor: errorDetails.color + '1A', borderColor: errorDetails.color + '33' }]}>
          <MaterialCommunityIcons name={errorDetails.icon} size={48} color={errorDetails.color} />
        </View>
        <Text style={styles.errorFullTitle}>{errorDetails.title}</Text>
        <Text style={styles.errorFullDesc}>{errorDetails.desc}</Text>
        
        <PrimaryButton 
          title="Clear Simulation" 
          onPress={() => setSimulatedError(null)} 
          style={styles.clearSimBtn}
        />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      {/* Profile Info Header */}
      <Surface style={styles.profileCard} elevation={1}>
        <View style={styles.profileRow}>
          <Avatar.Text 
            size={64} 
            label={user?.name ? user.name.split(' ').map(n => n[0]).join('') : 'MA'} 
            style={{ backgroundColor: theme.colors.primary }}
          />
          <View style={styles.profileInfo}>
            <Text style={styles.nameText}>{user?.name ?? 'Mariem Alawi'}</Text>
            <Text style={styles.emailText}>{user?.email ?? 'it-admin@vistaservices.io'}</Text>
            <View style={styles.roleBadge}>
              <Text style={styles.roleText}>{user?.role ?? 'IT Ops Coordinator'}</Text>
            </View>
          </View>
        </View>
      </Surface>

      {/* Simulator Section */}
      <Text style={styles.sectionHeader}>Telemetry State Simulator</Text>
      <Text style={styles.sectionSub}>Test responsive error components and exception screens:</Text>
      
      <View style={styles.exceptionGrid}>
        {exceptionsList.map((exc) => (
          <TouchableOpacity
            key={exc.key}
            style={styles.exceptionRow}
            onPress={() => setSimulatedError(exc.key)}
          >
            <MaterialCommunityIcons name={exc.icon} size={22} color={Colors.primaryLight} style={styles.rowIcon} />
            <View style={{ flex: 1 }}>
              <Text style={styles.rowTitle}>{exc.label}</Text>
              <Text style={styles.rowSub}>{exc.desc}</Text>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={18} color={Colors.textMuted} />
          </TouchableOpacity>
        ))}
      </View>

      {/* Action Panel */}
      <View style={styles.actionPanel}>
        <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
          <MaterialCommunityIcons name="logout" size={20} color={Colors.error} />
          <Text style={styles.logoutBtnText}>Logout Session</Text>
        </TouchableOpacity>
      </View>
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
    paddingBottom: 40,
  },
  profileCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileInfo: {
    marginLeft: Spacing.md,
    flex: 1,
  },
  nameText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.text,
  },
  emailText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  roleBadge: {
    backgroundColor: Colors.primary + '1A',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  roleText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginTop: Spacing.lg,
    letterSpacing: 0.5,
  },
  sectionSub: {
    fontSize: 10,
    color: Colors.textMuted,
    marginBottom: Spacing.md,
    marginTop: 2,
  },
  exceptionGrid: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
  },
  exceptionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  rowIcon: {
    marginRight: Spacing.md,
  },
  rowTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: Colors.text,
  },
  rowSub: {
    fontSize: 9,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  actionPanel: {
    marginTop: Spacing.xl,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
    backgroundColor: Colors.errorLight,
    borderWidth: 1,
    borderColor: Colors.error + '33',
    borderRadius: BorderRadius.md,
  },
  logoutBtnText: {
    color: Colors.error,
    fontSize: 13,
    fontWeight: 'bold',
    marginLeft: 6,
  },

  // Fullstage error overlays
  errorFullStage: {
    flex: 1,
    backgroundColor: '#0F172A',
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
  },
  errorIconBox: {
    width: 80,
    height: 80,
    borderRadius: 40,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  errorFullTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  errorFullDesc: {
    color: '#94A3B8',
    fontSize: 11,
    textAlign: 'center',
    marginTop: Spacing.md,
    lineHeight: 16,
    paddingHorizontal: Spacing.md,
  },
  clearSimBtn: {
    marginTop: 30,
    minWidth: 185,
  },
});
