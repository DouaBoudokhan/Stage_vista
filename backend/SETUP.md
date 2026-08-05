# StockIT Backend Setup Guide

## Requirements
- Python 3.10+
- PostgreSQL / Supabase database

## Setup Steps

1. Environment Configuration:
   Create `.env` file in the `backend` directory with:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/stockit
   SECRET_KEY=your_secret_key
   AZURE_AI_ENDPOINT=https://your-endpoint.ai.azure.com
   AZURE_AI_API_KEY=your_api_key
   ```

2. Virtual Environment & Dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. Initialize Database:
   The database will initialize automatically on application startup, creating all 8 required tables and seeding the core product categories.

4. Start Server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
