# StockIT - Mobile Hardware & Inventory Management Solution

StockIT is a modern inventory and hardware asset management system featuring real-time tracking of IT equipment, automated barcode/OCR-based stock entry, AI-assisted ticket assignments, and comprehensive analytics.

---

## 🏗️ Architecture Overview

The system architecture consists of 8 relational application tables:

1. **`users`** — Authentication, authorization, and roles.
2. **`products`** — Master product catalog (`id`, `product_name`, `tracking_type`, `stock_on_hand`).
3. **`documents`** — Scanned invoices and delivery documents.
4. **`purchase_orders`** — Purchase order metadata and cached descriptions.
5. **`inventory`** — Current physical asset and bulk stock records (`id`, `product_id`, `purchase_order_id`, `article_number`, `serial_number`, `quantity_available`, `status`).
6. **`stock_entries`** — Audit trail for stock received.
7. **`stock_exits`** — Audit trail for stock assigned to support tickets.
8. **`tickets`** — Internal IT support tickets equipment is assigned to.

---

## 🏷️ Serialized vs. Bulk Stock Tracking

StockIT deterministically enforces equipment tracking rules at the **Product catalog level** (`products.tracking_type`):

- **SERIALIZED** (`Laptop`, `Monitor`):
  - 1 inventory row per physical asset (`quantity_available = 1`).
  - Serial number is **required**.
  - Distinct asset tracking with lifecycle status (`AVAILABLE`, `ASSIGNED`, `MAINTENANCE`, `RETIRED`, `LOST`).
  - Stock assignment marks the asset `ASSIGNED` and decrements `products.stock_on_hand` by 1.

- **BULK** (`Headset`, `Mouse`, `Keyboard`):
  - 1 inventory row represents a batch of identical non-serialized equipment.
  - Serial number is `NULL`.
  - `quantity_available` holds the current quantity count.
  - Partial stock assignment decrements `quantity_available` without marking the batch `ASSIGNED`.

---

## 📸 OCR & AI Recognition Workflow

1. **YOLO11 Object Detection**: Real-time equipment classification on backend using trained YOLO model.
2. **Azure Computer Vision OCR**: Server-side text extraction from invoices and shipping labels via Azure Read API.
3. **Deterministic Parsing (Backend)**: Fast rule-based parsing resolves suppliers, document numbers, purchase orders, article numbers, and serials without AI hallucinations.
4. **Llama 3.3 LLM Caching (Azure AI)**: Generates human-friendly descriptions for purchase orders and caches them in `purchase_orders.description`.
4. **YOLO11 Object Detection**: Real-time IT hardware classification into core categories.

---

## 🚀 Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Running Unit Tests

```bash
cd backend
python -m unittest discover -s tests -v
```
