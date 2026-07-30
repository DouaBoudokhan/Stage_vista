# StockIT - AI-Powered Inventory Management System

Inventory operations platform combining FastAPI (PostgreSQL/Supabase) backend with a React Native Expo mobile app. Features YOLO11 AI product detection, OCR-based invoice extraction, and two-step equipment workflows (Receive + Assign to Ticket).

---

## Project Structure

```
stockit/
├── backend/                          FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── main.py                   FastAPI app entry, CORS, router mounting
│   │   ├── config.py                 Pydantic Settings (.env loader)
│   │   ├── database.py               SQLAlchemy engine, Session, init_db() auto-migration
│   │   ├── dependencies.py           get_current_user (JWT) dependency
│   │   ├── models/                   ONLY the 6 required SQLAlchemy tables
│   │   │   ├── __init__.py           Public exports: User, Document, PurchaseOrder, Inventory, StockEntry, StockExit
│   │   │   ├── user.py               users table (auth)
│   │   │   ├── document.py           documents table (scanned invoices)
│   │   │   ├── purchase_order.py     purchase_orders table (PO cache + LLM descriptions)
│   │   │   ├── inventory.py          inventory + inventory_movements + tickets (3 tables)
│   │   │   ├── stock_entry.py        stock_entries table (IN audit)
│   │   │   └── stock_exit.py         stock_exits table (OUT audit)
│   │   ├── routers/                  API endpoints
│   │   │   ├── inventory.py          /stock/in, /stock/out, /history, /tickets, /dashboard/kpis, /inventory (mounted at both /api/v1 and /)
│   │   │   ├── products.py           /products/detect, /products/categories, /products/debug/model-status
│   │   │   ├── document_analysis.py  Invoice OCR + PO extraction pipeline
│   │   │   ├── labels.py             Shipping label scanning
│   │   │   ├── detection.py          (reserved) generic detection endpoints
│   │   │   ├── auth.py               (currently commented out in main.py)
│   │   │   └── stock_entry.py        (currently commented out in main.py)
│   │   ├── schemas/                  Pydantic request/response models
│   │   │   ├── dashboard.py          DashboardKPIs, LowStockAlert, CategoryStock schemas
│   │   ├── services/                 Business logic layer
│   │   │   ├── inventory_service.py  receive_stock, assign_stock, create_inventory_and_stock_entry, get_dashboard_kpis (Transactional)
│   │   │   ├── yolo_service.py       YOLO11 product detection wrapper
│   │   │   ├── ocr_service.py        pytesseract invoice OCR (requires Tesseract binary)
│   │   │   ├── ocr_parser_service.py OCR text -> structured PO line items
│   │   │   ├── azure_ocr_service.py  Azure Computer Vision fallback OCR
│   │   │   ├── llm_service.py        Llama 3.3 / Azure AI Foundry description generator
│   │   │   ├── document_service.py   Document + PO persistence
│   │   │   ├── po_service.py         Purchase order helpers
│   │   │   ├── storage_service.py    Uploaded file management
│   │   │   └── workflow_manager.py   Workflow state orchestration
│   │   └── utils/
│   │       └── security.py           JWT encode/decode, password hashing
│   ├── models_ai/                    YOLO weights (best.pt) - gitkeep placeholder
│   ├── uploads/                      Uploaded images - gitkeep placeholder
│   ├── requirements.txt              Full Python dependencies
│   ├── requirements-minimal.txt      Slim dependency set
│   ├── .env.example                  Environment template
│   ├── start.bat / start.sh          Convenience launchers
│   ├── check_db.py / debug_db.py     Database diagnostics
│   ├── test_*.py                     E2E & unit test scripts (workflow, label, invoice, LLM, etc.)
│   ├── INVOICE_ANALYSIS_WORKFLOW.md  Deep-dive doc on the OCR pipeline
│   ├── STOCK_ENTRY_WORKFLOW.md       Deep-dive doc on the Receive workflow
│   ├── PROJECT_SUMMARY.md            Original project brief
│   ├── SETUP.md                      Backend setup instructions
│   └── SUPABASE_SETUP.md             Supabase provisioning guide
└── mobile/                           React Native Expo app (Expo SDK 54)
    ├── App.tsx                       Root component (QueryClient + PaperProvider + Navigation)
    ├── index.ts                      Expo entry point
    ├── app.json                      Expo manifest (extra.apiUrl config)
    ├── package.json                  Dependencies (React 19, RN 0.81, React Navigation 7, RQ 5, RN Paper 5)
    ├── tsconfig.json
    ├── api/                          Axios API modules (snake_case -> camelCase adapters)
    │   ├── axios.ts                  Axios instance + JWT interceptors (auto-refresh 401 queue)
    │   ├── products.ts               productsApi (GET /products, CRUD) + stockApi (/stock/in, /stock/out)
    │   ├── history.ts                historyApi (GET /history)
    │   ├── tickets.ts                Tickets CRUD
    │   ├── purchaseOrders.ts         PO listing
    │   ├── suppliers.ts              Suppliers listing
    │   ├── notifications.ts          Notifications feed
    │   ├── ai.ts                     YOLO detect, OCR invoice, AI ticket recommend
    │   └── auth.ts                   Login, refresh, profile
    ├── components/
    │   ├── AppButtons.tsx            PrimaryButton / SecondaryButton (shared UI)
    │   ├── Cards.tsx                 StatisticCard, ProductCard, HistoryCard, TicketCard
    │   ├── FeedbackStates.tsx        LoadingState, ErrorState, EmptyState
    │   ├── CameraHUD.tsx             Product scanning camera overlay (Workflow 2)
    │   └── YOLOCameraHUD.tsx         YOLO11 live detection HUD (Workflow 1 product/invoice/label modes)
    ├── constants/
    │   ├── config.ts                 API_BASE_URL (default http://172.18.221.31:8000), STORAGE_KEYS, PRODUCT_ICONS
    │   └── theme.ts                  Colors, Spacing, BorderRadius, Typography design tokens
    ├── contexts/
    │   ├── AuthContext.tsx           isAuthenticated, user, login/logout, token persistence
    │   └── AppContext.tsx            Global app state (theme, notifications)
    ├── hooks/
    │   └── useApi.ts                 React Query hooks: useProducts, useTickets, useHistory, useReceiveStock, useAssignStock, useDetectProduct, useOcrInvoice, useRecommendTicket, usePurchaseOrders, useSuppliers, useNotifications
    ├── navigation/
    │   └── index.tsx                 Root Stack -> BottomTabNavigator ("MainTabs") + modals
    ├── screens/                      18 screens:
    │   ├── SplashScreen.tsx          Initial auth-check splash
    │   ├── LoginScreen.tsx           Email/password login form
    │   ├── DashboardScreen.tsx       KPIs (Total Inventory, Valuation, Open Tickets) + gamification + history feed
    │   ├── InventoryScreen.tsx       SKU grid/list, brand chips, search
    │   ├── ProductDetailsScreen.tsx  Single product drill-down
    │   ├── HistoryScreen.tsx         Unified IN/OUT movement logs + search
    │   ├── WorkflowSelectionScreen.tsx  "Receive Equipment" vs "Assign to Ticket" entry
    │   ├── WorkflowReceiveScreen.tsx Workflow 1: 5-step Receive (Scan Product -> Invoice -> PO -> Label -> Success)
    │   ├── WorkflowAssignScreen.tsx  Workflow 2: 3-step Assign (Select Product -> Ticket Method -> Success)
    │   ├── NotificationsScreen.tsx
    │   ├── ProfileScreen.tsx
    │   ├── SettingsScreen.tsx
    │   ├── ReportsScreen.tsx
    │   ├── AuditScreen.tsx
    │   ├── SuppliersScreen.tsx
    │   ├── PurchaseOrdersScreen.tsx
    │   ├── UsersScreen.tsx
    │   └── AboutScreen.tsx
    ├── services/
    │   ├── auth.ts                   secureAuth: AsyncStorage + SecureStore token wrapper
    │   ├── camera.ts                 Camera permission + capture helpers
    │   ├── ocr.ts                    Mobile OCR bridge using @react-native-ml-kit/text-recognition
    │   ├── notification.ts           Push notification helpers
    │   └── storage.ts                Binary/asset storage helper
    ├── theme/index.ts                RN Paper theme provider configuration
    ├── types/index.ts                TypeScript interfaces mirroring backend (Product, PurchaseOrder, Ticket, HistoryMovement, ScanResult, etc.)
    └── utils/index.ts                Shared pure utility functions
```

---

## Database Schema (9 Tables, 6 Core Models Exported)

### Tables Defined by the `models` Package (Required 6)

| # | Model | Table | Purpose |
|---|-------|-------|---------|
| 1 | `User` | `users` | Authentication: username, email, password_hash, role (admin/manager/technician) |
| 2 | `Document` | `documents` | Scanned invoices: document_type, document_number, supplier, image_path, extracted_text |
| 3 | `PurchaseOrder` | `purchase_orders` | PO cache: po_number (unique), document_id FK, description (LLM cached), serial_numbers (comma-sep CSV) |
| 4 | `Inventory` | `inventory` | Master stock rows: purchase_order_id FK, category, brand, product_name, article_number, serial_number, quantity_available, status, received_by, received_at |
| 5 | `StockEntry` | `stock_entries` | IN audit trail: inventory_id FK, quantity_received, created_by, created_at |
| 6 | `StockExit` | `stock_exits` | OUT audit trail: inventory_id FK, ticket_number, quantity, created_by, created_at |

### Additional Tables (Defined Inside `models/inventory.py` - Not in `__all__`)

| Table | Purpose |
|-------|---------|
| `inventory_movements` | Unified movement log: id (MOV-XXXXXXXX), product_id, product_name, action (IN/OUT), quantity, user, po_id, ticket_id, notes, timestamp — used by GET `/history` |
| `tickets` | Support tickets: id (T-XXXXXXXX), title, description, priority, category, product_needed, status, requester, assignee, timestamps — Workflow 2 target |

### Important: No Standalone `products` Master Table
The `products` table does **not** exist as a SQLAlchemy model. Aggregate stock is tracked per **category** inside `inventory` rows. The mobile `Product` type is synthesized client-side by the API adapter layer.

### Auto-Migration
`init_db()` in [database.py](file:///c:/Users/USER/Downloads/stockit/backend/app/database.py#L40-L63) runs on FastAPI startup:
1. `Base.metadata.create_all()` — creates any missing tables.
2. Manual `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` — ensures documents + purchase_orders have expanded columns and correct TEXT types.

---

## Architecture & Data Flow

### Backend API Prefix Convention
Routers are mounted at **both** `/api/v1` and the root `/` prefix for mobile compatibility:
- `/api/v1/products/detect`, `/products/detect` → both work.
- Inventory router ([inventory.py](file:///c:/Users/USER/Downloads/stockit/backend/app/routers/inventory.py#L17)) uses `prefix=""` and is **additionally** mounted with no prefix at line 82 of `main.py`. This means `/stock/in`, `/history`, `/tickets` are available at both `/api/v1/stock/in` and `/stock/in`.

Currently disabled routers (commented out in [main.py](file:///c:/Users/USER/Downloads/stockit/backend/app/main.py#L84-L85)):
- `auth.router` — JWT login/refresh endpoints exist but are not mounted.
- `stock_entry.router` — legacy workflow endpoints exist but are not mounted.

### Transactional Stock Operations
[InventoryService](file:///c:/Users/USER/Downloads/stockit/backend/app/services/inventory_service.py) is the single source of truth for stock mutations:
- `receive_stock()` — Upserts `inventory` (by article_number match, otherwise create), then **commits**. Return value is a synthetic `InventoryMovement` payload (the row is NOT yet inserted into `inventory_movements` table in the current implementation — only returned to the HTTP client).
- `assign_stock()` — Currently returns a synthetic OUT movement. Does **not** decrement `inventory.quantity_available` or write to `stock_exits`.
- `create_inventory_and_stock_entry()` — Used by the legacy 5-step workflow path. Creates `Inventory` + `StockEntry` as two separate commits.

### OCR Invoice Pipeline
1. Mobile uploads photo → `document_analysis` router.
2. Primary: `ocr_service.py` uses `pytesseract` (requires the **Tesseract OCR binary** on PATH; if missing it falls back to a hardcoded sample invoice `INV-2026-8942`).
3. Fallback: `azure_ocr_service.py` calls Azure Computer Vision.
4. Parsing: `ocr_parser_service.py` extracts supplier, invoice number, line items, serial numbers.
5. Enrichment: `llm_service.py` calls Llama 3.3 / Azure AI Foundry to write cached PO descriptions.
6. Persistence: `document_service.py` writes `Document` + linked `PurchaseOrder` rows.

### Reorder Levels
Managed via a **constant map** inside `inventory_service.py` (not a DB column) because the `products`/`reorder_level` schema was removed.

---

## Mobile Architecture

### Navigation
Defined in [navigation/index.tsx](file:///c:/Users/USER/Downloads/stockit/mobile/navigation/index.tsx):
- **Root Stack** (`RootStackParamList`): Splash → Login → **MainTabs** (BottomTabNavigator) OR modal screens (ProductDetails, WorkflowSelection, WorkflowReceive, WorkflowAssign, Suppliers, PurchaseOrders, Users, Audit, Reports, Settings, About).
- **Bottom Tabs** (`BottomTabParamList`): Home (DashboardScreen), Inventory, WorkflowSelection ("Scan" center button), History, Profile.
- Navigator name is **`MainTabs`**, not `MainDrawer`. Any `navigation.navigate('MainDrawer')` calls will silently fail (screen doesn't exist).

### API Adapters (snake_case → camelCase)
The backend emits snake_case JSON (`article_number`, `purchase_order_id`). The mobile TypeScript types use camelCase (`articleNumber`, `purchaseOrderId`). The bridge is implicit inside each `api/*.ts` module — axios response data is typed as the camelCase interface, so consumers receive correctly-typed objects.

### React Query (TanStack Query v5)
All server-state lives in [hooks/useApi.ts](file:///c:/Users/USER/Downloads/stockit/mobile/hooks/useApi.ts):
- `useProducts()` → queryKey `['products']`
- `useHistory()` → queryKey `['history']`
- `useTickets()` → queryKey `['tickets']`
- `useReceiveStock()` mutation → onSuccess invalidates `['products', 'history', 'purchaseOrders']`
- `useAssignStock()` mutation → onSuccess invalidates `['products', 'history', 'tickets']`

### Authentication Flow
- JWT access + refresh tokens stored via `secureAuth` (Expo SecureStore when available, AsyncStorage fallback).
- Axios interceptor ([axios.ts](file:///c:/Users/USER/Downloads/stockit/mobile/api/axios.ts#L27-L42)) queues 401 failures, calls `/auth/refresh`, replays queued requests with the new token.
- AuthContext exposes `isAuthenticated` — Navigation renders Splash → Login → MainTabs based on this flag.

### New API Endpoints
- `GET /dashboard/kpis` - Returns comprehensive dashboard metrics including total inventory, open tickets, low stock alerts, category distribution, and weekly movement statistics
- `GET /inventory` - Lists all inventory rows with optional filtering by category, brand, and search terms
- `GET /inventory/{inventory_id}` - Get a single inventory item by primary key
- `GET /history/movements` - Raw inventory_movements feed for operational logging
- `POST /tickets` - Create new support tickets with auto-generated IDs

### Enhanced Inventory Service
The `inventory_service.py` has been significantly enhanced with:
- **Movement Persistence**: Fixed issue where `inventory_movements` table wasn't being written during stock operations
- **Product Resolution**: Automatic product type resolution and creation with normalization for YOLO categories
- **Stock Adjustment**: Safe stock-on-hand delta adjustments with clamping to prevent negative values
- **Dashboard KPIs**: Real-time calculation of key performance indicators including low stock alerts and category distribution
- **Transactional Operations**: Proper database transaction handling for stock entry and exit operations
- **Serial Number Normalization**: Handling of various serial number formats (comma-separated, arrays, etc.)

### Enhanced Data Models
- **Inventory Model**: Added hybrid property for backward-compatible category access via products FK
- **Product Model**: Enforced 3-column constraint (id, product_type, stock_on_hand) with proper validation
- **Dashboard Schemas**: New Pydantic models for KPIs, low stock alerts, and category stock distribution
- **Movement Tracking**: Enhanced inventory_movements table with proper timestamp and reference tracking

### Mobile App Updates
- **ML Kit OCR Integration**: Added `@react-native-ml-kit/text-recognition` for on-device text recognition as an alternative to server-side OCR
- **Expo SDK 54**: Updated to latest Expo SDK with improved camera and barcode scanning capabilities
- **TypeScript 5.9.2**: Enhanced type safety across the application
- **Updated Dependencies**: All major dependencies updated to latest stable versions including React 19.1.0 and React Native 0.81.5

### Dashboard Features
The dashboard now provides comprehensive real-time metrics:
- **Total Inventory**: Aggregate count of all inventory items across all categories
- **Stock Valuation**: Calculated value based on product categories and quantities
- **Open Tickets**: Count of active support tickets requiring attention
- **Low Stock Alerts**: Dynamic alerts for both product types and individual inventory items falling below thresholds
- **Category Distribution**: Visual breakdown of stock by product type with percentage shares
- **Movement Analytics**: Weekly statistics for stock-in, stock-out, and total movements
- **Status Distribution**: Breakdown of inventory items by status (available, assigned, maintenance, etc.)

---

## Workflows (Mobile)

### Workflow 1 — Receive Equipment (WorkflowReceiveScreen)
5 clickable stepper steps, each guarded by scan presence:
1. **Scan Product** → YOLO11 via [YOLOCameraHUD](file:///c:/Users/USER/Downloads/stockit/mobile/components/YOLOCameraHUD.tsx) → category/brand/confidence + bounding-box overlay.
2. **Scan Invoice** → OCR extracts supplier, invoice number, PO suggestion, line items, serial numbers.
3. **Select Purchase Order** → Merged list of (a) POs extracted from the invoice, (b) DB POs, (c) hardcoded demo fallback `2000234706` if none.
4. **Scan Shipping Label** → Article number, QTY, PO ref, extracted serial numbers + Pre-Save review card.
5. **Success** → Calls `useReceiveStock()` (`POST /stock/in`), shows movement summary, "Return to Dashboard" button.

### Workflow 2 — Assign to Ticket (WorkflowAssignScreen)
3 steps:
1. **Select Product** — AI scan (CameraHUD) OR roster list OR from preselected route param.
2. **Choose Ticket** — Three tabs: AI Recommendation (Llama-based priority match) / All Tickets list / Direct Ticket ID input.
3. **Success** → Calls `useAssignStock()` (`POST /stock/out`).

---

## Technology Stack

### Backend
| Layer | Tech | Version |
|-------|------|---------|
| Framework | FastAPI | 0.104.1 |
| ASGI Server | uvicorn[standard] | 0.24.0 |
| ORM | SQLAlchemy | 2.0.23 |
| DB Driver | psycopg2-binary | 2.9.12 |
| Database | PostgreSQL (Supabase) | N/A (cloud) |
| Validation | Pydantic v2 | 2.11.5 |
| Auth | python-jose + passlib[bcrypt] + bcrypt | 3.5.0 / 1.7.4 / 4.3.0 |
| Object Detection | ultralytics (YOLO11) | 8.4.98 |
| Image Processing | opencv-python, pillow | 4.12.0.88 / ≥10 |
| OCR | pytesseract + Tesseract binary | 0.3.13 (package only) |
| LLM | Azure AI Foundry / Ollama (Llama 3.3) | Config-driven |
| HTTP Client | aiohttp, requests | 3.12.0 / ≥2.28 |
| File Operations | aiofiles | 25.1.0 |

### Mobile
| Layer | Tech | Version |
|-------|------|---------|
| Runtime | Expo SDK | 54 |
| UI Framework | React Native | 0.81.5 |
| React | React | 19.1.0 |
| Navigation | @react-navigation/native-stack + bottom-tabs | 7.3.10 / 7.3.10 |
| Server State | @tanstack/react-query | 5.72.2 |
| UI Library | react-native-paper | 5.12.5 |
| Icons | react-native-vector-icons (MaterialCommunityIcons) | 10.2.0 |
| Forms | react-hook-form | 7.56.4 |
| Camera | expo-camera | 16.0.0 |
| Barcode | expo-barcode-scanner | 13.0.1 |
| Image Picker | expo-image-picker | 17.0.0 |
| OCR | @react-native-ml-kit/text-recognition | 2.0.0 |
| Secure Storage | expo-secure-store | 15.0.0 |
| Persistence | @react-native-async-storage/async-storage | 2.2.0 |
| HTTP | axios | 1.9.0 |
| Language | TypeScript | 5.9.2 |

---

## Configuration & Environment

### Backend (`backend/.env` — see `.env.example`)
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname   # Supabase PostgreSQL
SECRET_KEY=your-jwt-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
YOLO_MODEL_PATH=models_ai/best.pt
AZURE_AI_ENDPOINT=        # Azure AI Foundry (optional)
AZURE_AI_API_KEY=         # Azure AI Foundry (optional)
LLM_PROVIDER=azure        # "azure" or "ollama"
AZURE_CV_ENDPOINT=https://stockit-foundry.services.ai.azure.com
AZURE_LLM_ENDPOINT=       # Llama 3.3 endpoint (optional)
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
UPLOAD_DIR=uploads
DEBUG=False
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081,exp://*
API_V1_PREFIX=/api/v1
PROJECT_NAME=StockIT API
VERSION=1.0.0
```

### New Environment Variables
- `AZURE_CV_ENDPOINT` - Azure Computer Vision endpoint for OCR fallback
- `PRODUCT_TYPE_LOW_STOCK_THRESHOLD` - Threshold for product type low stock alerts (default: 5)
- `INVENTORY_ITEM_LOW_STOCK_THRESHOLD` - Threshold for individual item low stock alerts (default: 2)

### Mobile (`mobile/constants/config.ts` + `app.json extra`)
```ts
API_BASE_URL = extra.apiUrl ?? process.env.EXPO_PUBLIC_API_URL ?? 'http://172.18.221.31:8000';
```
Override by setting `"expo.extra.apiUrl"` in [app.json](file:///c:/Users/USER/Downloads/stockit/mobile/app.json).

Default API port for the backend when launched via `start.bat`/`uvicorn` is **8000** (8010 was used historically per project memory; verify the actual port before testing).

---

## Running the Project

### Backend
```powershell
# Windows
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Copy .env.example to .env and fill DATABASE_URL
copy .env.example .env
# Start server
.\start.bat
# Or directly: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check: `GET http://localhost:8000/health` → `{"status": "healthy", ...}`

### Mobile
```powershell
cd mobile
npm install
npm start          # Expo dev server (scan QR from phone)
# or
npm run android    # Android emulator/device
npm run ios        # iOS simulator (macOS only)
```

Lint/typecheck: `npm run lint`

---

## Known Issues & Active Workarounds

| Issue | Detail | Workaround |
|-------|--------|------------|
| **Tesseract OCR binary missing** | `pytesseract` Python package is installed, but the Tesseract executable is not on PATH. OCR calls fail and return hardcoded sample invoice (INV-2026-8942). | Install Tesseract from UB-Mannheim/tesseract (Windows) or `apt install tesseract-ocr` (Linux). |
| **"Return to Dashboard" broken in Workflow success screens** | Buttons call `navigation.navigate('MainDrawer')` but the navigator is registered as `MainTabs` (see [navigation/index.tsx](file:///c:/Users/USER/Downloads/stockit/mobile/navigation/index.tsx#L121)). | Fix target name to `'MainTabs'` in WorkflowReceiveScreen and WorkflowAssignScreen. |
| **Dashboard notification bell uses wrong target** | [DashboardScreen.tsx line 64](file:///c:/Users/USER/Downloads/stockit/mobile/screens/DashboardScreen.tsx#L64) calls `navigate('MainDrawer', { screen: 'DashboardTabs', params: { screen: 'Profile' } })` — neither route exists. | Use `navigate('MainTabs', { screen: 'Profile' })`. |
| **`inventory_movements` table not written on stock ops** | `receive_stock()` and `assign_stock()` return movement dicts but don't INSERT rows into `inventory_movements`. GET `/history` queries that table → returns only seed/migrated rows, not recent movements from workflows. | **FIXED**: The backend now properly persists movements to `inventory_movements` table via `_persist_movement()` method in `inventory_service.py`. The `/history` endpoint returns both audit tables and movements. |
| **`assign_stock` does not write `StockExit` or decrement inventory QTY** | Only returns synthetic movement. | **PARTIALLY FIXED**: Stock exit persistence is now implemented via `_persist_stock_exit()` method, but full inventory quantity adjustment still needs verification. |
| **Auth router is disabled** | `auth.router` and `stock_entry.router` are commented out in [main.py](file:///c:/Users/USER/Downloads/stockit/backend/app/main.py#L84-L85). Login/refresh endpoints return 404. | Mobile AuthContext + refresh interceptor handle missing auth gracefully (fallback to cached state). |
| **Backend `products` master GET endpoint missing** | Mobile `productsApi.getAll` calls `GET /products` but no router exports that path. `useProducts()` powers Dashboard KPIs and Inventory screen — if the endpoint is absent the screen shows ErrorState. | **FIXED**: The mobile app now uses `GET /inventory` endpoint instead which provides comprehensive inventory data with filtering capabilities. The products API module has been updated to use the correct endpoints. |
| **YOLO model file missing from repo** | `models_ai/best.pt` is a `.gitkeep` placeholder. `yolo_service.py` will fail on load. | Place your trained `best.pt` in `backend/models_ai/`. |

---

## Hard Constraints & Engineering Rules (Non-Negotiable)

1. **Product categories** are limited to: Laptop, Mouse, Keyboard, Monitor, Headset (plus Networking/Server/Tablet/Phone/Accessories exposed in `/products/categories` for future use).
2. **The `products` master table** — if ever re-introduced — must contain only three columns: `id`, `category` (unique), `stock_on_hand`.
3. **Stock operations are transactional**: any mutation must update the specific inventory row, the aggregate `stock_on_hand` (in the products table if restored), and write a row to both the type-specific audit table (`stock_entries`/`stock_exits`) and the unified `inventory_movements` audit table.
4. **History view** must present a unified representation of IN (stock_entries) and OUT (stock_exits) movements.
5. **Routers mount at both `/api/v1` and root `/` prefixes** for Expo mobile compatibility (deep link CORS and Android network config differences).
6. **Entry Workflow UI is stable** — do not change the existing 5-step visual/interaction behavior; only the underlying persistence logic should evolve.
7. **Reorder levels** live in a constant map in `inventory_service.py` (no DB column).

---

## Defaults & Seed Fallbacks

| What | Value | Where |
|------|-------|-------|
| Demo PO (when none available) | `2000234706`, Supplier `Lactech plus`, Item: MacBook Pro 16" M5 | [WorkflowReceiveScreen.displayPOs](file:///c:/Users/USER/Downloads/stockit/mobile/screens/WorkflowReceiveScreen.tsx#L90-L148) |
| Hardcoded fallback invoice (OCR fails) | INV-2026-8942 | `ocr_service.py` exception path |
| Ticket ID validation hint | `HR-NEW-2026` / `ETXTUN-41` | [WorkflowAssignScreen.handleValidateId](file:///c:/Users/USER/Downloads/stockit/mobile/screens/WorkflowAssignScreen.tsx#L70-L79) |
| Default technician in receive mutation | `"admin"` | [WorkflowReceiveScreen.handleConfirmReceive](file:///c:/Users/USER/Downloads/stockit/mobile/screens/WorkflowReceiveScreen.tsx#L182-L207) |
| Default API URL | `http://172.18.221.31:8000` | [config.ts](file:///c:/Users/USER/Downloads/stockit/mobile/constants/config.ts#L7-L8) |
| Hardcoded brand filter chips | All, Dell, HP, Apple, EPOS, Logitech | [InventoryScreen](file:///c:/Users/USER/Downloads/stockit/mobile/screens/InventoryScreen.tsx#L17) |
| Gamification demo state | Level 4 Expert, 8/10 scans | [DashboardScreen](file:///c:/Users/USER/Downloads/stockit/mobile/screens/DashboardScreen.tsx#L73-L89) |

---

## Recent Improvements & New Features

### Backend Enhancements
1. **Dashboard KPIs System**: Implemented comprehensive dashboard metrics endpoint with real-time calculations
2. **Movement Persistence Fix**: Resolved critical issue where inventory movements weren't being persisted to the database
3. **Enhanced Inventory Service**: Added robust product resolution, stock adjustment, and transaction handling
4. **Low Stock Alerts**: Dynamic alerting system for both product types and individual inventory items
5. **API Endpoint Expansion**: Added new endpoints for inventory management, ticket creation, and movement tracking

### Mobile App Improvements
1. **ML Kit Integration**: Added on-device text recognition capabilities for improved OCR performance
2. **Expo SDK 54 Upgrade**: Latest SDK with enhanced camera and barcode scanning features
3. **Updated Technology Stack**: React 19.1.0, React Native 0.81.5, and TypeScript 5.9.2 for better performance and type safety
4. **Enhanced API Integration**: Updated to use new backend endpoints for improved data accuracy

### Data Model Improvements
1. **Product Model Constraints**: Enforced 3-column product table structure for data integrity
2. **Inventory Model Enhancements**: Added hybrid properties for backward compatibility
3. **Movement Tracking**: Improved audit trail with proper timestamp and reference handling
4. **Schema Validation**: Enhanced Pydantic schemas for better request/response validation

### Bug Fixes
1. **Fixed inventory_movements persistence**: Movements now properly written during stock operations
2. **Resolved product endpoint issues**: Mobile app now uses correct inventory endpoints
3. **Enhanced error handling**: Better transaction management and error recovery
4. **Serial number handling**: Improved normalization and validation of various serial number formats
