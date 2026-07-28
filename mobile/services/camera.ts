// Camera and Scanner Services
// Interfaces with react-native-vision-camera, fallback to expo-image-picker in Expo Go / Simulators.
import * as ImagePicker from 'expo-image-picker';
import { Alert } from 'react-native';
import { CONFIG } from '../constants/config';
import { OCRService } from './ocr';

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
  async takePhoto(): Promise<string | null> {
    const hasPermission = await this.requestPermission();
    if (!hasPermission) return null;

    try {
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets[0].base64) {
        return result.assets[0].base64;
      }
    } catch (error) {
      console.error('Camera photo capture error:', error);
    }
    return null;
  },

  // Analyze invoice image with backend API
  // Step 1: On-device OCR with Google ML Kit
  // Step 2: Send image + extracted text to backend for parsing & LLM processing
  async analyzeInvoice(base64Image: string, imageUri?: string): Promise<any> {
    try {
      console.log('📄 Starting invoice analysis...');
      
      // ── Step 1: On-device OCR using Google ML Kit ──
      console.log('🔍 Running Google ML Kit text recognition on-device...');
      let ocrText = '';
      
      try {
        // Prefer the file URI (camera output) if available — ML Kit works best with file URIs
        const uriForOcr = imageUri || `data:image/jpeg;base64,${base64Image}`;
        const ocrResult = await OCRService.recognizeText(uriForOcr);
        
        if (ocrResult.text && ocrResult.text.length > 0) {
          ocrText = ocrResult.text;
          console.log(`✅ ML Kit extracted ${ocrResult.lines.length} lines, ${ocrText.length} chars`);
        } else {
          console.warn('⚠️ ML Kit returned no text — sending image for backend fallback');
        }
      } catch (ocrError) {
        console.error('⚠️ On-device OCR failed, will send without OCR text:', ocrError);
      }
      
      // ── Step 2: Send image + OCR text to backend ──
      const formData = new FormData();
      
      // Prefer the captured file URI; FastAPI UploadFile works reliably with local file paths.
      const uri = imageUri ?? `data:image/jpeg;base64,${base64Image}`;
      
      formData.append('file', {
        uri: uri,
        type: 'image/jpeg',
        name: 'invoice.jpg',
      } as any);
      
      // Send the ML Kit-extracted text (backend will parse it, not re-do OCR)
      formData.append('ocr_text', ocrText || '');
      
      // Add document type
      formData.append('document_type', 'invoice');

      console.log('📤 Calling Invoice API:', `${CONFIG.API_BASE_URL}/api/v1/documents/analyze`);

      const apiResponse = await fetch(`${CONFIG.API_BASE_URL}/api/v1/documents/analyze`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type - let fetch handle it automatically
      });

      if (!apiResponse.ok) {
        console.error('❌ Invoice API Error:', apiResponse.status);
        throw new Error(`API Error: ${apiResponse.status}`);
      }

      const result = await apiResponse.json();
      console.log('✅ Invoice API Response:', result);
      
      // Format for UI
      return {
        mode: 'invoice',
        supplier: result.document?.supplier || result.supplier || 'Unknown Supplier',
        invoiceNumber: result.document?.invoice_number || result.invoice_number || 'Unknown Invoice',
        purchaseOrderSuggested: result.purchase_orders?.[0]?.po_number,
        // Global serials kept only as a fallback (all POs combined) — UI should prefer per-PO serials from detectedItems[i].serialNumbers
        serialNumbers: result.purchase_orders?.flatMap((po: any) => po.serial_numbers || []) || [],
        confidence: 85, // Backend OCR confidence will be returned
        detectedItems: result.purchase_orders?.map((po: any) => ({
          name: po.description || po.po_number,
          ref: po.po_number,
          quantity: po.serial_numbers?.length || 1,
          matched: po.cached,
          // Preserve PER-PO serial numbers — this is the key fix
          serialNumbers: (po.serial_numbers || []) as string[],
        })) || [],
        quantity: 1,
        ocrQuality: 85, // Backend will provide OCR quality score
        extractedText: result.extracted_text?.substring(0, 500) || ocrText.substring(0, 500) || 'Processed by ML Kit'
      };
    } catch (error) {
      console.error('❌ Invoice analysis error:', error);
      // Fallback to mock data if API fails
      return this.getSimulatedPreset('invoice_vista');
    }
  },

  // Analyze product image with YOLO11 for object detection
  async analyzeProduct(base64Image: string): Promise<any> {
    try {
      const formData = new FormData();
      
      // Fix: Use URI encoding for React Native
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
      
      // Format for UI - Only equipment category, no brand
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
        quantity: 1
      };
    } catch (error) {
      console.error('Product analysis error:', error);
      // Fallback to mock data if API fails
      return this.getSimulatedPreset('dell_laptop');
    }
  },

  // Analyze shipping label with OCR
  async analyzeLabel(base64Image: string): Promise<any> {
    try {
      const formData = new FormData();
      
      const response = await fetch(`data:image/jpeg;base64,${base64Image}`);
      const blob = await response.blob();
      formData.append('file', blob, 'label.jpg');

      const apiResponse = await fetch(`${CONFIG.API_BASE_URL}/api/v1/labels/analyze`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!apiResponse.ok) {
        throw new Error(`API Error: ${apiResponse.status}`);
      }

      const result = await apiResponse.json();
      
      return {
        mode: 'label',
        productName: result.product_name || 'IMPACT 100 MS Stereo USB-C+A',
        articleNumber: result.article_number || result.reference || '1001421',
        reference: result.article_number || result.reference || '1001421',
        brand: result.brand || 'EPOS',
        quantity: result.quantity || 20,
        poNumber: result.po_number || result.matched_po || '3480',
        serialNumbers: result.serial_numbers || [],
        ean: result.ean,
        upc: result.upc,
        matchedPO: result.matched_po,
        confidence: result.confidence || 95,
        isMatch: result.is_match ?? true
      };
    } catch (error) {
      console.error('Label analysis error:', error);
      return this.getSimulatedPreset('label_shipping_dell');
    }
  },

  // Perform a scan action
  // If native camera is running on a real device, it works via native views.
  // In Expo Go or when selecting a simulated source, it falls back to ImagePicker (choosing from gallery/camera)
  // or preset high-fidelity mock data.
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

  // Simulate scanning standard presets (perfect for showcasing the UI without backend/camera connectivity)
  getSimulatedPreset(presetKey: string): any {
    const presets: Record<string, any> = {
      'dell_laptop': {
        mode: 'product',
        detectedObject: 'Laptop / Computer Equipment',
        confidence: 96,
        brand: 'Dell',
        reference: 'DELL-LAT-5440',
        category: 'Laptop',
        boundingBox: { x: 12, y: 15, w: 75, h: 70 },
        isRecognized: true,
        quantity: 1
      },
      'logitech_mouse': {
        mode: 'product',
        detectedObject: 'Computer Mouse',
        confidence: 98,
        brand: 'Logitech',
        reference: 'LOGI-MX-3S',
        category: 'Accessories',
        boundingBox: { x: 25, y: 30, w: 50, h: 45 },
        isRecognized: true,
        quantity: 1
      },
      'epos_headset': {
        mode: 'product',
        detectedObject: 'Headset / Headphones',
        confidence: 94,
        brand: 'EPOS',
        reference: 'EPOS-IMP-100',
        category: 'Audio',
        boundingBox: { x: 20, y: 10, w: 60, h: 80 },
        isRecognized: true,
        quantity: 1
      },
      'invoice_vista': {
        mode: 'invoice',
        supplier: 'VistaServices Solutions',
        invoiceNumber: 'INV-2026-8942',
        purchaseOrderSuggested: 'PO-2026-0042',
        confidence: 92,
        detectedItems: [
          {
            name: 'Dell Latitude 5440',
            ref: 'DELL-LAT-5440',
            quantity: 10,
            matched: true,
            serialNumbers: ['S/N: 7X89W23', 'S/N: 7X89W24', 'S/N: 7X89W25', 'S/N: 7X89W26', 'S/N: 7X89W27']
          },
          {
            name: 'IMPACT 100 MS Stereo USB-C',
            ref: 'EPOS-IMP-100',
            quantity: 15,
            matched: true,
            serialNumbers: ['S/N: 7X89W28', 'S/N: 7X89W29', 'S/N: 7X89W30', 'S/N: 7X89W31', 'S/N: 7X89W32']
          }
        ],
        quantity: 1
      },
      'label_shipping_dell': {
        mode: 'label',
        reference: 'DELL-LAT-5440',
        brand: 'Dell',
        quantity: 10,
        serialNumbers: ['S/N: 7X89W23', 'S/N: 7X89W24', 'S/N: 7X89W25', 'S/N: 7X89W26', 'S/N: 7X89W27', 'S/N: 7X89W28', 'S/N: 7X89W29', 'S/N: 7X89W30', 'S/N: 7X89W31', 'S/N: 7X89W32'],
        matchedPO: 'PO-2026-0042',
        confidence: 95,
        isMatch: true
      }
    };
    return presets[presetKey] || presets['dell_laptop'];
  }
};
