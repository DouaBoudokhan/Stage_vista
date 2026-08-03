// Camera and Scanner Services
// Sends images to backend for all OCR & AI processing (Azure Computer Vision + YOLO).
import * as ImagePicker from 'expo-image-picker';
import { Alert } from 'react-native';
import { CONFIG } from '../constants/config';

export interface CameraScanOptions {
  mode: 'product' | 'invoice' | 'label' | 'barcode' | 'qr';
}

export const CameraService = {
  // Check and request camera permission
  async requestPermission(): Promise<boolean> {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(
        'Camera Permission Blocked',
        'StockIT requires active camera access for hardware detection, label OCR, and invoice parsing. Please check your device settings.'
      );
      return false;
    }
    return true;
  },

  // Take a photo using the device camera
  async takePhoto(): Promise<{ base64: string; uri: string } | null> {
    const hasPermission = await this.requestPermission();
    if (!hasPermission) return null;

    try {
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets[0].base64) {
        return {
          base64: result.assets[0].base64,
          uri: result.assets[0].uri,
        };
      }
    } catch (error) {
      console.error('Camera photo capture error:', error);
    }
    return null;
  },

  /**
   * Analyze invoice image.
   * Sends the raw image to the backend. Azure Computer Vision extracts OCR text server-side.
   */
  async analyzeInvoice(base64Image: string, imageUri?: string): Promise<any> {
    try {
      console.log('📄 Starting invoice analysis (server-side Azure OCR)...');

      const formData = new FormData();
      const uri = imageUri ?? `data:image/jpeg;base64,${base64Image}`;

      formData.append('file', {
        uri: uri,
        type: 'image/jpeg',
        name: 'invoice.jpg',
      } as any);

      formData.append('ocr_text', '');
      formData.append('document_type', 'invoice');

      console.log('📤 Calling Invoice API:', `${CONFIG.API_BASE_URL}/api/v1/documents/analyze`);

      const apiResponse = await fetch(`${CONFIG.API_BASE_URL}/api/v1/documents/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!apiResponse.ok) {
        const errorBody = await apiResponse.text();
        console.error('❌ Invoice API Error:', apiResponse.status, errorBody);
        throw new Error(`API Error: ${apiResponse.status}`);
      }

      const result = await apiResponse.json();
      console.log('✅ Invoice API Response:', JSON.stringify(result).substring(0, 300));

      return {
        mode: 'invoice',
        supplier: result.document?.supplier || result.supplier || 'Unknown Supplier',
        invoiceNumber: result.document?.invoice_number || result.invoice_number || 'Unknown Invoice',
        purchaseOrderSuggested: result.purchase_orders?.[0]?.po_number,
        serialNumbers: result.purchase_orders?.flatMap((po: any) => po.serial_numbers || []) || [],
        confidence: 85,
        detectedItems: result.purchase_orders?.map((po: any) => ({
          name: po.description || po.po_number,
          ref: po.po_number,
          quantity: po.serial_numbers?.length || 1,
          matched: po.cached,
          serialNumbers: (po.serial_numbers || []) as string[],
        })) || [],
        quantity: 1,
        ocrQuality: 85,
        extractedText: result.extracted_text?.substring(0, 500) || '',
      };
    } catch (error) {
      console.error('❌ Invoice analysis error:', error);
      throw error;
    }
  },

  /**
   * Analyze product image with YOLO11 for object detection
   */
  async analyzeProduct(base64Image: string): Promise<any> {
    try {
      const formData = new FormData();
      const uri = `data:image/jpeg;base64,${base64Image}`;

      formData.append('file', {
        uri: uri,
        type: 'image/jpeg',
        name: 'product.jpg',
      } as any);

      console.log('Calling YOLO API:', `${CONFIG.API_BASE_URL}/api/v1/products/detect`);

      const apiResponse = await fetch(`${CONFIG.API_BASE_URL}/api/v1/products/detect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        body: formData,
      });

      if (!apiResponse.ok) {
        console.error('YOLO API Error:', apiResponse.status);
        throw new Error(`API Error: ${apiResponse.status}`);
      }

      const result = await apiResponse.json();
      console.log('YOLO API Response:', result);

      return {
        mode: 'product',
        detectedObject: result.category || 'Unknown Device',
        category: result.category || 'Equipment',
        equipment_type: result.equipment_type || result.category,
        confidence: Math.round((result.confidence || result.detection_score || 0.5) * 100),
        reference: result.reference || 'EQUIP-001',
        boundingBox: {
          x: result.bounding_box?.x || 0,
          y: result.bounding_box?.y || 0,
          width: result.bounding_box?.width || 100,
          height: result.bounding_box?.height || 100,
          image_width: result.image_size?.width || 640,
          image_height: result.image_size?.height || 480,
        },
        detected_features: result.detected_features || [],
        processing_time_ms: result.processing_time_ms || 150,
        yolo_version: result.yolo_version || 'YOLO11s',
        class_id: result.class_id || 0,
        isRecognized: true,
        quantity: 1,
      };
    } catch (error) {
      console.error('Product analysis error:', error);
      throw error;
    }
  },

  /**
   * Analyze shipping label image.
   * Sends the raw image to the backend. Azure Computer Vision extracts OCR text server-side.
   */
  async analyzeLabel(base64Image: string, imageUri?: string): Promise<any> {
    try {
      console.log('📦 Starting label analysis (server-side Azure OCR)...');

      const formData = new FormData();
      const uri = imageUri ?? `data:image/jpeg;base64,${base64Image}`;

      formData.append('file', {
        uri: uri,
        type: 'image/jpeg',
        name: 'label.jpg',
      } as any);

      console.log('📤 Calling Label API:', `${CONFIG.API_BASE_URL}/api/v1/labels/analyze`);

      const apiResponse = await fetch(`${CONFIG.API_BASE_URL}/api/v1/labels/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!apiResponse.ok) {
        const errorBody = await apiResponse.text();
        console.error('❌ Label API Error:', apiResponse.status, errorBody);
        throw new Error(`API Error: ${apiResponse.status}`);
      }

      const result = await apiResponse.json();
      console.log('✅ Label API Response:', result);

      return {
        mode: 'label',
        productName: result.product_name || 'Unknown Product',
        articleNumber: result.article_number || 'N/A',
        reference: result.article_number || 'N/A',
        brand: result.brand || 'Generic',
        quantity: result.quantity || 1,
        poNumber: result.po_number,
        upc: result.upc,
        serialNumbers: result.serial_numbers && result.serial_numbers.length > 0 ? result.serial_numbers : (result.upc ? [result.upc] : []),
        matchedPO: result.po_number,
        confidence: result.confidence || 80,
        isMatch: true,
      };
    } catch (error) {
      console.error('❌ Label analysis error:', error);
      throw error;
    }
  },

  async launchFallbackScanner(options: CameraScanOptions): Promise<string | null> {
    const hasPermission = await this.requestPermission();
    if (!hasPermission) return null;

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets[0].base64) {
        return result.assets[0].base64;
      }
    } catch (error) {
      console.error('Camera fallback library selection error:', error);
    }
    return null;
  },
};
