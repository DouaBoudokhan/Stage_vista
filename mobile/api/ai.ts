// AI API — all AI processing happens on the FastAPI backend
// The mobile app never calls Gemini/YOLO/OCR directly
import api from './axios';
import type { ScanResult, AIRecommendation } from '../types';

export const aiApi = {
  detectProduct: async (imageBase64: string): Promise<ScanResult> => {
    const { data } = await api.post<ScanResult>('/detect', {
      image: imageBase64,
      mode: 'product',
    });
    return data;
  },

  ocrInvoice: async (imageBase64: string): Promise<ScanResult> => {
    const { data } = await api.post<ScanResult>('/ocr', {
      image: imageBase64,
      mode: 'invoice',
    });
    return data;
  },

  analyzeInvoice: async (imageBase64: string): Promise<ScanResult> => {
    const { data } = await api.post<ScanResult>('/invoice-analysis', {
      image: imageBase64,
    });
    return data;
  },

  recommendTicket: async (payload: {
    productRef: string;
    category: string;
    brand: string;
  }): Promise<AIRecommendation> => {
    const { data } = await api.post<AIRecommendation>('/recommend-ticket', payload);
    return data;
  },
};
