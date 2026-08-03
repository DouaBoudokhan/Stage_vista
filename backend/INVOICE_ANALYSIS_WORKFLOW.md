# Invoice Analysis Workflow

## Overview
The Invoice Analysis workflow combines Google ML Kit on-device text recognition with backend deterministic parsing and LLM description caching.

## Flow Architecture
1. **Mobile Scan**: Camera captures image, Google ML Kit performs on-device OCR.
2. **Backend Submission**: Mobile sends extracted OCR text to `POST /api/v1/documents/analyze`.
3. **Deterministic Parsing**: Backend rule-based parser extracts supplier, invoice number, purchase order numbers, and serial numbers.
4. **LLM Caching**: Checks database cache for existing PO descriptions. Calls Azure AI Foundry (Llama 3.3) only for uncached POs.
5. **Persistence**: Saves document metadata to `documents` and `purchase_orders`.