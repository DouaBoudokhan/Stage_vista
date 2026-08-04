# StockIT Project Summary

StockIT is a hardware inventory management solution for IT equipment.

## Database Architecture
The database consists of 8 application tables:
- `users`
- `products` (master catalog table with `tracking_type` and `stock_on_hand`)
- `documents`
- `purchase_orders`
- `inventory` (asset records with lifecycle status: `AVAILABLE`, `ASSIGNED`, `MAINTENANCE`, `RETIRED`, `LOST`)
- `stock_entries`
- `stock_exits`
- `tickets`

There is NO `inventory_movements` table. History is queried dynamically from `stock_entries` (IN) and `stock_exits` (OUT).

## Tracking Types (Product Level)
- **SERIALIZED** (`products.tracking_type = 'SERIALIZED'`): `Laptop`, `Monitor` (1 row per asset, serial required, status = AVAILABLE/ASSIGNED/MAINTENANCE/RETIRED/LOST).
- **BULK** (`products.tracking_type = 'BULK'`): `Headset`, `Mouse`, `Keyboard` (1 row for batch, serial NULL, quantity decremented on assign).

## OCR
Azure Computer Vision is the OCR engine for server-side text extraction from shipping labels. Invoice analysis uses mobile camera capture with backend OCR processing.
