"""
Azure Computer Vision OCR Service
Real-time dynamic OCR extraction from image files using Azure Read API.
"""
import time
import requests
from typing import Dict, Any, Optional
from app.config import settings


class AzureOCRService:
    """Service to perform dynamic OCR using Azure Computer Vision Read API"""

    def __init__(self):
        self.endpoint = "https://stockit-foundry.cognitiveservices.azure.com"
        self.api_key = settings.AZURE_AI_API_KEY

    def extract_text_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """Send image bytes to Azure Computer Vision Read API and poll for extracted text."""
        if not self.api_key or not image_bytes:
            return None

        url = f"{self.endpoint}/vision/v3.2/read/analyze"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/octet-stream"
        }

        try:
            res = requests.post(url, headers=headers, data=image_bytes, timeout=10)
            if res.status_code != 202:
                print(f"⚠️ Azure OCR POST failed ({res.status_code}): {res.text}")
                return None

            operation_url = res.headers.get("Operation-Location")
            if not operation_url:
                return None

            # Poll operation result (up to 10 seconds)
            get_headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            for _ in range(20):
                time.sleep(0.5)
                poll_res = requests.get(operation_url, headers=get_headers, timeout=5)
                if poll_res.status_code == 200:
                    data = poll_res.json()
                    status = data.get("status")
                    if status == "succeeded":
                        lines = []
                        read_results = data.get("analyzeResult", {}).get("readResults", [])
                        for page in read_results:
                            for line in page.get("lines", []):
                                lines.append(line.get("text", ""))
                        extracted = "\n".join(lines)
                        print(f"✅ Azure OCR extracted {len(lines)} lines ({len(extracted)} chars)")
                        return extracted
                    elif status in ("failed", "canceled"):
                        print(f"❌ Azure OCR operation {status}")
                        return None
            return None
        except Exception as e:
            print(f"⚠️ Azure OCR exception: {e}")
            return None


azure_ocr_service = AzureOCRService()
