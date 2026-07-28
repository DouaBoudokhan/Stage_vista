import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Alert, Image } from 'react-native';
import { Portal, Modal } from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { CameraService } from '../services/camera';

interface YOLOCameraHUDProps {
  visible: boolean;
  onClose: () => void;
  onCapture: (result: any) => void;
  mode: 'product' | 'invoice' | 'label';
}

export const YOLOCameraHUD: React.FC<YOLOCameraHUDProps> = ({
  visible,
  onClose,
  onCapture,
  mode,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [capturedImageUri, setCapturedImageUri] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  
  useEffect(() => {
    if (visible) {
      console.log('🎥 Camera HUD opened for mode:', mode);
      // Reset state when opening
      setCapturedImageUri(null);
      setAnalysisResult(null);
      // Auto-open camera when component becomes visible
      handleTakePhoto();
    }
  }, [visible]);

  const handleTakePhoto = async () => {
    if (isProcessing) return;
    
    console.log('📷 Opening camera...');
    setIsProcessing(true);
    
    try {
      // Request camera permissions
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Required', 'Camera permission is required to scan products');
        onClose();
        return;
      }

      // Launch camera
      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const asset = result.assets[0];
        console.log('📸 Photo taken successfully');
        
        // Store the image URI for display
        setCapturedImageUri(asset.uri);
        
        if (asset.base64) {
          console.log('📤 Sending to YOLO API...');
          
          let analysisResult;
          if (mode === 'product') {
            analysisResult = await CameraService.analyzeProduct(asset.base64);
            console.log('🎯 YOLO Result:', analysisResult.category, analysisResult.confidence);
          } else if (mode === 'invoice') {
            // Pass both base64 and URI for OCR processing
            analysisResult = await CameraService.analyzeInvoice(asset.base64, asset.uri);
          } else if (mode === 'label') {
            analysisResult = await CameraService.analyzeLabel(asset.base64);
          }

          if (analysisResult) {
            // Store analysis result with image info
            setAnalysisResult({
              ...analysisResult,
              capturedImageUri: asset.uri,
              imageWidth: asset.width || 640,
              imageHeight: asset.height || 480
            });
          }
        }
      } else {
        console.log('📷 Camera cancelled');
        onClose();
      }
    } catch (error) {
      console.error('❌ Camera error:', error);
      Alert.alert('Camera Error', 'Could not open camera. Please try again.');
      onClose();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUseResult = () => {
    if (analysisResult) {
      onCapture(analysisResult);
    }
  };

  const handleRetakePhoto = () => {
    setCapturedImageUri(null);
    setAnalysisResult(null);
    handleTakePhoto();
  };

  const getModeTitle = () => {
    switch (mode) {
      case 'product': return 'YOLO Product Detection';
      case 'invoice': return 'Invoice Analysis';
      case 'label': return 'Label Scanning';
      default: return 'Camera';
    }
  };

  return (
    <Portal>
      <Modal visible={visible} onDismiss={onClose} contentContainerStyle={styles.modal}>
        <View style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <MaterialCommunityIcons name="close" size={24} color="#FFF" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>{getModeTitle()}</Text>
            <View style={styles.headerSpacer} />
          </View>

          {/* Content */}
          <View style={styles.content}>
            {isProcessing ? (
              <View style={styles.loadingContainer}>
                <MaterialCommunityIcons name="camera" size={64} color={Colors.primaryLight} />
                <Text style={styles.loadingTitle}>
                  {capturedImageUri && mode === 'invoice' 
                    ? 'Processing Invoice...' 
                    : capturedImageUri 
                      ? 'Analyzing Image...' 
                      : 'Opening Camera...'
                  }
                </Text>
                <Text style={styles.loadingSubtitle}>
                  {capturedImageUri && mode === 'invoice'
                    ? 'Backend extracting text and analyzing invoice...'
                    : capturedImageUri 
                      ? 'YOLO processing in progress...'
                      : mode === 'product' 
                        ? 'Point at equipment for YOLO detection' 
                        : `Position ${mode} in frame`
                  }
                </Text>
                <View style={styles.loadingSpinner}>
                  <MaterialCommunityIcons name="loading" size={32} color="#FFF" />
                </View>
              </View>
            ) : capturedImageUri && analysisResult ? (
              <View style={styles.resultContainer}>
                {/* Captured Image with YOLO Bounding Boxes */}
                <View style={styles.imageContainer}>
                  <Image source={{ uri: capturedImageUri }} style={styles.capturedImage} />
                  
                  {/* YOLO Bounding Box Overlay */}
                  {analysisResult.boundingBox && (
                    <View 
                      style={[
                        styles.boundingBox,
                        {
                          left: `${(analysisResult.boundingBox.x / analysisResult.imageWidth) * 100}%`,
                          top: `${(analysisResult.boundingBox.y / analysisResult.imageHeight) * 100}%`,
                          width: `${(analysisResult.boundingBox.width / analysisResult.imageWidth) * 100}%`,
                          height: `${(analysisResult.boundingBox.height / analysisResult.imageHeight) * 100}%`,
                        }
                      ]}
                    >
                      <View style={styles.confidenceLabel}>
                        <Text style={styles.confidenceText}>
                          {analysisResult.category} {analysisResult.confidence}%
                        </Text>
                      </View>
                    </View>
                  )}
                </View>

                {/* Analysis Results */}
                <View style={styles.analysisCard}>
                  <View style={styles.detectionHeader}>
                    <MaterialCommunityIcons name="check-circle" size={20} color={Colors.success} />
                    <Text style={styles.detectionTitle}>
                      {mode === 'product' ? 'Detection Complete' : 
                       mode === 'invoice' ? 'OCR & Analysis Complete' : 
                       'Analysis Complete'}
                    </Text>
                  </View>
                  
                  {mode === 'product' && (
                    <>
                      <Text style={styles.detectedItem}>
                        {analysisResult.category?.toUpperCase()} - {analysisResult.confidence}% confidence
                      </Text>
                      
                      {analysisResult.equipment_type && (
                        <Text style={styles.detectedType}>Type: {analysisResult.equipment_type}</Text>
                      )}
                    </>
                  )}
                  
                  {mode === 'invoice' && (
                    <>
                      <Text style={styles.detectedItem}>
                        {analysisResult.supplier} - Invoice: {analysisResult.invoiceNumber}
                      </Text>
                      
                      {analysisResult.ocrQuality && (
                        <Text style={styles.detectedType}>
                          OCR Quality: {analysisResult.ocrQuality}%
                        </Text>
                      )}
                      
                      {analysisResult.purchaseOrderSuggested && (
                        <Text style={styles.detectedType}>
                          Suggested PO: {analysisResult.purchaseOrderSuggested}
                        </Text>
                      )}
                    </>
                  )}
                  
                  {mode === 'label' && (
                    <>
                      <Text style={styles.detectedItem}>
                        {analysisResult.reference} - Qty: {analysisResult.quantity}
                      </Text>
                      
                      <Text style={styles.detectedType}>Brand: {analysisResult.brand}</Text>
                    </>
                  )}
                </View>

                {/* Action Buttons */}
                <View style={styles.actionButtonsRow}>
                  <TouchableOpacity style={styles.retakeButton} onPress={handleRetakePhoto}>
                    <MaterialCommunityIcons name="camera-retake" size={20} color="#666" />
                    <Text style={styles.retakeText}>Retake</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity style={styles.useResultButton} onPress={handleUseResult}>
                    <MaterialCommunityIcons name="check" size={20} color="#FFF" />
                    <Text style={styles.useResultText}>Use Result</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <View style={styles.idleContainer}>
                <MaterialCommunityIcons name="camera-outline" size={64} color="#666" />
                <Text style={styles.idleTitle}>Camera Ready</Text>
                <Text style={styles.idleSubtitle}>Tap below to open camera</Text>
                
                <TouchableOpacity style={styles.openCameraButton} onPress={handleTakePhoto}>
                  <MaterialCommunityIcons name="camera" size={24} color="#FFF" />
                  <Text style={styles.openCameraText}>Open Camera</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </Portal>
  );
};

const styles = StyleSheet.create({
  modal: {
    margin: 0,
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.xl + 20,
    paddingBottom: Spacing.md,
    backgroundColor: 'rgba(0,0,0,0.9)',
  },
  closeButton: {
    padding: Spacing.sm,
  },
  headerTitle: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  headerSpacer: {
    width: 40,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  loadingContainer: {
    alignItems: 'center',
  },
  loadingTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: Spacing.lg,
  },
  loadingSubtitle: {
    color: '#AAA',
    fontSize: 14,
    textAlign: 'center',
    marginTop: Spacing.sm,
    marginBottom: Spacing.xl,
  },
  loadingSpinner: {
    marginTop: Spacing.lg,
  },
  idleContainer: {
    alignItems: 'center',
  },
  idleTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: Spacing.lg,
  },
  idleSubtitle: {
    color: '#AAA',
    fontSize: 14,
    marginTop: Spacing.sm,
    marginBottom: Spacing.xl,
  },
  openCameraButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
  },
  openCameraText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: Spacing.sm,
  },
  resultContainer: {
    flex: 1,
    width: '100%',
    alignItems: 'center',
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
    maxWidth: 300,
    aspectRatio: 1,
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
    marginBottom: Spacing.lg,
  },
  capturedImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  boundingBox: {
    position: 'absolute',
    borderWidth: 3,
    borderColor: Colors.success,
    backgroundColor: 'rgba(34, 197, 94, 0.1)',
  },
  confidenceLabel: {
    position: 'absolute',
    top: -25,
    left: 0,
    backgroundColor: Colors.success,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  confidenceText: {
    color: '#FFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  analysisCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    width: '100%',
    maxWidth: 300,
    marginBottom: Spacing.lg,
  },
  detectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  detectionTitle: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: Spacing.sm,
  },
  detectedItem: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: Spacing.xs,
  },
  detectedType: {
    color: '#AAA',
    fontSize: 12,
  },
  actionButtonsRow: {
    flexDirection: 'row',
    width: '100%',
    maxWidth: 300,
    justifyContent: 'space-between',
  },
  retakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    flex: 0.45,
    justifyContent: 'center',
  },
  retakeText: {
    color: '#AAA',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: Spacing.xs,
  },
  useResultButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.success,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    flex: 0.45,
    justifyContent: 'center',
  },
  useResultText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: Spacing.xs,
  },
});