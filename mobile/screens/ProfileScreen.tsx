import React, { useState } from 'react';
import { StyleSheet, View, ScrollView, TouchableOpacity, Alert, Switch } from 'react-native';
import { Text, Avatar, Surface, Divider, useTheme } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

export default function ProfileScreen({ navigation }: any) {
  const { user, logout } = useAuth();
  const theme = useTheme();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Logout', 
          style: 'destructive',
          onPress: logout 
        },
      ]
    );
  };

  const handleSettingToggle = (setting: string, value: boolean) => {
    if (setting === 'notifications') {
      setNotificationsEnabled(value);
      Alert.alert('Notifications', value ? 'Notifications enabled' : 'Notifications disabled');
    } else if (setting === 'darkMode') {
      setDarkModeEnabled(value);
      Alert.alert('Dark Mode', value ? 'Dark mode enabled' : 'Dark mode disabled');
    }
  };

  const menuItems = [
    {
      section: 'Quick Actions',
      items: [
        { icon: 'package-variant', label: 'Inventory Overview', onPress: () => navigation.navigate('Inventory') },
        { icon: 'history', label: 'Movement History', onPress: () => navigation.navigate('History') },
      ]
    },
    {
      section: 'Settings',
      items: [
        { icon: 'bell-outline', label: 'Push Notifications', toggle: true, value: notificationsEnabled, onToggle: (v: boolean) => handleSettingToggle('notifications', v) },
        { icon: 'weather-night', label: 'Dark Mode', toggle: true, value: darkModeEnabled, onToggle: (v: boolean) => handleSettingToggle('darkMode', v) },
        { icon: 'cog-outline', label: 'App Settings', onPress: () => navigation.navigate('Settings') },
      ]
    },
    {
      section: 'Information',
      items: [
        { icon: 'information-outline', label: 'About StockIT', onPress: () => navigation.navigate('About') },
        { icon: 'file-document-outline', label: 'Documentation', onPress: () => Alert.alert('Documentation', 'User guide coming soon.') },
        { icon: 'shield-check-outline', label: 'Privacy Policy', onPress: () => Alert.alert('Privacy Policy', 'Your data is secure and encrypted.') },
      ]
    },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      {/* Profile Header */}
      <Surface style={styles.profileCard} elevation={2}>
        <View style={styles.profileHeader}>
          <Avatar.Text 
            size={72} 
            label={user?.name ? user.name.split(' ').map(n => n[0]).join('').toUpperCase() : user?.email ? user.email.substring(0, 2).toUpperCase() : 'DU'} 
            style={{ backgroundColor: theme.colors.primary }}
          />
          <View style={styles.profileInfo}>
            <Text style={styles.nameText}>{user?.name ?? user?.email?.split('@')[0] ?? 'User'}</Text>
            <Text style={styles.emailText}>{user?.email ?? 'user@stockit.local'}</Text>
            <View style={styles.roleBadge}>
              <Text style={styles.roleText}>{user?.role ?? 'Administrator'}</Text>
            </View>
          </View>
        </View>
      </Surface>

      {/* Menu Sections */}
      {menuItems.map((section, sectionIdx) => (
        <View key={sectionIdx}>
          <Text style={styles.sectionHeader}>{section.section}</Text>
          <Surface style={styles.menuCard} elevation={1}>
            {section.items.map((item, itemIdx) => (
              <View key={itemIdx}>
                <TouchableOpacity
                  style={styles.menuRow}
                  onPress={item.onPress}
                  disabled={item.toggle}
                >
                  <View style={styles.menuRowLeft}>
                    <View style={styles.menuIconBox}>
                      <MaterialCommunityIcons name={item.icon} size={22} color={Colors.primaryLight} />
                    </View>
                    <Text style={styles.menuLabel}>{item.label}</Text>
                  </View>
                  
                  {item.toggle ? (
                    <Switch
                      value={item.value}
                      onValueChange={item.onToggle}
                      trackColor={{ false: '#CBD5E1', true: Colors.primaryLight + '66' }}
                      thumbColor={item.value ? Colors.primaryLight : '#f4f4f4'}
                    />
                  ) : (
                    <MaterialCommunityIcons name="chevron-right" size={20} color={Colors.textMuted} />
                  )}
                </TouchableOpacity>
                {itemIdx < section.items.length - 1 && <Divider style={styles.menuDivider} />}
              </View>
            ))}
          </Surface>
        </View>
      ))}

      {/* Logout Button */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <MaterialCommunityIcons name="logout" size={20} color={Colors.error} />
        <Text style={styles.logoutBtnText}>Logout Session</Text>
      </TouchableOpacity>

      {/* App Version */}
      <Text style={styles.versionText}>StockIT v1.0.0 • Build 2026.02</Text>
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
    paddingBottom: 80,
  },
  profileCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.lg,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileInfo: {
    marginLeft: Spacing.md,
    flex: 1,
  },
  nameText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.text,
  },
  emailText: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  roleBadge: {
    backgroundColor: Colors.primary + '1A',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  roleText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    color: Colors.textSecondary,
    marginTop: Spacing.lg,
    marginBottom: Spacing.sm,
    letterSpacing: 0.5,
  },
  menuCard: {
    backgroundColor: '#FFF',
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
    marginBottom: Spacing.md,
  },
  menuRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.md,
  },
  menuRowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  menuRowRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuIconBox: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: Colors.primaryLight + '0A',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  menuLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
    flex: 1,
  },
  menuDivider: {
    marginLeft: 64,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 50,
    backgroundColor: Colors.errorLight,
    borderWidth: 1.5,
    borderColor: Colors.error + '33',
    borderRadius: BorderRadius.lg,
    marginTop: Spacing.lg,
  },
  logoutBtnText: {
    color: Colors.error,
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  versionText: {
    fontSize: 10,
    color: Colors.textMuted,
    textAlign: 'center',
    marginTop: Spacing.lg,
    marginBottom: Spacing.md,
  },
});
