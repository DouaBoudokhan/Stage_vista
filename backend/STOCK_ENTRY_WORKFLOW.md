# Stock Entry Workflow Documentation

## Overview

The Stock Entry workflow is a 5-step process for registering newly received IT equipment into the inventory system. It combines AI-powered object detection, OCR text extraction, and structured data validation to ensure accurate inventory management.

## Workflow Architecture

```
[Step 1] Product Detection (YOLO)
    ↓
[Step 2] Document OCR (Purchase Orders)
    ↓
[Step 3] Technician PO Selection
    ↓
[Step 4] Package Label OCR
    ↓
[Step 5] Database Save (Inventory + Stock Entry)
```

## API Endpoints

### Base URL: `/api/v1/stock-entry`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/start` | Start new workflow session |
| GET | `/status/{workflow_id}` | Get workflow status |
| POST | `/step1/detect-product` | Run YOLO product detection |
| POST | `/step1/confirm/{workflow_id}` | Confirm detection results |
| POST | `/step2/scan-document` | OCR delivery document |
| POST | `/step2/confirm/{workflow_id}` | Confirm document scan |
| POST | `/step3/select-po` | Select Purchase Order |
| POST | `/step4/scan-package` | OCR package label |
| POST | `/step4/confirm/{workflow_id}` | Confirm package scan |
| POST | `/step5/save` | Save final stock entry |
| DELETE | `/{workflow_id}` | Cancel workflow |

## Step-by-Step Process

### Step 1: Product Detection

**Purpose**: Identify the IT equipment category using AI vision

**Input**: 
```json
{
    "image_data": "base64_encoded_image"
}
```

**Process**:
1. Load YOLO11s model (`models_ai/best.pt`)
2. Run inference on product image
3. Return highest confidence detection
4. Validate confidence > 0.75 threshold

**Output**:
```json
{
    "category": "Laptop",
    "confidence": 0.97,
    "success": true,
    "message": "Successfully detected Laptop with 0.97 confidence"
}
```

**Supported Categories**:
- Laptop, Desktop, Monitor, Keyboard, Mouse
- Headset, Speaker, Webcam, Phone, Tablet
- Charger, Adapter, Cable, Docking Station, USB Hub
- Router, Switch, Modem

### Step 2: Document OCR

**Purpose**: Extract supplier info and Purchase Orders from delivery documents

**Input**:
```json
{
    "image_data": "base64_encoded_document_image"
}
```

**Process**:
1. Run OCR on delivery document (invoice/bon de livraison)
2. Extract supplier name and document number
3. Find all Purchase Orders with regex patterns
4. Extract serial numbers associated with each PO
5. Create database records for document and POs

**Output**:
```json
{
    "supplier": "TECH SOLUTIONS LTD",
    "document_number": "INV-2024-001234",
    "purchase_orders": [
        {
            "po_number": "2000234706",
            "description": "MacBook Pro 16 M5 24GB 1TB SSD",
            "serial_numbers": ["C7R2RVDQVQ"]
        }
    ],
    "extracted_text": "Full OCR text...",
    "success": true
}
```

### Step 3: Purchase Order Selection

**Purpose**: Let technician choose correct PO from detected options

**Input**:
```json
{
    "selected_po_number": "2000234706",
    "workflow_id": "uuid-workflow-id"
}
```

**Process**:
1. Validate selected PO exists in workflow data
2. Confirm PO exists in database
3. Update workflow state with selection
4. Prepare for package scanning

**Output**:
```json
{
    "message": "Purchase Order 2000234706 selected",
    "po_details": {
        "po_number": "2000234706",
        "description": "MacBook Pro 16 M5 24GB 1TB SSD",
        "serial_numbers": ["C7R2RVDQVQ"]
    },
    "next_step": 4
}
```

### Step 4: Package Label OCR

**Purpose**: Extract product details from physical package

**Input**:
```json
{
    "image_data": "base64_encoded_package_image",
    "workflow_id": "uuid-workflow-id"
}
```

**Process**:
1. Run OCR on package label
2. Extract: Brand, Product Name, Article Number, Quantity, PO
3. Validate all required fields present
4. Check for PO mismatch warnings

**Output**:
```json
{
    "brand": "APPLE",
    "product_name": "MacBook Pro 16 M5 24GB 1TB SSD",
    "article_number": "MBP16-001421",
    "quantity": 1,
    "po_on_package": "2000234706",
    "success": true,
    "warning": null
}
```

### Step 5: Database Save

**Purpose**: Create final inventory and stock entry records

**Input**:
```json
{
    "workflow_id": "uuid-workflow-id",
    "received_by": "technician_username",
    "confirm_warnings": true
}
```

**Process**:
1. Validate workflow completion
2. Check warning confirmations
3. Create Inventory record
4. Create StockEntry record
5. Update quantities
6. Mark workflow complete

**Output**:
```json
{
    "category": "Laptop",
    "brand": "APPLE",
    "product_name": "MacBook Pro 16 M5 24GB 1TB SSD",
    "article_number": "MBP16-001421",
    "quantity": 1,
    "supplier": "TECH SOLUTIONS LTD",
    "selected_po": "2000234706",
    "status": "COMPLETED",
    "inventory_id": 123,
    "stock_entry_id": 456
}
```

## Database Schema Updates

The workflow creates records in:

1. **Documents** - Delivery document metadata
2. **PurchaseOrders** - Extracted PO information  
3. **Inventory** - Final product records
4. **StockEntries** - Reception history

## Error Handling

### Common Error Scenarios:

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| Low confidence detection | 400 | YOLO confidence < 0.75 |
| No text found | 400 | OCR failed to extract text |
| No POs detected | 400 | No Purchase Orders in document |
| Workflow not found | 404 | Invalid/expired workflow ID |
| PO mismatch warning | 200 | Package PO ≠ Selected PO |
| Database error | 500 | Save operation failed |

### Error Response Format:
```json
{
    "detail": "Error description",
    "error_code": "DETECTION_FAILED",
    "step": 1
}
```

## Business Rules

### Validation Rules:
- ✅ Product detection confidence ≥ 0.75
- ✅ At least 1 Purchase Order found in document  
- ✅ Selected PO must exist in available options
- ✅ Package label must contain: Brand, Product, Article #, Qty
- ✅ All steps must complete in sequence

### Warning Conditions:
- ⚠️ Package PO differs from selected PO
- ⚠️ Serial numbers missing
- ⚠️ Quantity mismatch

## Testing

### Test the complete workflow:

```bash
cd /path/to/backend
python test_workflow.py
```

### Manual testing via Swagger UI:
1. Visit: `http://localhost:8000/docs`
2. Navigate to "Stock Entry Workflow" section
3. Test each endpoint sequentially

### API Testing with curl:

```bash
# Start workflow
curl -X POST http://localhost:8000/api/v1/stock-entry/start

# Get status
curl http://localhost:8000/api/v1/stock-entry/status/{workflow_id}
```

## Configuration

### Environment Variables:
- `YOLO_MODEL_PATH` - Path to trained YOLO model
- `DATABASE_URL` - Database connection string
- `DEBUG` - Enable debug mode

### Model Requirements:
- YOLO11s model trained on IT equipment
- Model file: `models_ai/best.pt`
- Minimum 15 IT equipment classes

## Performance

### Expected Response Times:
- Product Detection: < 2 seconds
- Document OCR: < 5 seconds  
- Package OCR: < 3 seconds
- Database Save: < 1 second

### Scalability:
- YOLO model loaded once at startup
- Workflow sessions stored in memory
- Auto-cleanup after 2 hours
- Production: Use Redis for session storage

## Integration

### Mobile App Integration:
1. Start workflow: `POST /start`
2. For each step: Capture image → Send to API → Confirm result
3. Handle warnings with user confirmation
4. Complete workflow: `POST /step5/save`

### Future Extensions:
- Stock Exit workflow (similar 5-step process)
- Batch processing multiple items
- Integration with ERP systems
- Advanced AI models for better accuracy

## Monitoring

### Key Metrics:
- Workflow completion rate
- YOLO detection accuracy
- OCR success rate  
- Average workflow duration
- Error distribution by step

### Logging:
- All API requests/responses logged
- Workflow state changes tracked
- OCR text stored for auditing
- Error details preserved