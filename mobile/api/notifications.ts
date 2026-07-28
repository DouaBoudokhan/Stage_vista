// Notifications API
import api from './axios';
import type { Notification } from '../types';

export const notificationsApi = {
  getAll: async (): Promise<Notification[]> => {
    const { data } = await api.get<Notification[]>('/notifications');
    return data;
  },
};
