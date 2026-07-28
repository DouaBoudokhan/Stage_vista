import React, { useState, useEffect } from 'react';
import { StyleSheet, View, TouchableOpacity, Alert } from 'react-native';
import { Text, Portal, Modal, Surface } from 'react-native-paper';
import { Colors, Spacing, BorderRadius } from '../constants/theme';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { CameraService } from '../services/camera';

interface CameraHUDProps {
  visible: boolean;
  onClose: () => void;
  onScanResult: (result: any) => void;
  mode: 'product' | 'invoice' | 'label';
}

export const CameraHUD: React.FC<CameraHUDProps> = ({
  visible,
  onClose,
  onScanResult,
  mode,
}) => {
  const [isScanning, setIsScanning] = useState(false);

  const getModeConfig = () => {
    switch (mode) {
      case 'product':
        return {
          title: 'Scan Product',
          icon: 'laptop',
          description: 'Point camera at the actual equipment to identify it',
        };
      case 'invoice':
        return {
          title: 'Scan Invoice', 
          icon: 'file-document',
          description: 'Point camera at the commercial invoice document',
        };
      case 'label':
        return {
          title: 'Scan Shipping Label',
          icon: 'barcode',
          description: 'Point camera at the shipping label on the box',
        };
    }
  };

  const config = getModeConfig();

  const handleTakePhoto = async () => {
    try {
      setIsScanning(true);
      
      // Use the camera service to take a photo
      const base64Image = await CameraService.takePhoto();
      
      if (base64Image) {
        if (mode === 'invoice') {
          // For invoice mode, use the real backend API
          try {
            const analysisResult = await CameraService.analyzeInvoice(base64Image);
            
            // Convert backend response to expected format
            const formattedResult = {
              mode: 'invoice',
              supplier: analysisResult.document?.supplier || 'Unknown Supplier',
              invoiceNumber: analysisResult.document?.invoice_number || 'Unknown Invoice',
              purchaseOrderSuggested: analysisResult.purchase_orders?.[0]?.po_number,
              confidence: 95,
              detectedItems: analysisResult.purchase_orders?.map((po: any) => ({
                name: po.description || po.po_number,
                ref: po.po_number,
                quantity: po.serial_numbers?.length || 1,
                matched: po.cached
              })) || [],
              quantity: 1
            };
            
            onScanResult(formattedResult);
          } catch (error) {
            Alert.alert('Analysis Failed', 'Could not analyze invoice. Using mock data for demo.');
            // Fallback to mock data
            const mockData = CameraService.getSimulatedPreset('invoice_vista');
            onScanResult(mockData);
          }
        } else {
          // For product and label modes, use mock data for now
          const mockData = CameraService.getSimulatedPreset(
            mode === 'product' ? 'dell_laptop' : 'label_shipping_dell'
          );
          onScanResult(mockData);
        }
      }
      
      setIsScanning(false);
    } catch (error) {
      setIsScanning(false);
      Alert.alert('Camera Error', 'Failed to take photo. Please try again.');
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
            <Text style={styles.headerTitle}>{config.title}</Text>
            <View style={styles.placeholder} />
          </View>

          {/* Camera Viewfinder Area */}
          <View style={styles.viewfinderContainer}>
            <View style={styles.viewfinderFrame}>
              {/* Corner brackets */}
              <View style={[styles.corner, styles.topLeft]} />
              <View style={[styles.corner, styles.topRight]} />
              <View style={[styles.corner, styles.bottomLeft]} />
              <View style={[styles.corner, styles.bottomRight]} />
              
              {/* Center content */}
              <View style={styles.centerContent}>
                <MaterialCommunityIcons 
                  name={config.icon} 
                  size={48} 
                  color="rgba(255,255,255,0.7)" 
                />
                <Text style={styles.instructionText}>{config.description}</Text>
              </View>
            </View>
          </View>

          {/* Bottom Controls */}
          <View style={styles.controls}>
            <Text style={styles.instructionTitle}>Position the {mode} in the frame above</Text>
            
            <TouchableOpacity 
              style={[styles.captureButton, isScanning && styles.captureButtonScanning]} 
              onPress={handleTakePhoto}
              disabled={isScanning}
            >
              {isScanning ? (
                <MaterialCommunityIcons name="loading" size={32} color="#FFF" />
              ) : (
                <MaterialCommunityIcons name="camera" size={32} color="#FFF" />
              )}
            </TouchableOpacity>
            
            <Text style={styles.captureText}>
              {isScanning ? 'Processing...' : 'Tap to Capture'}
            </Text>
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
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  closeButton: {
    padding: Spacing.sm,
  },
  headerTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  placeholder: {
    width: 40, // Same width as close button for centering
  },
  viewfinderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  viewfinderFrame: {
    width: 300,
    height: 300,
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  corner: {
    position: 'absolute',
    width: 30,
    height: 30,
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderColor: Colors.primaryLight,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderColor: Colors.primaryLight,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderColor: Colors.primaryLight,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
    borderColor: Colors.primaryLight,
  },
  centerContent: {
    alignItems: 'center',
  },
  instructionText: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 14,
    textAlign: 'center',
    marginTop: Spacing.md,
    paddingHorizontal: Spacing.lg,
  },
  controls: {
    alignItems: 'center',
    paddingBottom: Spacing.xl + 20,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  instructionTitle: {
    color: '#FFF',
    fontSize: 16,
    marginBottom: Spacing.lg,
    textAlign: 'center',
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  captureButtonScanning: {
    backgroundColor: Colors.textSecondary,
  },
  captureText: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 14,
  },
});
