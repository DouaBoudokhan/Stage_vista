// Types for the StockIT mobile application
// These mirror the FastAPI backend models

export interface Product {
  id: string;
  name: string;
  ref: string;
  brand: string;
  category: string;
  supplier: string;
  warehouse: string;
  shelf: string;
  quantity: number;
  reserved: number;
  status: 'In Stock' | 'Low Stock' | 'Out of Stock';
  image: string;
  price: number;
}

export interface PurchaseOrder {
  id: string;
  supplier: string;
  date: string;
  status: 'Pending' | 'Completed' | 'Partial';
  items: PurchaseOrderItem[];
  serialNumbers?: string[];
}

export interface PurchaseOrderItem {
  ref: string;
  name: string;
  brand: string;
  quantity: number;
  received: number;
  serialNumbers?: string[];
}

export interface Ticket {
  id: string;
  requester: string;
  department: string;
  requestedEquipment: string;
  brandPreference?: string;
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  status: 'Pending' | 'Approved' | 'Assigned';
  reason: string;
  date: string;
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
}

export interface ScanResult {
  mode: 'product' | 'invoice' | 'label';
  detectedObject?: string;
  brand?: string;
  reference?: string;
  category?: string;
  confidence: number;
  boundingBox?: { x: number; y: number; w: number; h: number };
  supplier?: string;
  invoiceNumber?: string;
  purchaseOrderSuggested?: string;
  detectedItems?: DetectedItem[];
  serialNumbers?: string[];
  productName?: string;
  articleNumber?: string;
  poNumber?: string;
  matchedPO?: string;
  isMatch?: boolean;
  quantity?: number;
}

export interface DetectedItem {
  name: string;
  ref: string;
  quantity: number;
  matched: boolean;
  serialNumbers?: string[];
}

export interface Notification {
  id: string;
  title: string;
  desc: string;
  time: string;
  unread: boolean;
}

export interface Supplier {
  id: string;
  name: string;
  contact: string;
  email: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface AIRecommendation {
  ticket: Ticket;
  confidence: number;
  reason: string;
}

export interface StockInRequest {
  ref: string;
  quantity: number;
  poId?: string;
  technician: string;
}

export interface StockOutRequest {
  productId: string;
  quantity: number;
  ticketId: string;
  technician: string;
}
