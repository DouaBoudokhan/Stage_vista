/**
 * OCR Service — all text recognition is performed server-side by Azure Computer Vision.
 * The mobile app sends the raw image to the backend; no on-device OCR engine is needed.
 */

export interface OCRResult {
  text: string;
  confidence: number;
  processingTime: number;
  source: string;
  lines: string[];
}

export const OCRService = {
  /**
   * Clean and preprocess text for better parsing
   */
  cleanOCRText(rawText: string): string {
    return rawText
      .replace(/\s+/g, ' ')
      .replace(/[|]/g, 'I')
      .replace(/\n\s*\n/g, '\n')
      .trim();
  },

  /**
   * Validate OCR result quality
   */
  validateOCRQuality(ocrResult: OCRResult): {
    isGoodQuality: boolean;
    issues: string[];
    score: number;
  } {
    const issues: string[] = [];
    let score = 100;

    if (!ocrResult.text || ocrResult.text.length < 10) {
      issues.push('Very little text extracted');
      score -= 50;
    }

    return {
      isGoodQuality: score >= 50,
      issues,
      score: Math.max(0, score),
    };
  },
};