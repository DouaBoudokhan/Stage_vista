// Notification service for showing toast alerts and custom app notifications
import { Alert } from 'react-native';

export const NotificationService = {
  // Show standard local notification/toast alert
  show(title: string, message: string) {
    Alert.alert(title, message);
  },

  // Trigger push alert or channel alerts (mocked)
  async registerForPushNotificationsAsync(): Promise<string | null> {
    console.log('Registering for push notifications...');
    return 'mock_push_token_123456';
  },

  // Send system logs
  logActivity(activityName: string, detail: string) {
    console.log(`[Notification Service Log] Activity: ${activityName} - Detail: ${detail}`);
  }
};
