/**
 * OCR Service supporting both Google ML Kit (on-device for standalone/dev builds)
 * and seamless fallback to backend OCR when running inside Expo Go on iOS/Android.
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
   * Extract text from an image URI using Google ML Kit on-device recognition if available.
   * If running inside Expo Go, gracefully falls back to server-side OCR.
   */
  async recognizeText(imageUri: string): Promise<OCRResult> {
    const startTime = Date.now();

    try {
      // Safely load ML Kit module dynamically to avoid crashes in Expo Go
      let MLKitModule: any = null;
      try {
        MLKitModule = require('@react-native-ml-kit/text-recognition');
      } catch (e) {
        console.log('ℹ️ Google ML Kit native module not available (e.g. running in Expo Go)');
      }

      const TextRecognition = MLKitModule?.default || MLKitModule;
      const TextRecognitionScript = MLKitModule?.TextRecognitionScript;

      if (TextRecognition && typeof TextRecognition.recognize === 'function') {
        console.log('🔍 Starting Google ML Kit text recognition on-device...');
        const script = TextRecognitionScript?.LATIN || 'Latin';
        const result = await TextRecognition.recognize(imageUri, script);

        const processingTime = Date.now() - startTime;
        const text = result.text || '';
        const lines = (result.blocks || [])
          .flatMap((block: any) => block.lines || [])
          .map((line: any) => line.text);

        console.log(`✅ ML Kit extracted ${lines.length} lines (${text.length} chars) in ${processingTime}ms`);

        return {
          text,
          confidence: lines.length > 0 ? 0.9 : 0,
          processingTime,
          source: 'google_ml_kit',
          lines,
        };
      } else {
        console.log('ℹ️ Expo Go detected — delegating OCR to backend server');
        return {
          text: '',
          confidence: 0,
          processingTime: Date.now() - startTime,
          source: 'backend_fallback',
          lines: [],
        };
      }
    } catch (error) {
      console.warn('⚠️ Google ML Kit recognition error (will use backend OCR):', error);

      return {
        text: '',
        confidence: 0,
        processingTime: Date.now() - startTime,
        source: 'backend_fallback',
        lines: [],
      };
    }
  },

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