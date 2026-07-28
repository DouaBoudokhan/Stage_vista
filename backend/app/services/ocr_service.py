"""OCR Service for Stock Entry Workflow"""
import re
import base64
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from io import BytesIO
import pytesseract
from ..schemas.stock_entry import PurchaseOrderInfo


class OCRService:
    """OCR Service using Google ML Kit (simulated with Tesseract for now)"""
    
    def __init__(self):
        """Initialize OCR service"""
        # In production, this would initialize Google ML Kit
        # For now, we'll use Tesseract as a fallback
        pass
    
    def extract_text_from_image(self, image_base64: str) -> Tuple[bool, str]:
        """
        Extract text from image using OCR
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            Tuple of (success, extracted_text)
        """
        try:
            # Decode base64 to image
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract (Google ML Kit simulation)
            extracted_text = pytesseract.image_to_string(image, lang='eng+fra')
            
            if not extracted_text.strip():
                return False, "No text found in image"
            
            return True, extracted_text
            
        except Exception as e:
            return False, f"OCR failed: {str(e)}"
    
    def process_delivery_document(self, image_base64: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process delivery document (Step 2)
        Extract supplier, document number, and Purchase Orders
        
        Returns:
            Tuple of (success, result_dict)
        """
        success, text = self.extract_text_from_image(image_base64)
        
        if not success:
            return False, {"message": text}
        
        try:
            # Extract supplier
            supplier = self._extract_supplier(text)
            
            # Extract document number
            document_number = self._extract_document_number(text)
            
            # Extract Purchase Orders
            purchase_orders = self._extract_purchase_orders(text)
            
            if not purchase_orders:
                return False, {
                    "message": "No Purchase Orders found in document",
                    "extracted_text": text
                }
            
            return True, {
                "supplier": supplier,
                "document_number": document_number,
                "purchase_orders": purchase_orders,
                "extracted_text": text,
                "message": f"Found {len(purchase_orders)} Purchase Orders"
            }
            
        except Exception as e:
            return False, {
                "message": f"Failed to process document: {str(e)}",
                "extracted_text": text
            }
    
    def process_package_label(self, image_base64: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process package label (Step 4)
        Extract brand, product name, article number, quantity, and PO
        
        Returns:
            Tuple of (success, result_dict)
        """
        success, text = self.extract_text_from_image(image_base64)
        
        if not success:
            return False, {"message": text}
        
        try:
            # Extract package information
            brand = self._extract_brand(text)
            product_name = self._extract_product_name(text)
            article_number = self._extract_article_number(text)
            quantity = self._extract_quantity(text)
            po_on_package = self._extract_po_from_package(text)
            
            # Validate required fields
            if not brand:
                return False, {"message": "Brand not found on package label", "extracted_text": text}
            if not product_name:
                return False, {"message": "Product name not found on package label", "extracted_text": text}
            if not article_number:
                return False, {"message": "Article number not found on package label", "extracted_text": text}
            if not quantity or quantity <= 0:
                return False, {"message": "Valid quantity not found on package label", "extracted_text": text}
            
            return True, {
                "brand": brand,
                "product_name": product_name,
                "article_number": article_number,
                "quantity": quantity,
                "po_on_package": po_on_package,
                "extracted_text": text,
                "message": f"Successfully extracted package information for {product_name}"
            }
            
        except Exception as e:
            return False, {
                "message": f"Failed to process package label: {str(e)}",
                "extracted_text": text
            }
    
    def _extract_supplier(self, text: str) -> str:
        """Extract supplier name from document text"""
        lines = text.split('\n')
        
        # Common supplier patterns
        supplier_keywords = ['supplier', 'vendor', 'from', 'expediteur', 'fournisseur']
        
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line_lower = line.lower().strip()
            
            # Look for supplier indicators
            for keyword in supplier_keywords:
                if keyword in line_lower:
                    # Try to extract supplier name from same line or next line
                    supplier_line = line.strip()
                    if ':' in supplier_line:
                        supplier = supplier_line.split(':', 1)[1].strip()
                        if supplier:
                            return supplier
                    
                    # Check next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and len(next_line) > 2:
                            return next_line
        
        # Fallback: look for company patterns (capital letters, common suffixes)
        for line in lines[:15]:
            line = line.strip()
            if re.match(r'^[A-Z][A-Z\s&.,]{3,}(?:Ltd|LLC|Inc|GmbH|SAS|SA|Corp).*$', line):
                return line
        
        return "Unknown Supplier"
    
    def _extract_document_number(self, text: str) -> str:
        """Extract document number from text"""
        # Common document number patterns
        patterns = [
            r'(?:Invoice|Facture|Doc|Document)\s*[#:]\s*([A-Z0-9-]+)',
            r'(?:N°|No\.?|Number)\s*[:\s]*([A-Z0-9-]+)',
            r'([A-Z]{2,}\d{6,})',  # Pattern like ABC123456
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown Document"
    
    def _extract_purchase_orders(self, text: str) -> List[PurchaseOrderInfo]:
        """Extract Purchase Orders from document text"""
        purchase_orders = []
        lines = text.split('\n')
        
        # PO patterns
        po_pattern = r'(?:PO|Purchase Order|Commande)\s*[#:]?\s*(\d{7,})'
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for PO number
            po_match = re.search(po_pattern, line, re.IGNORECASE)
            if po_match:
                po_number = po_match.group(1)
                
                # Extract description and serial numbers from following lines
                description_lines = []
                serial_numbers = []
                
                # Look ahead for product info (next 5 lines)
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    
                    # Stop if we hit another PO
                    if re.search(po_pattern, next_line, re.IGNORECASE):
                        break
                    
                    # Check for serial number patterns
                    serial_match = re.search(r'(?:SN|Serial|S/N)[:\s]*([A-Z0-9]{8,})', next_line, re.IGNORECASE)
                    if serial_match:
                        serial_numbers.append(serial_match.group(1))
                    
                    # Collect description lines (non-empty, non-numeric only)
                    if next_line and not re.match(r'^\d+[\.,]?\d*$', next_line) and len(next_line) > 3:
                        description_lines.append(next_line)
                
                # Create description from collected lines
                description = ' - '.join(description_lines[:2]) if description_lines else f"PO {po_number}"
                
                purchase_orders.append(PurchaseOrderInfo(
                    po_number=po_number,
                    description=description,
                    serial_numbers=serial_numbers
                ))
            
            i += 1
        
        return purchase_orders
    
    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand from package label"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Common brand patterns - usually at the top
        for line in lines[:5]:
            # Look for all-caps brands or known patterns
            if re.match(r'^[A-Z][A-Z\s&]{2,15}$', line):
                return line
            
            # Known IT brands
            known_brands = ['EPOS', 'LOGITECH', 'DELL', 'HP', 'LENOVO', 'APPLE', 'MICROSOFT', 
                          'CISCO', 'ASUS', 'ACER', 'SAMSUNG', 'LG', 'SONY', 'CANON', 'EPSON']
            
            for brand in known_brands:
                if brand.lower() in line.lower():
                    return brand
        
        # Fallback: first meaningful line
        if lines:
            return lines[0]
        
        return None
    
    def _extract_product_name(self, text: str) -> Optional[str]:
        """Extract product name from package label"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for product name patterns (usually longer descriptive lines)
        for line in lines:
            # Skip very short lines and pure numbers
            if len(line) < 5 or re.match(r'^\d+[\.,]?\d*$', line):
                continue
            
            # Product names often contain model info, specifications
            if any(keyword in line.lower() for keyword in ['usb', 'pro', 'max', 'stereo', 'wireless', 'bluetooth']):
                return line
            
            # Look for mixed alphanumeric with spaces (typical product naming)
            if re.search(r'[A-Za-z]+\s+\d+|[A-Za-z]+\s+[A-Za-z]+', line):
                return line
        
        # Fallback: longest non-brand line
        non_brand_lines = [line for line in lines if not re.match(r'^[A-Z]{3,}$', line)]
        if non_brand_lines:
            return max(non_brand_lines, key=len)
        
        return None
    
    def _extract_article_number(self, text: str) -> Optional[str]:
        """Extract article number from package label"""
        # Common article number patterns
        patterns = [
            r'(?:Article|Art|Item|Ref|P/N)[#:\s]*([A-Z0-9-]{4,})',
            r'^(\d{6,})$',  # Pure numeric codes
            r'^([A-Z]{2,}\d{4,})$',  # Alphanumeric codes
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_quantity(self, text: str) -> Optional[int]:
        """Extract quantity from package label"""
        # Quantity patterns
        patterns = [
            r'(?:Qty|Quantity|Quantité)[:\s]*(\d+)',
            r'(?:Pcs|Pieces|Pièces)[:\s]*(\d+)',
            r'^(\d{1,3})$',  # Single number on its own line
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_po_from_package(self, text: str) -> Optional[str]:
        """Extract PO number from package label"""
        # PO patterns on package
        patterns = [
            r'(?:PO|Purchase Order)[#:\s]*(\d+)',
            r'(?:Commande)[#:\s]*(\d+)',
            r'^(\d{4,8})$',  # Simple number that could be PO
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1)
        
        return None


# Global instance
ocr_service = OCRService()