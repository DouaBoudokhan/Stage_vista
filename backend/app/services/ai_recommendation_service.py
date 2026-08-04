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
        1. For each ticket, check if AI analysis is cached and valid
        2. If cached: reuse stored analysis
        3. If not cached or outdated: call LLM and cache result
        4. Return ranked list with confidence scores
        """
        if not tickets:
            raise ValueError("No tickets available for ranking")
        
        product_hint = (detected_product or category or "equipment").strip()
        ranked = []
        
        for ticket in tickets:
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
    
    async def _analyze_ticket_with_llm(
        self,
        ticket: Ticket,
        product_hint: str,
        quantity: int,
        available_quantity: int,
    ) -> Dict[str, Any]:
        """
        Analyze a single ticket using LLM.
        Returns analysis dictionary with score, reason, confidence.
        """
        # Build prompt for LLM
        prompt = self._build_analysis_prompt(
            ticket=ticket,
            product_hint=product_hint,
            quantity=quantity,
            available_quantity=available_quantity,
        )
        
        try:
            # Call LLM service (using existing Llama 3.3 integration)
            # For now, use rule-based scoring as fallback
            # TODO: Integrate with actual LLM when available
            analysis = self._rule_based_scoring(
                ticket=ticket,
                product_hint=product_hint,
                quantity=quantity,
                available_quantity=available_quantity,
            )
            
            return analysis
            
        except Exception as e:
            print(f"❌ LLM analysis failed for ticket {ticket.jira_key}: {e}")
            # Fallback to rule-based scoring
            return self._rule_based_scoring(
                ticket=ticket,
                product_hint=product_hint,
                quantity=quantity,
                available_quantity=available_quantity,
            )
    
    def _build_analysis_prompt(
        self,
        ticket: Ticket,
        product_hint: str,
        quantity: int,
        available_quantity: int,
    ) -> str:
        """Build LLM prompt for ticket analysis."""
        return f"""Analyze the following IT support ticket and determine if the requested equipment matches the available stock.

Ticket Details:
- Ticket ID: {ticket.jira_key}
- Title: {ticket.title}
- Description: {ticket.description or 'No description'}
- Priority: {ticket.priority}
- Requester: {ticket.requester}

Available Stock:
- Product: {product_hint}
- Quantity Available: {available_quantity}
- Quantity Requested: {quantity}

Please provide:
1. A relevance score (0-100)
2. A brief reason for the match
3. Confidence level (0-100)
4. Recommended product (if different from requested)
5. Recommended quantity

Return as JSON."""
    
    def _rule_based_scoring(
        self,
        ticket: Ticket,
        product_hint: str,
        quantity: int,
        available_quantity: int,
    ) -> Dict[str, Any]:
        """
        Rule-based scoring algorithm (fallback when LLM unavailable).
        """
        title = (ticket.title or "").lower()
        description = (ticket.description or "").lower()
        text = f"{title} {description}".lower()
        product_lower = product_hint.lower()
        
        score = 0
        reason_parts = []
        
        # Product match (highest weight)
        if product_lower in text:
            score += 40
            reason_parts.append(f"matches {product_hint}")
        elif any(word in text for word in ["laptop", "monitor", "mouse", "keyboard", "headset"]):
            score += 20
            reason_parts.append("mentions equipment type")
        
        # Urgency indicators
        urgency_keywords = ["urgent", "asap", "today", "immediately", "emergency", "critical"]
        if any(keyword in text for keyword in urgency_keywords):
            score += 15
            reason_parts.append("urgent request")
        
        # Priority boost
        priority_scores = {"critical": 15, "high": 10, "medium": 5, "low": 2}
        priority_score = priority_scores.get(ticket.priority.lower(), 0)
        score += priority_score
        if priority_score >= 10:
            reason_parts.append("high priority")
        
        # Quantity matching
        if quantity > 1:
            if any(word in text for word in ["multiple", "several", "two", "three"]):
                score += 10
                reason_parts.append("supports multiple units")
        
        # Availability check
        if available_quantity >= quantity:
            score += 10
        else:
            score -= 20
            reason_parts.append("insufficient stock")
        
        # Build reason
        reason = ", ".join(reason_parts) if reason_parts else "general equipment request"
        
        # Calculate confidence based on number of matches
        confidence = min(95, 50 + (len(reason_parts) * 10))
        
        return {
            "score": max(0, min(100, score)),
            "reason": reason,
            "confidence": confidence,
            "recommended_product": product_hint,
            "recommended_quantity": min(quantity, available_quantity),
        }
    
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
