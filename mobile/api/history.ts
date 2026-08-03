// History API — stock_entries (IN) + stock_exits (OUT) audit timeline
import api from './axios';

export interface StockHistoryRecord {
  id: string;
  sourceTable: 'stock_entries' | 'stock_exits';
  sourceId: number;
  action: 'IN' | 'OUT';
  inventoryId?: number;
  productName?: string;
  articleNumber?: string;
  category?: string;
  quantity: number;
  technician: string;
  timestamp: string;
  poNumber?: string;
  ticketId?: string;
  reference?: string;
  notes?: string;
}

export interface HistoryMovement {
  id: string;
  productId: string;
  productName: string;
  type: 'Receive' | 'Assign' | 'Adjustment';
  quantity: number;
  date: string;
  technician: string;
  comment: string;
  ticketId?: string;
  poId?: string;
  sourceTable?: string;
  category?: string;
}

interface StockHistoryResponse {
  id: string;
  source_table: string;
  source_id: number;
  action: string;
  inventory_id?: number;
  product_name?: string;
  article_number?: string;
  category?: string;
  quantity: number;
  technician: string;
  timestamp: string;
  po_number?: string;
  ticket_id?: string;
  reference?: string;
  notes?: string;
}

function mapHistoryRecord(row: StockHistoryResponse): StockHistoryRecord {
  return {
    id: row.id,
    sourceTable: row.source_table as StockHistoryRecord['sourceTable'],
    sourceId: row.source_id,
    action: row.action as StockHistoryRecord['action'],
    inventoryId: row.inventory_id,
    productName: row.product_name,
    articleNumber: row.article_number,
    category: row.category,
    quantity: row.quantity,
    technician: row.technician,
    timestamp: row.timestamp,
    poNumber: row.po_number,
    ticketId: row.ticket_id,
    reference: row.reference,
    notes: row.notes,
  };
}

export function toHistoryMovement(row: StockHistoryRecord): HistoryMovement {
  const parts: string[] = [];
  if (row.poNumber) parts.push(`PO: ${row.poNumber}`);
  if (row.ticketId) parts.push(`Ticket: ${row.ticketId}`);
  if (row.notes) parts.push(row.notes);
  if (row.sourceTable) parts.push(`via ${row.sourceTable}`);

  return {
    id: row.id,
    productId: row.articleNumber ?? String(row.inventoryId ?? row.id),
    productName: row.productName ?? row.articleNumber ?? 'Unknown product',
    type: row.action === 'IN' ? 'Receive' : row.action === 'OUT' ? 'Assign' : 'Adjustment',
    quantity: row.quantity,
    date: row.timestamp,
    technician: row.technician,
    comment: parts.join(' • ') || row.reference || '',
    ticketId: row.ticketId,
    poId: row.poNumber,
    sourceTable: row.sourceTable,
    category: row.category,
  };
}

export const historyApi = {
  getAll: async (params?: { action?: 'IN' | 'OUT'; limit?: number }): Promise<HistoryMovement[]> => {
    const { data } = await api.get<StockHistoryResponse[]>('/history', { params });
    return data.map(mapHistoryRecord).map(toHistoryMovement);
  },

  getRaw: async (params?: { action?: 'IN' | 'OUT'; limit?: number }): Promise<StockHistoryRecord[]> => {
    const { data } = await api.get<StockHistoryResponse[]>('/history', { params });
    return data.map(mapHistoryRecord);
  },
};
