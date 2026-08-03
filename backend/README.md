# StockIT Backend API

FastAPI application for hardware stock management and document processing.

## Database Schema (8 Tables)

- `users`
- `products`
- `documents`
- `purchase_orders`
- `inventory`
- `stock_entries`
- `stock_exits`
- `tickets`

## API Endpoints

- `POST /api/v1/stock/in` — Receive stock into inventory
- `POST /api/v1/stock/out` — Assign stock to a ticket
- `GET /api/v1/inventory` — List current stock records
- `GET /api/v1/history` — Unified audit history timeline from `stock_entries` and `stock_exits`
- `GET /api/v1/dashboard/kpis` — Real-time KPI metrics and analytics
- `POST /api/v1/documents/analyze` — Document OCR parsing and LLM description caching
- `POST /api/v1/products/detect` — YOLO11 product classification
- `POST /api/v1/labels/analyze` — Package label text parsing

## Unit Tests

Run the test suite:
```bash
python -m unittest discover -s tests -v
```
