// Suppliers API
import api from './axios';
import type { Supplier } from '../types';

export const suppliersApi = {
  getAll: async (): Promise<Supplier[]> => {
    const { data } = await api.get<Supplier[]>('/suppliers');
    return data;
  },
};
