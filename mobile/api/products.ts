// Products API
import api from './axios';
import type { Product } from '../types';

export const productsApi = {
  getAll: async (): Promise<Product[]> => {
    const { data } = await api.get<Product[]>('/products');
    return data;
  },

  getById: async (id: string): Promise<Product> => {
    const { data } = await api.get<Product>(`/products/${id}`);
    return data;
  },

  create: async (product: Partial<Product>): Promise<Product> => {
    const { data } = await api.post<Product>('/products', product);
    return data;
  },

  update: async (id: string, product: Partial<Product>): Promise<Product> => {
    const { data } = await api.put<Product>(`/products/${id}`, product);
    return data;
  },

  remove: async (id: string): Promise<void> => {
    await api.delete(`/products/${id}`);
  },
};

// Stock operations
export const stockApi = {
  receiveStock: async (payload: {
    ref: string;
    quantity: number;
    poId?: string;
    technician: string;
    category?: string;
    brand?: string;
    productName?: string;
    articleNumber?: string;
    serialNumbers?: string[];
  }) => {
    const { data } = await api.post('/stock/in', payload);
    return data;
  },

  assignStock: async (payload: {
    productId: string;
    quantity: number;
    ticketId: string;
    technician: string;
  }) => {
    const { data } = await api.post('/stock/out', payload);
    return data;
  },
};
