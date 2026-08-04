// Inventory API — reads from the inventory table (current on-hand stock)
import api from './axios';

export interface InventoryItem {
  id: number;
  productId: number;
  category?: string;
  articleNumber: string;
  serialNumber?: string;
  quantityAvailable: number;
  trackingType: 'SERIALIZED' | 'BULK';
  status: string;
  receivedBy: string;
  receivedAt?: string;
  purchaseOrderId?: number;
  poNumber?: string;
  // Optional denormalized fields (may be populated by higher-level API wrappers)
  productName?: string;
  brand?: string;
  image?: string;
}

interface InventoryItemResponse {
  id: number;
  product_id: number;
  category?: string;
  article_number: string;
  serial_number?: string;
  quantity_available: number;
  tracking_type: string;
  status: string;
  received_by: string;
  received_at?: string;
  purchase_order_id?: number;
  po_number?: string;
}

function mapInventoryItem(row: InventoryItemResponse): InventoryItem {
  return {
    id: row.id,
    productId: row.product_id,
    category: row.category,
    articleNumber: row.article_number,
    serialNumber: row.serial_number,
    quantityAvailable: row.quantity_available,
    trackingType: row.tracking_type as InventoryItem['trackingType'],
    status: row.status,
    receivedBy: row.received_by,
    receivedAt: row.received_at,
    purchaseOrderId: row.purchase_order_id,
    poNumber: row.po_number,
  };
}

export const inventoryApi = {
  getAll: async (params?: {
    category?: string;
    brand?: string;
    search?: string;
    limit?: number;
  }): Promise<InventoryItem[]> => {
    const { data } = await api.get<InventoryItemResponse[]>('/inventory', { params });
    return data.map(mapInventoryItem);
  },

  getById: async (id: number): Promise<InventoryItem> => {
    const { data } = await api.get<InventoryItemResponse>(`/inventory/${id}`);
    return mapInventoryItem(data);
  },
};
