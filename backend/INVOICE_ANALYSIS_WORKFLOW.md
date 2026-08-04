# Invoice Analysis Workflow

## Overview
The Invoice Analysis workflow uses Azure Computer Vision OCR for server-side text recognition with backend deterministic parsing and LLM description caching.

## Flow Architecture
1. **Mobile Scan**: Camera captures image and sends to backend.
2. **Backend OCR**: Azure Computer Vision extracts text server-side.
3. **Backend Submission**: Extracted OCR text is sent to `POST /api/v1/documents/analyze`.
4. **Deterministic Parsing**: Backend rule-based parser extracts supplier, invoice number, purchase order numbers, and serial numbers.
4. **LLM Caching**: Checks database cache for existing PO descriptions. Calls Azure AI Foundry (Llama 3.3) only for uncached POs.
5. **Persistence**: Saves document metadata to `documents` and `purchase_orders`.