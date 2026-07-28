// React Query hooks for all API interactions
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productsApi, stockApi } from '../api/products';
import { ticketsApi } from '../api/tickets';
import { historyApi } from '../api/history';
import { notificationsApi } from '../api/notifications';
import { purchaseOrdersApi } from '../api/purchaseOrders';
import { suppliersApi } from '../api/suppliers';
import { aiApi } from '../api/ai';

// ─── Products ─────────────────────────────────────────
export function useProducts() {
  return useQuery({
    queryKey: ['products'],
    queryFn: productsApi.getAll,
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: ['products', id],
    queryFn: () => productsApi.getById(id),
    enabled: !!id,
  });
}

// ─── Tickets ──────────────────────────────────────────
export function useTickets() {
  return useQuery({
    queryKey: ['tickets'],
    queryFn: ticketsApi.getAll,
  });
}

export function useTicket(id: string) {
  return useQuery({
    queryKey: ['tickets', id],
    queryFn: () => ticketsApi.getById(id),
    enabled: !!id,
  });
}

// ─── History ──────────────────────────────────────────
export function useHistory() {
  return useQuery({
    queryKey: ['history'],
    queryFn: historyApi.getAll,
  });
}

// ─── Notifications ────────────────────────────────────
export function useNotifications() {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: notificationsApi.getAll,
  });
}

// ─── Purchase Orders ──────────────────────────────────
export function usePurchaseOrders() {
  return useQuery({
    queryKey: ['purchaseOrders'],
    queryFn: purchaseOrdersApi.getAll,
  });
}

// ─── Suppliers ────────────────────────────────────────
export function useSuppliers() {
  return useQuery({
    queryKey: ['suppliers'],
    queryFn: suppliersApi.getAll,
  });
}

// ─── Mutations ────────────────────────────────────────
export function useReceiveStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: stockApi.receiveStock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['history'] });
      queryClient.invalidateQueries({ queryKey: ['purchaseOrders'] });
    },
  });
}

export function useAssignStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: stockApi.assignStock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['history'] });
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
    },
  });
}

// ─── AI ───────────────────────────────────────────────
export function useDetectProduct() {
  return useMutation({
    mutationFn: aiApi.detectProduct,
  });
}

export function useOcrInvoice() {
  return useMutation({
    mutationFn: aiApi.ocrInvoice,
  });
}

export function useRecommendTicket() {
  return useMutation({
    mutationFn: aiApi.recommendTicket,
  });
}
