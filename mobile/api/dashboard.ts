// Dashboard KPI API
import api from './axios';

export interface LowStockAlert {
  alertType: 'product_type' | 'inventory_item';
  productType: string;
  productName?: string;
  articleNumber?: string;
  inventoryId?: number;
  currentQuantity: number;
  threshold: number;
  severity: 'warning' | 'critical';
}

export interface CategoryStock {
  productType: string;
  stockOnHand: number;
  inventoryRecords: number;
  sharePercent: number;
}

export interface DashboardKPIs {
  totalInventoryQuantity: number;
  totalInventoryRecords: number;
  totalProductTypes: number;
  activeProductTypes: number;
  openTickets: number;
  totalTickets: number;
  ticketFulfillmentRate: number;
  movementsThisWeek: number;
  stockInThisWeek: number;
  stockOutThisWeek: number;
  totalPurchaseOrders: number;
  lowStockAlertCount: number;
  lowStockAlerts: LowStockAlert[];
  categoryStock: CategoryStock[];
  statusDistribution: Record<string, number>;
}

interface DashboardKPIsResponse {
  total_inventory_quantity: number;
  total_inventory_records: number;
  total_product_types: number;
  active_product_types: number;
  open_tickets: number;
  total_tickets: number;
  ticket_fulfillment_rate: number;
  movements_this_week: number;
  stock_in_this_week: number;
  stock_out_this_week: number;
  total_purchase_orders: number;
  low_stock_alert_count: number;
  low_stock_alerts: Array<{
    alert_type: string;
    product_type: string;
    product_name?: string;
    article_number?: string;
    inventory_id?: number;
    current_quantity: number;
    threshold: number;
    severity: string;
  }>;
  category_stock: Array<{
    product_type: string;
    stock_on_hand: number;
    inventory_records: number;
    share_percent: number;
  }>;
  status_distribution: Record<string, number>;
}

function mapDashboardKPIs(data: DashboardKPIsResponse): DashboardKPIs {
  return {
    totalInventoryQuantity: data.total_inventory_quantity,
    totalInventoryRecords: data.total_inventory_records,
    totalProductTypes: data.total_product_types,
    activeProductTypes: data.active_product_types,
    openTickets: data.open_tickets,
    totalTickets: data.total_tickets,
    ticketFulfillmentRate: data.ticket_fulfillment_rate,
    movementsThisWeek: data.movements_this_week,
    stockInThisWeek: data.stock_in_this_week,
    stockOutThisWeek: data.stock_out_this_week,
    totalPurchaseOrders: data.total_purchase_orders,
    lowStockAlertCount: data.low_stock_alert_count,
    lowStockAlerts: data.low_stock_alerts.map((a) => ({
      alertType: a.alert_type as LowStockAlert['alertType'],
      productType: a.product_type,
      productName: a.product_name,
      articleNumber: a.article_number,
      inventoryId: a.inventory_id,
      currentQuantity: a.current_quantity,
      threshold: a.threshold,
      severity: a.severity as LowStockAlert['severity'],
    })),
    categoryStock: data.category_stock.map((c) => ({
      productType: c.product_type,
      stockOnHand: c.stock_on_hand,
      inventoryRecords: c.inventory_records,
      sharePercent: c.share_percent,
    })),
    statusDistribution: data.status_distribution,
  };
}

export const dashboardApi = {
  getKPIs: async (): Promise<DashboardKPIs> => {
    const { data } = await api.get<DashboardKPIsResponse>('/dashboard/kpis');
    return mapDashboardKPIs(data);
  },
};
