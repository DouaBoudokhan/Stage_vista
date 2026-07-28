// History API
import api from './axios';
import type { HistoryMovement } from '../types';

export const historyApi = {
  getAll: async (): Promise<HistoryMovement[]> => {
    const { data } = await api.get<HistoryMovement[]>('/history');
    return data;
  },
};
