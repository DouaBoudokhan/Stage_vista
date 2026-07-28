# StockIT Backend API

FastAPI backend for StockIT mobile inventory management application.

## 🚀 Features

- **REST API** - Full CRUD operations for inventory management
- **JWT Authentication** - Secure token-based authentication
- **AI Integration**:
  - YOLO object detection for IT equipment recognition
  - Tesseract OCR for invoice/document processing
- **PostgreSQL Database** - Supabase integration
- **SQLAlchemy ORM** - Type-safe database operations
- **Automatic API Documentation** - Swagger UI and ReDoc

---

## 📋 Requirements

- Python 3.11+
- PostgreSQL (Supabase account)
- Tesseract OCR (for invoice processing)

---

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Models
YOLO_MODEL_PATH=models_ai/best.pt

# Application
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,exp://192.168.*
```

**Generate SECRET_KEY:**
```bash
openssl rand -hex 32
```

### 4. Get Supabase Connection String

1. Go to [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. Go to **Settings** → **Database**
4. Copy **Connection String** (URI mode)
5. Replace `[YOUR-PASSWORD]` with your database password
6. Paste into `.env` as `DATABASE_URL`

### 5. Install Tesseract OCR (Optional - for invoice scanning)

**Windows:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Mac:**
```bash
brew install tesseract
```

### 6. Add YOLO Model (Optional - for object detection)

Place your trained YOLO model in:
```
backend/models_ai/best.pt
```

Or the default YOLOv8 will be downloaded automatically.

---

## 🏃 Running the Server

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Alternative (using Python)

```bash
python -m app.main
```

---

## 📚 API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout

### Products
- `GET /api/v1/products` - Get all products
- `GET /api/v1/products/{id}` - Get product by ID
- `POST /api/v1/products` - Create product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

### Inventory
- `POST /api/v1/stock/in` - Receive stock
- `POST /api/v1/stock/out` - Assign stock to ticket
- `GET /api/v1/history` - Get movement history

### Tickets
- `GET /api/v1/tickets` - Get all tickets
- `GET /api/v1/tickets/{id}` - Get ticket by ID
- `POST /api/v1/tickets` - Create ticket

### AI Detection
- `POST /api/v1/detect` - Detect objects in image (YOLO)
- `POST /api/v1/ocr` - Extract text from image (OCR)
- `POST /api/v1/invoice-analysis` - Analyze invoice

---

## 🧪 Testing the API

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@stockit.com",
    "name": "Admin User",
    "password": "password123",
    "role": "admin"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@stockit.com",
    "password": "password123"
  }'
```

Copy the `access_token` from response.

### 3. Create a Product

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Dell Laptop XPS 15",
    "reference": "DELL-XPS-15-2024",
    "category": "Laptop",
    "brand": "Dell",
    "quantity": 10,
    "price": 1299.99,
    "location": "Warehouse A"
  }'
```

---

## 🗄️ Database Schema

### Tables

**users**
- id (PK)
- email (unique)
- name
- hashed_password
- role (admin/manager/technician)
- is_active
- created_at, updated_at

**products**
- id (PK)
- name
- reference (unique, barcode/SKU)
- category, brand, model
- quantity, min_quantity, price
- location, supplier
- description, image_url
- created_at, updated_at, last_updated

**inventory_movements**
- id (PK)
- product_id (FK)
- action (Received/Assigned/Returned)
- quantity
- po_id, reference (for receiving)
- ticket_id, assignee (for assigning)
- user, notes
- timestamp

**tickets**
- id (PK)
- title, description
- status (Open/In Progress/Assigned/Closed)
- priority (Critical/High/Medium/Low)
- requester, assignee
- category, product_needed
- created_at, updated_at, closed_at

**invoices**
- id (PK)
- invoice_number (unique)
- supplier, total_amount, currency
- extracted_text, extracted_data (JSON)
- image_path, status
- processed_by, notes
- created_at, processed_at

---

## 📱 Mobile App Integration

Update your mobile app's API base URL:

**File:** `mobile/constants/config.ts`

```typescript
export const API_BASE_URL = 'http://YOUR_IP:8000/api/v1';
```

Replace `YOUR_IP` with your computer's local IP address.

**Find your IP:**

Windows:
```bash
ipconfig
```

Mac/Linux:
```bash
ifconfig
```

Example: `http://192.168.1.100:8000/api/v1`

---

## 🔧 Troubleshooting

### Database Connection Error

Make sure:
1. Supabase project is active
2. Database password is correct in `.env`
3. Connection string format: `postgresql://user:password@host:port/database`

### Port Already in Use

```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process on port 8000 (Linux/Mac)
lsof -ti:8000 | xargs kill -9
```

### Tesseract Not Found

Make sure Tesseract is installed and in PATH.

Update path in `app/services/ocr_service.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### YOLO Model Issues

If YOLO model is not found, the default YOLOv8n will download automatically on first use.

---

## 🚀 Deployment

### Using Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Railway/Render/Heroku

1. Push code to GitHub
2. Connect repository
3. Set environment variables
4. Deploy!

---

## 📝 License

MIT License

---

## 👥 Support

For issues or questions, contact: your-email@example.com

---

**Built with ❤️ for StockIT Mobile**
