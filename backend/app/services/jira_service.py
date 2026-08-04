"""
Jira integration service - Jira is the single source of truth for tickets.
Local database is used only as a cache for AI analysis.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from sqlalchemy.orm import Session

from ..config import settings
from ..models.ticket import Ticket


class JiraServiceError(Exception):
    """Raised when Jira API is unavailable or misconfigured."""
    pass


class JiraService:
    """
    Jira ticket service - fetches live tickets from Jira API.
    Syncs with local database for AI analysis caching.
    """

    def __init__(self) -> None:
        self.base_url = settings.JIRA_BASE_URL.rstrip("/") if settings.JIRA_BASE_URL else ""
        self.user_email = settings.JIRA_USER_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.project_key = settings.JIRA_PROJECT_KEY
        self.issue_type = settings.JIRA_ISSUE_TYPE
        self.cost_center = settings.JIRA_COST_CENTER
        self.component = settings.JIRA_COMPONENT
        
        # Validate configuration
        if not all([self.base_url, self.user_email, self.api_token]):
            raise JiraServiceError(
                "Jira credentials not configured. Please set JIRA_BASE_URL, "
                "JIRA_USER_EMAIL, and JIRA_API_TOKEN in environment variables."
            )

    def _auth_headers(self) -> Dict[str, str]:
        """Generate Basic Auth headers for Jira API."""
        token = base64.b64encode(
            f"{self.user_email}:{self.api_token}".encode("utf-8")
        ).decode("ascii")
        return {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def fetch_open_tickets_from_jira(self) -> List[Dict[str, Any]]:
        """
        Fetch open tickets directly from Jira API.
        Raises JiraServiceError if the API is unavailable.
        """
        url = f"{self.base_url}/rest/api/3/search"
        params = {
            "jql": f"project = {self.project_key} AND statusCategory != Done AND status != Closed",
            "maxResults": 100,
            "fields": "summary,description,priority,status,assignee,reporter,created,updated,labels,customfield_*",
        }
        
        try:
            print(f"🔍 Fetching tickets from Jira: {url}")
            response = requests.get(
                url, 
                headers=self._auth_headers(), 
                params=params, 
                timeout=15
            )
            response.raise_for_status()
            payload = response.json()
            issues = payload.get("issues", [])
            
            print(f"✅ Fetched {len(issues)} tickets from Jira")
            
            normalized = []
            for issue in issues:
                fields = issue.get("fields", {})
                
                # Parse description (handle Jira's ADF format)
                description = ""
                desc_field = fields.get("description")
                if isinstance(desc_field, dict):
                    # Atlassian Document Format (ADF)
                    description = self._extract_text_from_adf(desc_field)
                elif isinstance(desc_field, str):
                    description = desc_field
                
                # Extract reporter/requester info
                reporter = fields.get("reporter") or {}
                requester = (
                    reporter.get("displayName") 
                    or reporter.get("emailAddress") 
                    or "Unknown"
                )
                
                # Extract assignee
                assignee_field = fields.get("assignee") or {}
                assignee = assignee_field.get("displayName") or assignee_field.get("emailAddress")
                
                # Parse timestamps
                created_at = self._parse_jira_timestamp(fields.get("created"))
                updated_at = self._parse_jira_timestamp(fields.get("updated"))
                
                normalized.append({
                    "jira_key": issue.get("key"),
                    "title": fields.get("summary") or "Untitled Ticket",
                    "description": description,
                    "priority": self._normalize_priority(
                        (fields.get("priority") or {}).get("name")
                    ),
                    "status": (fields.get("status") or {}).get("name") or "Open",
                    "requester": requester,
                    "assignee": assignee,
                    "created_at": created_at,
                    "jira_last_updated": updated_at,
                    "labels": fields.get("labels", []),
                    "category": self._extract_category_from_labels(fields.get("labels", [])),
                    "product_needed": self._extract_product_from_description(description),
                })
            
            return normalized
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Jira API request failed: {e}")
            raise JiraServiceError(f"Failed to fetch tickets from Jira: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error fetching from Jira: {e}")
            raise JiraServiceError(f"Unexpected error: {str(e)}")

    def sync_tickets_with_cache(
        self, 
        db: Session, 
        jira_tickets: Optional[List[Dict[str, Any]]] = None
    ) -> List[Ticket]:
        """
        Sync Jira tickets with local database cache.
        
        Workflow:
        1. Fetch tickets from Jira (or use provided list)
        2. For each Jira ticket:
           - Search local DB by jira_key
           - If not exists: insert, mark ai_analyzed = False
           - If exists: update Jira fields, preserve AI analysis
        3. Return list of synced Ticket objects
        """
        if jira_tickets is None:
            jira_tickets = self.fetch_open_tickets_from_jira()
        
        if not jira_tickets:
            raise JiraServiceError("No tickets available from Jira")
        
        synced_tickets = []
        
        for jira_data in jira_tickets:
            jira_key = jira_data["jira_key"]
            
            # Check if ticket exists in local cache
            existing = db.query(Ticket).filter(Ticket.jira_key == jira_key).first()
            
            if existing:
                # Update Jira fields (preserve AI analysis)
                existing.title = jira_data["title"]
                existing.description = jira_data["description"]
                existing.priority = jira_data["priority"]
                existing.status = jira_data["status"]
                existing.requester = jira_data["requester"]
                existing.assignee = jira_data.get("assignee")
                existing.category = jira_data.get("category")
                existing.product_needed = jira_data.get("product_needed")
                existing.jira_last_updated = jira_data["jira_last_updated"]
                
                print(f"✓ Updated ticket {jira_key} from Jira")
                synced_tickets.append(existing)
            else:
                # Insert new ticket
                new_ticket = Ticket(
                    id=jira_key,  # Use Jira key as primary key
                    jira_key=jira_key,
                    title=jira_data["title"],
                    description=jira_data["description"],
                    priority=jira_data["priority"],
                    status=jira_data["status"],
                    requester=jira_data["requester"],
                    assignee=jira_data.get("assignee"),
                    category=jira_data.get("category"),
                    product_needed=jira_data.get("product_needed"),
                    created_at=jira_data["created_at"],
                    jira_last_updated=jira_data["jira_last_updated"],
                    ai_analyzed=False,  # Mark as not analyzed
                )
                db.add(new_ticket)
                db.flush()
                
                print(f"✓ Inserted new ticket {jira_key} from Jira")
                synced_tickets.append(new_ticket)
        
        db.commit()
        print(f"✅ Synced {len(synced_tickets)} tickets with local cache")
        
        return synced_tickets

    def get_tickets(self, db: Session, force_refresh: bool = False) -> List[Ticket]:
        """
        Get tickets - always fetches from Jira and syncs with cache.
        
        Args:
            db: Database session
            force_refresh: If True, always fetch from Jira (default: False)
        
        Returns:
            List of Ticket objects from local cache (after sync)
        """
        # Always fetch fresh data from Jira
        jira_tickets = self.fetch_open_tickets_from_jira()
        
        # Sync with local cache
        synced_tickets = self.sync_tickets_with_cache(db, jira_tickets)
        
        return synced_tickets

    def search_tickets(self, db: Session, query: str) -> List[Ticket]:
        """
        Search tickets by query string.
        Always fetches fresh data from Jira first.
        """
        tickets = self.get_tickets(db)
        
        if not query:
            return tickets
        
        needle = query.strip().lower()
        return [
            ticket for ticket in tickets
            if needle in ticket.jira_key.lower()
            or needle in (ticket.title or "").lower()
            or needle in (ticket.requester or "").lower()
            or needle in (ticket.description or "").lower()
        ]

    # Helper methods
    
    @staticmethod
    def _parse_jira_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira ISO timestamp to datetime."""
        if not timestamp_str:
            return None
        try:
            # Jira format: 2024-01-15T10:30:45.123+0000
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            return None
    
    @staticmethod
    def _extract_text_from_adf(adf: Dict[str, Any]) -> str:
        """Extract plain text from Atlassian Document Format (ADF)."""
        if not adf:
            return ""
        
        text_parts = []
        
        def extract_content(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    text_parts.append(node.get("text", ""))
                if "content" in node:
                    for child in node["content"]:
                        extract_content(child)
            elif isinstance(node, list):
                for item in node:
                    extract_content(item)
        
        extract_content(adf)
        return " ".join(text_parts).strip()
    
    @staticmethod
    def _normalize_priority(priority: Optional[str]) -> str:
        """Normalize Jira priority to standard values."""
        if not priority:
            return "Medium"
        normalized = str(priority).strip().lower()
        if normalized in {"critical", "highest", "urgent", "blocker"}:
            return "Critical"
        if normalized in {"high", "important"}:
            return "High"
        if normalized in {"medium", "normal"}:
            return "Medium"
        return "Low"
    
    @staticmethod
    def _extract_category_from_labels(labels: List[str]) -> Optional[str]:
        """Extract category from Jira labels."""
        for label in labels:
            label_lower = label.lower()
            if label_lower in {"hardware", "equipment", "laptop", "monitor", "mouse", "keyboard"}:
                return label
        return None
    
    @staticmethod
    def _extract_product_from_description(description: str) -> Optional[str]:
        """Extract product type from ticket description."""
        if not description:
            return None
        
        desc_lower = description.lower()
        product_keywords = {
            "laptop": "Laptop",
            "monitor": "Monitor",
            "mouse": "Mouse",
            "keyboard": "Keyboard",
            "headset": "Headset",
            "headphone": "Headset",
        }
        
        for keyword, product in product_keywords.items():
            if keyword in desc_lower:
                return product
        
        return None


# Global instance
jira_service = JiraService()
