import React from 'react';
import { StyleSheet, View } from 'react-native';
import HistoryScreen from './HistoryScreen';

export default function AuditScreen(props: any) {
  // Reuse history log screen logic since they both trace the audit logs
  return <HistoryScreen {...props} />;
}
