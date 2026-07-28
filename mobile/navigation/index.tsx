// Navigation setup using React Navigation
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useAuth } from '../contexts/AuthContext';
import { Colors } from '../constants/theme';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { StyleSheet, View } from 'react-native';
import { useTheme } from 'react-native-paper';

// Screens
import SplashScreen from '../screens/SplashScreen';
import LoginScreen from '../screens/LoginScreen';
import DashboardScreen from '../screens/DashboardScreen';
import InventoryScreen from '../screens/InventoryScreen';
import ProductDetailsScreen from '../screens/ProductDetailsScreen';
import WorkflowSelectionScreen from '../screens/WorkflowSelectionScreen';
import WorkflowReceiveScreen from '../screens/WorkflowReceiveScreen';
import WorkflowAssignScreen from '../screens/WorkflowAssignScreen';
import HistoryScreen from '../screens/HistoryScreen';
import NotificationsScreen from '../screens/NotificationsScreen';
import ProfileScreen from '../screens/ProfileScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ReportsScreen from '../screens/ReportsScreen';
import SuppliersScreen from '../screens/SuppliersScreen';
import PurchaseOrdersScreen from '../screens/PurchaseOrdersScreen';
import UsersScreen from '../screens/UsersScreen';
import AuditScreen from '../screens/AuditScreen';
import AboutScreen from '../screens/AboutScreen';

// Navigation Params Types
export type RootStackParamList = {
  Splash: undefined;
  Login: undefined;
  MainTabs: undefined;
  ProductDetails: { productId: string };
  WorkflowSelection: undefined;
  WorkflowReceive: undefined;
  WorkflowAssign: undefined;
  Suppliers: undefined;
  PurchaseOrders: undefined;
  Users: undefined;
  Audit: undefined;
  Reports: undefined;
  Settings: undefined;
  About: undefined;
};

export type BottomTabParamList = {
  Home: undefined;
  Inventory: undefined;
  WorkflowSelection: undefined;
  History: undefined;
  Profile: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<BottomTabParamList>();

// Bottom Tabs Navigator
function BottomTabNavigator() {
  const theme = useTheme();
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: true,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarStyle: {
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
          backgroundColor: theme.colors.surface,
          borderTopWidth: 1,
          borderTopColor: theme.colors.outline,
        },
        tabBarIcon: ({ color, size }) => {
          let iconName = 'home';
          if (route.name === 'Home') iconName = 'home-outline';
          else if (route.name === 'Inventory') iconName = 'package-variant-closed';
          else if (route.name === 'WorkflowSelection') iconName = 'camera-outline';
          else if (route.name === 'History') iconName = 'history';
          else if (route.name === 'Profile') iconName = 'account-outline';
          return <MaterialCommunityIcons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={DashboardScreen} options={{ title: 'StockIT' }} />
      <Tab.Screen name="Inventory" component={InventoryScreen} />
      <Tab.Screen 
        name="WorkflowSelection" 
        component={WorkflowSelectionScreen} 
        options={{
          tabBarLabel: 'Scan',
          title: 'Choose Workflow',
          tabBarIcon: ({ color }) => (
            <View style={styles.scanButtonContainer}>
              <MaterialCommunityIcons name="camera" size={28} color="#FFF" />
            </View>
          )
        }}
      />
      <Tab.Screen name="History" component={HistoryScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

// Root Navigation Entry Point
export default function Navigation() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isLoading ? (
        <Stack.Screen name="Splash" component={SplashScreen} />
      ) : !isAuthenticated ? (
        <Stack.Screen name="Login" component={LoginScreen} />
      ) : (
        <>
          <Stack.Screen name="MainTabs" component={BottomTabNavigator} />
          <Stack.Screen name="ProductDetails" component={ProductDetailsScreen} options={{ headerShown: true, title: 'Product Details' }} />
          <Stack.Screen name="WorkflowSelection" component={WorkflowSelectionScreen} options={{ headerShown: true, title: 'Choose Workflow' }} />
          <Stack.Screen name="WorkflowReceive" component={WorkflowReceiveScreen} options={{ headerShown: true, title: 'Receive Equipment' }} />
          <Stack.Screen name="WorkflowAssign" component={WorkflowAssignScreen} options={{ headerShown: true, title: 'Assign to Ticket' }} />
          <Stack.Screen name="Suppliers" component={SuppliersScreen} options={{ headerShown: true, title: 'Suppliers' }} />
          <Stack.Screen name="PurchaseOrders" component={PurchaseOrdersScreen} options={{ headerShown: true, title: 'Purchase Orders' }} />
          <Stack.Screen name="Users" component={UsersScreen} options={{ headerShown: true, title: 'Users' }} />
          <Stack.Screen name="Audit" component={AuditScreen} options={{ headerShown: true, title: 'Audit Log' }} />
          <Stack.Screen name="Reports" component={ReportsScreen} options={{ headerShown: true, title: 'Reports' }} />
          <Stack.Screen name="Settings" component={SettingsScreen} options={{ headerShown: true, title: 'Settings' }} />
          <Stack.Screen name="About" component={AboutScreen} options={{ headerShown: true, title: 'About' }} />
        </>
      )}
    </Stack.Navigator>
  );
}

const styles = StyleSheet.create({
  scanButtonContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 6,
    bottom: 2,
  },
});
