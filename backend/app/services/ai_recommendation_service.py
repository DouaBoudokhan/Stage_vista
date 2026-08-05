"""
AI-powered ticket recommendation service with intelligent caching.
Only calls LLM for new or modified tickets.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.ticket import Ticket
from .llm_service import get_llm_service


class AIRecommendationService:
    """
    AI recommendation service with smart caching.
    Reuses cached AI analysis when tickets haven't changed.
    """
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    async def rank_tickets_with_ai(
        self,
        db: Session,
        tickets: List[Ticket],
        detected_product: Optional[str],
        category: Optional[str],
        quantity: int,
        available_quantity: int,
    ) -> List[Dict[str, Any]]:
        """
        Rank tickets by relevance using AI analysis.
        
        Workflow:
        1. Pre-filter tickets to top 20 most relevant (fast)
        2. For each top ticket, check if AI analysis is cached and valid
        3. If cached: reuse stored analysis
        4. If not cached or outdated: call LLM and cache result
        5. Return top 3 ranked results
        """
        if not tickets:
            raise ValueError("No tickets available for ranking")
        
        product_hint = (category or detected_product or "equipment").strip()
        
        print("\n" + "="*80)
        print("🎯 AI RECOMMENDATION REQUEST")
        print(f"   Detected Product: {detected_product}")
        print(f"   Category: {category}")
        print(f"   Product Hint (used): {product_hint}")
        print(f"   Quantity: {quantity}")
        print(f"   Available: {available_quantity}")
        print(f"   Total Tickets: {len(tickets)}")
        print("="*80)
        
        # STEP 1: Pre-filter tickets by equipment keyword (returns ALL matches)
        print(f"🔍 Pre-filtering {len(tickets)} tickets...")
        candidates = self._quick_filter_candidates(tickets, product_hint)
        
        # If no candidates found, return empty list (not an error)
        if not candidates or len(candidates) == 0:
            print(f"⚠️ No tickets found matching '{product_hint}' - returning empty recommendations")
            return []
        
        print(f"✅ Will analyze {len(candidates)} tickets with Azure Llama 3.3\n")
        
        ranked = []
        
        for ticket in candidates:
            # Check if we can reuse cached AI analysis
            if ticket.ai_analyzed and not ticket.needs_ai_analysis():
                # Reuse cached analysis
                print(f"♻️ Reusing cached AI analysis for ticket {ticket.jira_key}")
                ranked.append({
                    "ticket": self._ticket_to_dict(ticket),
                    "score": ticket.ai_score or 0,
                    "reason": ticket.ai_reason or "Previously analyzed",
                    "confidence": ticket.ai_confidence or 50,
                    "recommended_product": ticket.ai_recommended_product,
                    "recommended_quantity": ticket.ai_recommended_quantity,
                    "cached": True,
                })
            else:
                # Need fresh AI analysis
                print(f"🧠 Generating new AI analysis for ticket {ticket.jira_key}")
                analysis = await self._analyze_ticket_with_llm(
                    ticket=ticket,
                    product_hint=product_hint,
                    quantity=quantity,
                    available_quantity=available_quantity,
                )
                
                # Cache the analysis in the database
                ticket.ai_analyzed = True
                ticket.ai_analysis = json.dumps(analysis)
                ticket.ai_score = analysis["score"]
                ticket.ai_reason = analysis["reason"]
                ticket.ai_recommended_product = analysis.get("recommended_product")
                ticket.ai_recommended_quantity = analysis.get("recommended_quantity")
                ticket.ai_confidence = analysis["confidence"]
                ticket.ai_model = "llama-3.3-70b"
                ticket.analyzed_at = datetime.utcnow()
                db.commit()
                
                print(f"✅ Cached AI analysis for ticket {ticket.jira_key}")
                
                ranked.append({
                    "ticket": self._ticket_to_dict(ticket),
                    "score": analysis["score"],
                    "reason": analysis["reason"],
                    "confidence": analysis["confidence"],
                    "recommended_product": analysis.get("recommended_product"),
                    "recommended_quantity": analysis.get("recommended_quantity"),
                    "cached": False,
                })
        
        # Sort by score descending
        ranked.sort(key=lambda x: -x["score"])
        
        # Return top 3
        return ranked[:3]
    
    def _quick_filter_candidates(
        self,
        tickets: List[Ticket],
        product_hint: str,
    ) -> List[Ticket]:
        """
        Quick filter to find tickets that mention the equipment keyword OR synonyms.
        Returns ALL tickets that match (no limit).
        """
        # Equipment synonyms mapping
        equipment_synonyms = {
            "laptop": ["laptop", "computer", "notebook", "pc", "macbook", "thinkpad"],
            "headset": ["headset", "casque", "headphone", "earphone", "audio", "micro"],
            "monitor": ["monitor", "screen", "display", "écran"],
            "mouse": ["mouse", "souris"],
            "keyboard": ["keyboard", "clavier"],
        }
        
        product_lower = product_hint.lower()
        
        # Get synonyms for this product
        search_terms = [product_lower]
        for key, synonyms in equipment_synonyms.items():
            if product_lower in synonyms:
                search_terms = synonyms
                break
        
        matched_tickets = []
        
        print(f"🔍 Quick filter: Looking for '{product_hint}' (synonyms: {', '.join(search_terms)}) in {len(tickets)} tickets")
        
        for ticket in tickets:
            title = (ticket.title or "").lower()
            description = (ticket.description or "").lower()
            text = f"{title} {description}"
            
            # Check if any synonym matches
            if any(term in text for term in search_terms):
                matched_tickets.append(ticket)
        
        # Show how many matched
        print(f"✅ Found {len(matched_tickets)} tickets mentioning '{product_hint}' or synonyms")
        
        # Debug: Show first 5 matches
        if matched_tickets:
            print(f"\n📊 First 5 matches:")
            for i, ticket in enumerate(matched_tickets[:5], 1):
                title_preview = ticket.title[:60] if ticket.title else "No title"
                print(f"  {i}. {ticket.jira_key}: {title_preview} (Priority: {ticket.priority})")
            print()
        
        return matched_tickets
    
    async def _analyze_ticket_with_llm(
        self,
        ticket: Ticket,
        product_hint: str,
        quantity: int,
        available_quantity: int,
    ) -> Dict[str, Any]:
        """
        Analyze a single ticket using Azure AI Foundry Llama 3.3.
        Returns analysis dictionary with score, reason, confidence.
        No fallback - LLM is required.
        """
        # Build prompt for LLM
        prompt = self._build_analysis_prompt(
            ticket=ticket,
            product_hint=product_hint,
            quantity=quantity,
            available_quantity=available_quantity,
        )
        
        # Call Azure AI Foundry Llama 3.3 (same as invoice analysis)
        analysis = await self._call_llm_for_analysis(prompt, ticket, product_hint, quantity, available_quantity)
        return analysis
    
    async def _call_llm_for_analysis(
        self,
        prompt: str,
        ticket: Ticket,
        product_hint: str,
        quantity: int,
        available_quantity: int,
    ) -> Dict[str, Any]:
        """Call Azure AI Foundry Llama 3.3 for ticket analysis (same model as invoice analysis)"""
        import aiohttp
        from ..config import settings
        
        # Use Azure AI Foundry credentials (same as invoice analysis)
        azure_endpoint = getattr(settings, 'AZURE_LLM_ENDPOINT', None) or getattr(settings, 'AZURE_AI_ENDPOINT', None)
        azure_api_key = getattr(settings, 'AZURE_AI_API_KEY', None)
        
        if not azure_endpoint or not azure_api_key:
            raise Exception("❌ Azure AI Foundry not configured. Set AZURE_AI_ENDPOINT and AZURE_AI_API_KEY in .env")
        
        # Ensure endpoint has correct format
        endpoint_url = azure_endpoint.rstrip('/')
        if not endpoint_url.endswith('/chat/completions'):
            if endpoint_url.endswith('/v1'):
                url = f"{endpoint_url}/chat/completions"
            else:
                url = f"{endpoint_url}/openai/v1/chat/completions"
        else:
            url = endpoint_url
        
        headers = {
            "Authorization": f"Bearer {azure_api_key}",
            "api-key": azure_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "Llama-3.3-70B-Instruct",  # Same model as invoice analysis
            "messages": [
                {
                    "role": "system",
                    "content": "You are an IT support ticket analyzer. Analyze if tickets match available equipment. Return ONLY valid JSON: {\"score\": 0-100, \"reason\": \"brief explanation\", \"confidence\": 0-100}"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 150,
            "temperature": 0.2
        }
        
        print(f"🧠 Calling Azure AI Foundry (Llama 3.3) for ticket {ticket.jira_key}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Azure AI Foundry error ({response.status}): {error_text}")
                    raise Exception(f"Azure AI Foundry API error {response.status}: {error_text}")
                
                response_data = await response.json()
                
                # Parse LLM response
                content = response_data["choices"][0]["message"]["content"]
                
                print(f"✅ Llama 3.3 response for {ticket.jira_key}: {content[:100]}...")
                
                # Try to parse JSON
                import json
                import re
                
                # Extract JSON from response
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                    
                    return {
                        "score": int(analysis_data.get("score", 50)),
                        "reason": analysis_data.get("reason", "AI analysis"),
                        "confidence": int(analysis_data.get("confidence", 70)),
                        "recommended_product": product_hint,
                        "recommended_quantity": min(quantity, available_quantity),
                    }
                else:
                    raise Exception(f"Could not parse JSON from Llama 3.3 response: {content}")
    
    
    def _build_analysis_prompt(
        self,
        ticket: Ticket,
        product_hint: str,
        quantity: int,
        available_quantity: int,
    ) -> str:
        """Build LLM prompt for ticket analysis with emphasis on intent and context."""
        return f"""Analyze if this IT support ticket is requesting NEW/REPLACEMENT equipment, not just help/repair.

TICKET INFORMATION:
- ID: {ticket.jira_key}
- Title: {ticket.title}
- Description: {ticket.description or 'No description provided'}
- Priority: {ticket.priority}
- Status: {ticket.status}
- Requester: {ticket.requester}

AVAILABLE STOCK:
- Equipment Type: {product_hint}
- Available Quantity: {available_quantity}
- Requested Quantity: {quantity}

CRITICAL: Understand the INTENT of the ticket:

✅ MATCH if ticket requests:
- "New {product_hint}"
- "Replacement {product_hint}"
- "{product_hint} needed"
- "Request {product_hint}"
- "Need a {product_hint}"
- "Get new equipment"

❌ NO MATCH if ticket requests:
- "Help fix my {product_hint}"
- "My {product_hint} is broken" (asking for repair help)
- "Issue with {product_hint}" (troubleshooting request)
- "Can someone help" (support request)
- "{product_hint} not working" (technical assistance)
- Software/driver issues

EXAMPLES:
- "My laptop won't turn on, can IT help?" → Score: 0 (asking for help, not new laptop)
- "Request new laptop for new hire" → Score: 100 (requesting new equipment)
- "Headset microphone broken, need replacement" → Score: 95 (explicitly requesting replacement)
- "Monitor flickering, how to fix?" → Score: 0 (asking for troubleshooting)

TASK:
Score this ticket based on:
1. **Equipment Match** (0-50 points): Does ticket REQUEST new/replacement "{product_hint}"?
2. **URGENCY** (0-50 points): How urgent is the EQUIPMENT REQUEST?
   - Priority level (Critical/High = more urgent)
   - Urgency keywords: "urgent", "asap", "immediately", "new hire", "starting soon"
   - Business impact

SCORING GUIDELINES:
- 90-100: Clear equipment request + HIGH urgency
- 70-89:  Clear equipment request + MEDIUM urgency  
- 50-69:  Clear equipment request + LOW urgency
- 30-49:  Unclear intent, might be equipment request
- 0-29:   Troubleshooting/repair help request, NOT equipment request

RESPONSE FORMAT (JSON only):
{{
  "score": <0-100>,
  "reason": "<brief explanation focusing on whether ticket requests NEW equipment vs help/repair>",
  "confidence": <0-100>
}}

Return ONLY the JSON, no other text."""
    
    @staticmethod
    def _ticket_to_dict(ticket: Ticket) -> Dict[str, Any]:
        """Convert Ticket model to dictionary."""
        return {
            "id": ticket.jira_key,
            "jira_key": ticket.jira_key,
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": ticket.status,
            "requester": ticket.requester,
            "assignee": ticket.assignee,
            "category": ticket.category,
            "product_needed": ticket.product_needed,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }


# Global instance
ai_recommendation_service = AIRecommendationService()
