"""Storage Service for handling file uploads"""
import os
import uuid
import aiofiles
from typing import Tuple, Optional
from fastapi import UploadFile
from PIL import Image
import io
from ..config import settings


class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        """Initialize storage service"""
        self.upload_dir = getattr(settings, 'UPLOAD_DIR', 'uploads')
        self.documents_dir = os.path.join(self.upload_dir, 'documents')
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure upload directories exist"""
        os.makedirs(self.documents_dir, exist_ok=True)
    
    async def save_document_image(self, file: UploadFile) -> Tuple[bool, str, Optional[str]]:
        """
        Save uploaded document image
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (success, file_path_or_error_message, original_filename)
        """
        try:
            # Validate file
            validation_result = await self._validate_file(file)
            if not validation_result[0]:
                return False, validation_result[1], None
            
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.documents_dir, unique_filename)
            
            # Save file
            content = await file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Verify file was saved correctly
            if not os.path.exists(file_path):
                return False, "File save verification failed", None
            
            # Return relative path for database storage
            relative_path = os.path.join('documents', unique_filename)
            
            return True, relative_path, file.filename
            
        except Exception as e:
            return False, f"File save error: {str(e)}", None
    
    async def _validate_file(self, file: UploadFile) -> Tuple[bool, str]:
        """Validate uploaded file"""
        try:
            # Check filename
            if not file.filename:
                return False, "No filename provided"
            
            # Check file extension
            file_extension = self._get_file_extension(file.filename)
            if file_extension.lower() not in self.allowed_extensions:
                return False, f"File type {file_extension} not allowed. Allowed: {', '.join(self.allowed_extensions)}"
            
            # Check file size
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            if len(content) > self.max_file_size:
                return False, f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
            
            if len(content) == 0:
                return False, "Empty file"
            
            # For image files, verify they can be opened
            if file_extension.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}:
                try:
                    image = Image.open(io.BytesIO(content))
                    image.verify()  # Verify it's a valid image
                except Exception:
                    return False, "Invalid image file"
            
            return True, "Valid file"
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        if not filename:
            return ""
        
        return os.path.splitext(filename)[1].lower()
    
    def get_full_path(self, relative_path: str) -> str:
        """Get full file system path from relative path"""
        return os.path.join(self.upload_dir, relative_path)
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists"""
        full_path = self.get_full_path(relative_path)
        return os.path.exists(full_path)
    
    async def delete_file(self, relative_path: str) -> bool:
        """Delete file from storage"""
        try:
            full_path = self.get_full_path(relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False
    
    def get_file_info(self, relative_path: str) -> Optional[dict]:
        """Get file information"""
        try:
            full_path = self.get_full_path(relative_path)
            if not os.path.exists(full_path):
                return None
            
            stat = os.stat(full_path)
            
            return {
                "path": relative_path,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "exists": True
            }
        except Exception:
            return None


# Global instance
storage_service = StorageService()