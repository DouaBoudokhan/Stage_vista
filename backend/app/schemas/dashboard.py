"""Dashboard KPI schemas"""
from pydantic import BaseModel
from typing import Dict, List, Optional


class LowStockAlert(BaseModel):
    """Dynamically generated low-stock alert from live inventory data."""

    alert_type: str  # product_type | inventory_item
    product_type: str
    product_name: Optional[str] = None
    article_number: Optional[str] = None
    inventory_id: Optional[int] = None
    current_quantity: int
    threshold: int
    severity: str  # warning | critical


class CategoryStock(BaseModel):
    """Stock levels grouped by product type."""

    product_type: str
    stock_on_hand: int
    inventory_records: int
    share_percent: float


class DashboardKPIs(BaseModel):
    """Aggregated dashboard metrics calculated from the database."""

    total_inventory_quantity: int
    total_inventory_records: int
    total_product_types: int
    active_product_types: int
    open_tickets: int
    total_tickets: int
    ticket_fulfillment_rate: float
    movements_this_week: int
    stock_in_this_week: int
    stock_out_this_week: int
    total_purchase_orders: int
    low_stock_alert_count: int
    low_stock_alerts: List[LowStockAlert]
    category_stock: List[CategoryStock]
    status_distribution: Dict[str, int]
