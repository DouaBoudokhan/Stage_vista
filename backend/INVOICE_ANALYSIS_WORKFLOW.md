# Invoice Analysis Workflow Documentation

## Overview

The Invoice Analysis workflow is a production-ready AI system that processes invoice/delivery documents to extract Purchase Order information and generate human-readable descriptions. It combines deterministic parsing with Azure AI Foundry LLM capabilities while implementing intelligent caching to minimize API costs.

## Architecture

### Service-Oriented Design

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Router Layer  │    │  Service Layer   │    │ Database Layer  │
│                 │    │                  │    │                 │
│ • HTTP Handling │    │ • Business Logic │    │ • Data Models   │
│ • Validation    │───▶│ • Orchestration  │───▶│ • Persistence   │
│ • Response      │    │ • Error Handling │    │ • Relationships │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Services

1. **OCRParserService** - Deterministic text extraction
2. **LLMService** - Azure AI Foundry integration  
3. **DocumentService** - Workflow orchestration
4. **StorageService** - File management

## Workflow Steps

### Step 1: Deterministic Parsing (NO AI)

**Purpose**: Extract factual information using only rule-based parsing

**Input**: Raw OCR text from Google ML Kit
**Process**:
- Extract supplier name using pattern matching
- Extract invoice number using regex patterns
- Find all Purchase Order numbers
- Split text into PO sections
- Extract serial numbers for each PO
- Clean text content for LLM processing

**Output**:
```json
{
    "supplier": "TECH SOLUTIONS LTD",
    "invoice_number": "INV-2026-00012", 
    "purchase_orders": [
        {
            "po_number": "2000234706",
            "text": "MacBook Pro 16 M5 24GB RAM 1TB SSD",
            "serial_numbers": ["C02ABC123456"]
        }
    ]
}
```

**Critical Rule**: LLM never extracts factual data - only deterministic parsing.

### Step 2: Database Cache Lookup

**Purpose**: Avoid redundant LLM calls for known Purchase Orders

**Process**:
```sql
SELECT description 
FROM purchase_orders 
WHERE po_number = ? 
  AND description IS NOT NULL
```

- **Cache Hit**: Use existing description, skip LLM
- **Cache Miss**: Call LLM to generate description

**Benefits**:
- Reduces LLM API costs
- Improves response speed
- Ensures consistency

### Step 3: LLM Description Generation

**Purpose**: Generate concise, human-readable equipment descriptions

**Model**: Azure AI Foundry - Llama-3.3-70B-Instruct

**Prompt Strategy**:
```
You are an IT inventory specialist. Generate a concise, professional description for equipment from Purchase Order {po_number}.

RULES:
- Maximum 30 words
- Only describe what's explicitly mentioned in the text
- DO NOT invent specifications or details
- DO NOT infer missing information
- Use clear, professional language
- Focus on: brand, product type, key specifications
- Return ONLY valid JSON

Input text: "{po_text}"

Return format:
{"description": "Brief equipment description here"}
```

**Configuration**:
- Temperature: 0.1 (consistent output)
- Max tokens: 100
- Top-p: 0.95

### Step 4: Database Persistence

**Purpose**: Save all extracted data for future reference

**Records Created**:

1. **Document** record:
   - Supplier, invoice number, document type
   - Image path, OCR text
   - Timestamps

2. **PurchaseOrder** records:
   - PO number, LLM-generated description
   - Document reference
   - Timestamps for cache management

## API Endpoints

### Base URL: `/api/v1/documents`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | **Complete workflow** - analyze invoice image + OCR |
| POST | `/parse-ocr` | **Test parsing** - deterministic OCR parsing only |
| POST | `/generate-description` | **Test LLM** - generate description for PO text |
| GET | `/list` | List recent documents |
| GET | `/purchase-orders` | List POs with cache status |
| GET | `/cache-stats` | LLM cache performance metrics |
| GET | `/{document_id}` | Get specific document details |

## Complete Analysis Endpoint

### `POST /documents/analyze`

**Purpose**: Main endpoint for production workflow

**Input**:
- `image`: Multipart file upload (invoice/delivery document)
- `ocr_text`: Text extracted by Google ML Kit in React Native
- `document_type`: Type of document (default: "invoice")

**Process**:
1. Save uploaded image to storage
2. Parse OCR text deterministically
3. Create document record
4. For each Purchase Order:
   - Check cache for existing description
   - Generate new description via LLM if needed
   - Save/update PO record
5. Return complete structured results

**Response**:
```json
{
  "success": true,
  "document": {
    "id": 123,
    "supplier": "TECH SOLUTIONS LTD",
    "invoice_number": "INV-2026-00012",
    "document_type": "invoice",
    "image_path": "documents/uuid.png"
  },
  "purchase_orders": [
    {
      "id": 456,
      "po_number": "2000234706",
      "description": "Apple MacBook Pro 16 with M5 processor, 24GB RAM and 1TB SSD.",
      "serial_numbers": ["C02ABC123456"],
      "cached": false,
      "llm_used": true
    }
  ],
  "statistics": {
    "total_pos": 2,
    "cached_descriptions": 1,
    "new_descriptions": 1,
    "total_serial_numbers": 2
  }
}
```

## Database Schema

### Enhanced Tables

**Documents**:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(100) NOT NULL,
    document_number VARCHAR(255) NOT NULL,
    supplier VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    extracted_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**PurchaseOrders** (with LLM cache):
```sql
CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    po_number VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,  -- LLM-generated cache
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Key Indexes

- **Unique PO lookup**: `UNIQUE INDEX ON purchase_orders(po_number)`
- **Cache queries**: `INDEX ON purchase_orders(po_number) WHERE description IS NOT NULL`

## Configuration

### Environment Variables

```env
# Azure AI Foundry
AZURE_AI_ENDPOINT=https://your-endpoint.azureml.net
AZURE_AI_API_KEY=your-api-key
LLM_PROVIDER=azure

# Alternative: Ollama (on-premises)
LLM_PROVIDER=ollama
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# File Storage
UPLOAD_DIR=uploads
```

### Provider Switching

The architecture supports easy switching between cloud and on-premises LLM:

**Development** (Azure AI Foundry):
```python
llm_service = AzureAIFoundryService()
```

**Production** (On-premises Ollama):
```python
llm_service = OllamaService()  
```

No changes required in business logic or API contracts.

## Testing

### Comprehensive Test Suite

```bash
# Run complete test suite
python test_invoice_analysis.py
```

**Test Coverage**:
- ✅ Deterministic OCR parsing
- ✅ LLM description generation
- ✅ Complete workflow integration
- ✅ Cache functionality verification
- ✅ API endpoint validation
- ✅ Error handling scenarios

### Manual Testing

1. **Start Backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Visit Swagger UI**: http://localhost:8000/docs

3. **Test Individual Components**:
   - Parse OCR text: `/documents/parse-ocr`
   - Generate description: `/documents/generate-description`
   - Complete analysis: `/documents/analyze`

## Production Deployment

### Performance Optimizations

1. **LLM Cache Strategy**:
   - Index on `po_number` for fast lookup
   - Unique constraint prevents duplicates
   - Cache hit rate monitoring

2. **File Storage**:
   - Local storage for development
   - S3/Azure Blob for production
   - Image compression and optimization

3. **Error Handling**:
   - Graceful LLM failures with fallback descriptions
   - File cleanup on errors
   - Comprehensive logging

### Monitoring Metrics

- **Cache Hit Rate**: Percentage of POs with existing descriptions
- **LLM Response Time**: Azure AI Foundry API latency
- **Parsing Success Rate**: OCR text processing success
- **Error Distribution**: Track errors by workflow step

### Scaling Considerations

1. **Database**: Connection pooling for concurrent requests
2. **LLM Service**: Rate limiting and retry logic
3. **File Storage**: CDN for image serving
4. **Caching**: Redis for session-based caching

## Integration with Mobile App

### React Native Integration

1. **Capture Invoice Image** with camera
2. **Run OCR** using Google ML Kit locally
3. **Upload** image + OCR text to `/documents/analyze`
4. **Display Results** with PO selection interface
5. **Continue** to package scanning workflow

### Example React Native Code

```javascript
// Capture and analyze invoice
const analyzeInvoice = async (imageUri, ocrText) => {
  const formData = new FormData();
  formData.append('image', {
    uri: imageUri,
    type: 'image/jpeg',
    name: 'invoice.jpg'
  });
  formData.append('ocr_text', ocrText);
  formData.append('document_type', 'invoice');

  const response = await fetch('/api/v1/documents/analyze', {
    method: 'POST',
    body: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  return response.json();
};
```

## Security Considerations

### Data Protection
- **Image Storage**: Secure file permissions and access controls
- **OCR Text**: Encrypted storage of sensitive business documents  
- **API Keys**: Environment variables, never in code
- **Input Validation**: File type/size limits, text sanitization

### Privacy Compliance
- **Data Retention**: Configurable cleanup policies
- **Access Logging**: Track document access and modifications
- **Anonymization**: Option to redact sensitive information

## Troubleshooting

### Common Issues

**1. DNS Resolution Errors**
```
Error: could not translate host name
Solution: Check network connectivity, verify Azure endpoint
```

**2. LLM API Failures**
```
Error: Azure API error 401
Solution: Verify AZURE_AI_API_KEY in .env file
```

**3. OCR Parsing Failures**
```
Error: No Purchase Orders found
Solution: Check OCR text quality, review regex patterns
```

**4. File Upload Issues**
```
Error: File save verification failed
Solution: Check UPLOAD_DIR permissions, disk space
```

### Debug Mode

Enable detailed logging:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### Health Checks

Monitor system health:
- `/health` - Basic API health
- `/documents/cache-stats` - LLM cache performance  
- File system permissions and disk space

## Future Enhancements

### Planned Features

1. **Multi-language OCR** support
2. **PDF document processing**
3. **Batch invoice analysis**
4. **Advanced error recovery**
5. **Real-time analytics dashboard**

### AI Improvements

1. **Custom fine-tuned models** for IT equipment
2. **Confidence scoring** for extracted data
3. **Auto-correction** of OCR errors
4. **Smart field validation** using business rules

The Invoice Analysis workflow provides a robust, scalable foundation for intelligent document processing in the StockIT inventory management system.