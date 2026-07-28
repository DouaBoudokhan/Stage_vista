// Purchase Orders API
import api from './axios';
import type { PurchaseOrder } from '../types';

export const purchaseOrdersApi = {
  getAll: async (): Promise<PurchaseOrder[]> => {
    const { data } = await api.get<PurchaseOrder[]>('/api/v1/documents/purchase-orders');
    return data;
  },
};
