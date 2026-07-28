"""LLM Service for Azure AI Foundry Integration"""
import json
import asyncio
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import aiohttp
from ..config import settings


class LLMService(ABC):
    """Abstract base class for LLM services - allows easy switching between providers"""
    
    @abstractmethod
    async def generate_description(self, po_number: str, po_text: str) -> Dict[str, Any]:
        """Generate concise description for Purchase Order content"""
        pass


class AzureAIFoundryService(LLMService):
    """Azure AI Foundry LLM Service using Llama-3.3-70B-Instruct"""
    
    def __init__(self):
        """Initialize Azure AI Foundry service"""
        # Use dedicated LLM endpoint (Llama 3.3)
        self.endpoint = getattr(settings, 'AZURE_LLM_ENDPOINT', None) or settings.AZURE_AI_ENDPOINT
        self.api_key = getattr(settings, 'AZURE_AI_API_KEY', None)
        self.model_name = "Llama-3.3-70B-Instruct"
        self.max_tokens = 100  # Keep descriptions concise (30 words max)
        self.temperature = 0.1  # Low temperature for consistent, factual output
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure AI Foundry credentials not configured")
    
    async def generate_description(self, po_number: str, po_text: str) -> Dict[str, Any]:
        """
        Generate concise description for Purchase Order using Azure AI Foundry
        
        Args:
            po_number: Purchase Order number
            po_text: Clean text content for this PO
            
        Returns:
            Dict with 'description' or error details
        """
        try:
            # Create focused prompt for description generation
            prompt = self._build_prompt(po_number, po_text)
            
            # Call Azure AI Foundry API
            response_data = await self._call_azure_api(prompt)
            
            # Parse and validate response
            description = self._parse_response(response_data)
            
            # Validate description length (max 30 words)
            word_count = len(description.split())
            if word_count > 30:
                # Truncate to 30 words
                description = ' '.join(description.split()[:30])
            
            return {
                "success": True,
                "description": description,
                "word_count": word_count,
                "model_used": self.model_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": f"Equipment for PO {po_number}"  # Fallback description
            }
    
    def _build_prompt(self, po_number: str, po_text: str) -> str:
        """Build focused prompt for description generation"""
        return f"""You are an IT inventory specialist analyzing a commercial invoice. Identify the exact equipment, product models, and quantities associated with Purchase Order number {po_number} or listed on the invoice.

RULES:
- Maximum 15 words
- State the exact brand, model, and item description clearly (e.g. "MacBook Pro 16 M5 18 CPU and 20 GPU", "10x Dell Latitude 5440 Laptops", "15x EPOS Impact 100 Headsets")
- DO NOT use generic phrases like "Equipment for PO"
- Return ONLY valid JSON in format: {{"description": "Exact equipment name/model"}}

Invoice Text:
"{po_text}"

Response:"""
    
    async def _call_azure_api(self, prompt: str) -> Dict[str, Any]:
        """Call Azure AI Foundry API (Llama-3.3-70B-Instruct)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        endpoint_url = self.endpoint.rstrip('/')
        if not endpoint_url.endswith('/chat/completions'):
            if endpoint_url.endswith('/v1'):
                url = f"{endpoint_url}/chat/completions"
            else:
                url = f"{endpoint_url}/openai/v1/chat/completions"
        else:
            url = endpoint_url

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an IT inventory assistant. Generate a short 1-sentence description of the equipment for a Purchase Order."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        print(f"🧠 Calling Llama 3.3 API at {url}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=25)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"⚠️ Llama 3.3 API error ({response.status}): {error_text}")
                    raise Exception(f"Llama 3.3 API error {response.status}: {error_text}")
                
                res_json = await response.json()
                print(f"✅ Llama 3.3 description generated successfully")
                return res_json
    
    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        """Parse Azure AI response and extract description"""
        try:
            # Extract content from Azure response
            content = response_data["choices"][0]["message"]["content"]
            
            # Try to parse as JSON first
            try:
                json_response = json.loads(content.strip())
                description = json_response.get("description", "").strip()
                
                if description:
                    return description
            except json.JSONDecodeError:
                pass
            
            # Fallback: extract description from text
            # Look for description patterns
            import re
            
            # Try to find JSON-like pattern
            json_match = re.search(r'\{"description":\s*"([^"]+)"\}', content)
            if json_match:
                return json_match.group(1)
            
            # Try to find description after colon
            desc_match = re.search(r'description[:\s]*(.+)', content, re.IGNORECASE)
            if desc_match:
                return desc_match.group(1).strip()
            
            # Use first sentence if nothing else works
            sentences = content.strip().split('.')
            if sentences and len(sentences[0]) > 5:
                return sentences[0].strip()
            
            raise Exception("Could not extract description from LLM response")
            
        except Exception as e:
            raise Exception(f"Failed to parse LLM response: {e}")


class OllamaService(LLMService):
    """Local Ollama LLM Service (for future on-premises deployment)"""
    
    def __init__(self):
        """Initialize Ollama service"""
        self.endpoint = getattr(settings, 'OLLAMA_ENDPOINT', 'http://localhost:11434')
        self.model_name = getattr(settings, 'OLLAMA_MODEL', 'llama3.1:8b')
    
    async def generate_description(self, po_number: str, po_text: str) -> Dict[str, Any]:
        """Generate description using local Ollama"""
        try:
            prompt = self._build_prompt(po_number, po_text)
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 50,  # Limit output length
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                    
                    response_data = await response.json()
                    description = self._parse_ollama_response(response_data)
                    
                    return {
                        "success": True,
                        "description": description,
                        "model_used": self.model_name
                    }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": f"Equipment for PO {po_number}"
            }
    
    def _build_prompt(self, po_number: str, po_text: str) -> str:
        """Build prompt for Ollama"""
        return f"""Generate a concise description (max 30 words) for IT equipment from Purchase Order {po_number}.

Text: {po_text}

Description:"""
    
    def _parse_ollama_response(self, response_data: Dict[str, Any]) -> str:
        """Parse Ollama response"""
        response_text = response_data.get("response", "").strip()
        
        # Limit to 30 words
        words = response_text.split()[:30]
        return ' '.join(words)


class MockLLMService(LLMService):
    """Mock LLM Service for testing when Azure is not configured"""
    
    def __init__(self):
        """Initialize mock service"""
        self.model_name = "mock-llm-v1"
    
    async def generate_description(self, po_number: str, po_text: str) -> Dict[str, Any]:
        """Generate mock description for testing"""
        try:
            # Simulate processing time
            await asyncio.sleep(0.1)
            
            # Rule-based description generation for testing
            text_lower = po_text.lower()
            
            if "macbook" in text_lower:
                description = "Apple MacBook Pro laptop with advanced specifications"
            elif "keyboard" in text_lower:
                description = "Professional computer keyboard peripheral"
            elif "mouse" in text_lower:
                description = "High-precision computer mouse peripheral"
            elif "monitor" in text_lower or "display" in text_lower:
                description = "Professional computer monitor display"
            elif "headset" in text_lower or "headphone" in text_lower:
                description = "Professional audio headset equipment"
            else:
                # Generic description based on first few words
                words = po_text.split()[:4]
                description = f"IT equipment: {' '.join(words)}"
            
            # Ensure max 30 words
            description_words = description.split()[:30]
            final_description = ' '.join(description_words)
            
            return {
                "success": True,
                "description": final_description,
                "word_count": len(description_words),
                "model_used": self.model_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "description": f"Equipment for PO {po_number}"
            }


# Global instance - use lazy initialization
_llm_service = None

def get_llm_service() -> LLMService:
    """Factory function to get appropriate LLM service based on configuration"""
    global _llm_service
    
    if _llm_service is not None:
        return _llm_service
    
    llm_provider = getattr(settings, 'LLM_PROVIDER', 'mock').lower()
    
    try:
        if llm_provider == 'azure':
            _llm_service = AzureAIFoundryService()
        elif llm_provider == 'ollama':
            _llm_service = OllamaService()
        elif llm_provider == 'mock':
            _llm_service = MockLLMService()
        else:
            print(f"Warning: Unknown LLM provider '{llm_provider}', using mock service")
            _llm_service = MockLLMService()
            
    except Exception as e:
        print(f"Warning: LLM service initialization failed: {e}")
        print("Falling back to MockLLMService for testing")
        _llm_service = MockLLMService()
    
    return _llm_service