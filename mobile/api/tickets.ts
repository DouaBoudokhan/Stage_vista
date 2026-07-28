// Tickets API
import api from './axios';
import type { Ticket } from '../types';

export const ticketsApi = {
  getAll: async (): Promise<Ticket[]> => {
    const { data } = await api.get<Ticket[]>('/tickets');
    return data;
  },

  getById: async (id: string): Promise<Ticket> => {
    const { data } = await api.get<Ticket>(`/tickets/${id}`);
    return data;
  },
};
