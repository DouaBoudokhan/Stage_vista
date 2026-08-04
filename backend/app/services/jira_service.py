"""Jira integration helpers for AI-assisted stock exit recommendations."""
from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

import requests

from ..config import settings


class JiraRecommendationService:
    """Provide Jira ticket lookup and AI-style recommendation ranking."""

    def __init__(self) -> None:
        self.base_url = settings.JIRA_BASE_URL.rstrip("/") if settings.JIRA_BASE_URL else ""
        self.user_email = settings.JIRA_USER_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.project_key = settings.JIRA_PROJECT_KEY
        self.issue_type = settings.JIRA_ISSUE_TYPE
        self.cost_center = settings.JIRA_COST_CENTER
        self.component = settings.JIRA_COMPONENT

    def _auth_headers(self) -> Dict[str, str]:
        if not self.base_url or not self.user_email or not self.api_token:
            return {}
        token = base64.b64encode(f"{self.user_email}:{self.api_token}".encode("utf-8")).decode("ascii")
        return {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        }

    def get_open_tickets(self) -> List[Dict[str, Any]]:
        """Fetch open Jira tickets when credentials are configured."""
        if not self.base_url or not self.user_email or not self.api_token:
            return []

        url = f"{self.base_url}/rest/api/3/search"
        params = {
            "jql": "statusCategory != Done AND status != Closed",
            "maxResults": 50,
            "fields": "summary,description,priority,status,assignee,reporter,created,labels",
        }
        try:
            response = requests.get(url, headers=self._auth_headers(), params=params, timeout=10)
            response.raise_for_status()
            payload = response.json()
            issues = payload.get("issues", [])
            normalized = []
            for issue in issues:
                fields = issue.get("fields", {})
                normalized.append(
                    {
                        "id": issue.get("key"),
                        "title": fields.get("summary"),
                        "description": fields.get("description") or "",
                        "priority": self._normalize_priority(fields.get("priority", {}).get("name")),
                        "status": fields.get("status", {}).get("name"),
                        "requester": (fields.get("reporter") or {}).get("displayName") or (fields.get("reporter") or {}).get("emailAddress"),
                        "created_at": fields.get("created"),
                        "labels": [label for label in fields.get("labels", [])],
                    }
                )
            return normalized
        except Exception:
            return []

    def search_tickets(self, query: str) -> List[Dict[str, Any]]:
        """Search Jira tickets using a free-text query."""
        tickets = self.get_open_tickets()
        if not query:
            return tickets
        needle = query.strip().lower()
        return [ticket for ticket in tickets if needle in (ticket.get("id") or "").lower() or needle in (ticket.get("title") or "").lower() or needle in (ticket.get("requester") or "").lower()]

    def rank_tickets(
        self,
        detected_product: Optional[str],
        category: Optional[str],
        quantity: int,
        available_quantity: int,
        tickets: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Rank tickets by relevance for the requested stock exit."""
        ticket_pool = tickets or self.get_open_tickets()
        if not ticket_pool:
            return []

        product_hint = (detected_product or category or "equipment").strip().lower()
        ranked = []
        for ticket in ticket_pool:
            title = (ticket.get("title") or "").lower()
            description = (ticket.get("description") or "").lower()
            text = f"{title} {description}".lower()

            score = 0
            if product_hint and product_hint in text:
                score += 5
            if "urgent" in text or "asap" in text or "today" in text or "immediately" in text:
                score += 4
            if "priority" in text or "high" in text:
                score += 2
            if quantity > 1 and ("multiple" in text or "two" in text or "several" in text):
                score += 2
            if available_quantity <= 1:
                score += 1

            priority_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            score += priority_weight.get((ticket.get("priority") or "").lower(), 0)

            reason_parts = []
            if product_hint and product_hint in text:
                reason_parts.append(f"matches {detected_product or category}")
            if "urgent" in text or "asap" in text or "today" in text or "immediately" in text:
                reason_parts.append("urgent request")
            if priority_weight.get((ticket.get("priority") or "").lower(), 0) >= 3:
                reason_parts.append("high priority")
            if quantity > 1:
                reason_parts.append("supports multiple units")
            reason = ", ".join(reason_parts) or "general fit for the requested equipment"
            ranked.append({"ticket": ticket, "score": score, "reason": reason})

        ranked.sort(key=lambda item: (-item["score"], (item["ticket"].get("created_at") or "")))
        return ranked[:3]

    @staticmethod
    def _normalize_priority(priority: Optional[str]) -> str:
        if not priority:
            return "Medium"
        normalized = str(priority).strip().lower()
        if normalized in {"critical", "highest", "urgent"}:
            return "Critical"
        if normalized in {"high", "important"}:
            return "High"
        if normalized in {"medium", "normal"}:
            return "Medium"
        return "Low"
