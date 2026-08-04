#!/usr/bin/env python3
"""
Test Jira Connection
Fetches open tickets from Jira and displays them in the terminal
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.services.jira_service import JiraService, JiraServiceError
from app.config import settings
import json
from datetime import datetime

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_ticket_details(ticket):
    """Print a single ticket in a nice format"""
    print(f"┌─ {ticket.get('jira_key', 'N/A')} {'─' * (70 - len(ticket.get('jira_key', 'N/A')))}")
    print(f"│ Title: {ticket.get('title', 'N/A')}")
    print(f"│ Status: {ticket.get('status', 'N/A')}")
    print(f"│ Priority: {ticket.get('priority', 'N/A')}")
    print(f"│ Category: {ticket.get('category', 'N/A')}")
    print(f"│ Requested Quantity: {ticket.get('requested_quantity', 'N/A')}")
    print(f"│ Cost Center: {ticket.get('cost_center', 'N/A')}")
    print(f"│ Created: {ticket.get('created_at', 'N/A')}")
    print(f"│ Updated: {ticket.get('jira_last_updated', 'N/A')}")
    
    # Description (truncated)
    description = ticket.get('description', 'N/A')
    if len(description) > 100:
        description = description[:97] + "..."
    print(f"│ Description: {description}")
    
    print(f"└{'─' * 78}\n")

def print_configuration():
    """Print current Jira configuration"""
    print_section("Jira Configuration")
    
    config_items = [
        ("JIRA_BASE_URL", settings.JIRA_BASE_URL),
        ("JIRA_USER_EMAIL", settings.JIRA_USER_EMAIL),
        ("JIRA_API_TOKEN", "***" + settings.JIRA_API_TOKEN[-4:] if settings.JIRA_API_TOKEN else None),
        ("JIRA_PROJECT_KEY", settings.JIRA_PROJECT_KEY),
        ("JIRA_ISSUE_TYPE", getattr(settings, 'JIRA_ISSUE_TYPE', 'Not set')),
        ("JIRA_COST_CENTER", getattr(settings, 'JIRA_COST_CENTER', 'Not set')),
        ("JIRA_COMPONENT", getattr(settings, 'JIRA_COMPONENT', 'Not set')),
    ]
    
    for key, value in config_items:
        status = "✅" if value else "❌"
        display_value = value if value else "NOT SET"
        print(f"{status} {key:25} = {display_value}")

def test_jira_api_directly():
    """Test Jira API directly with requests"""
    print_section("Testing Direct Jira API Connection")
    
    import requests
    import base64
    
    if not settings.JIRA_BASE_URL or not settings.JIRA_USER_EMAIL or not settings.JIRA_API_TOKEN:
        print("❌ Jira credentials not configured. Skipping direct API test.")
        return False
    
    try:
        # Create basic auth header
        auth_string = f"{settings.JIRA_USER_EMAIL}:{settings.JIRA_API_TOKEN}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        base64_string = base64_bytes.decode('ascii')
        
        headers = {
            "Authorization": f"Basic {base64_string}",
            "Content-Type": "application/json"
        }
        
        # Test connection with a simple API call
        url = f"{settings.JIRA_BASE_URL}/rest/api/3/myself"
        
        print(f"Testing connection to: {settings.JIRA_BASE_URL}")
        print(f"Using email: {settings.JIRA_USER_EMAIL}")
        print(f"Calling endpoint: {url}\n")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Connection successful!")
            print(f"   Authenticated as: {user_data.get('displayName', 'Unknown')}")
            print(f"   Email: {user_data.get('emailAddress', 'Unknown')}")
            print(f"   Account ID: {user_data.get('accountId', 'Unknown')}\n")
            return True
        else:
            print(f"❌ Connection failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}\n")
        return False

def test_jira_service():
    """Test JiraService class"""
    print_section("Testing JiraService")
    
    try:
        # Initialize service
        jira_service = JiraService()
        print("✅ JiraService initialized successfully\n")
        
        # Fetch tickets
        print("Fetching open tickets from Jira...")
        tickets = jira_service.fetch_open_tickets_from_jira()
        
        if not tickets:
            print("⚠️  No open tickets found in Jira")
            print(f"   Project: {settings.JIRA_PROJECT_KEY}")
            print(f"   Status: Open\n")
            return []
        
        print(f"✅ Successfully fetched {len(tickets)} open ticket(s)\n")
        return tickets
        
    except JiraServiceError as e:
        print(f"❌ JiraServiceError: {e}\n")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return []

def display_tickets(tickets):
    """Display all tickets in a formatted way"""
    if not tickets:
        return
    
    print_section(f"Open Tickets ({len(tickets)} total)")
    
    for i, ticket in enumerate(tickets, 1):
        print(f"Ticket {i}/{len(tickets)}:")
        print_ticket_details(ticket)

def export_to_json(tickets):
    """Export tickets to JSON file"""
    if not tickets:
        return
    
    print_section("Export")
    
    output_file = "jira_tickets_export.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tickets, f, indent=2, default=str)
        
        print(f"✅ Exported {len(tickets)} ticket(s) to: {output_file}\n")
        
    except Exception as e:
        print(f"❌ Failed to export: {e}\n")

def print_summary(tickets):
    """Print summary statistics"""
    if not tickets:
        return
    
    print_section("Summary")
    
    # Count by status
    statuses = {}
    priorities = {}
    categories = {}
    
    for ticket in tickets:
        status = ticket.get('status', 'Unknown')
        priority = ticket.get('priority', 'Unknown')
        category = ticket.get('category', 'Uncategorized')
        
        statuses[status] = statuses.get(status, 0) + 1
        priorities[priority] = priorities.get(priority, 0) + 1
        categories[category] = categories.get(category, 0) + 1
    
    print(f"Total Tickets: {len(tickets)}\n")
    
    print("By Status:")
    for status, count in sorted(statuses.items()):
        print(f"  • {status}: {count}")
    
    print("\nBy Priority:")
    for priority, count in sorted(priorities.items()):
        print(f"  • {priority}: {count}")
    
    print("\nBy Category:")
    for category, count in sorted(categories.items()):
        print(f"  • {category}: {count}")
    
    print()

def main():
    print("\n" + "="*80)
    print("  StockIT - Jira Connection Test")
    print("="*80)
    
    # Step 1: Show configuration
    print_configuration()
    
    # Step 2: Test direct API connection
    api_works = test_jira_api_directly()
    
    if not api_works:
        print("\n❌ Direct API test failed. Please check your Jira credentials.")
        print("\nRequired environment variables:")
        print("  - JIRA_BASE_URL (e.g., https://your-domain.atlassian.net)")
        print("  - JIRA_USER_EMAIL (your Jira account email)")
        print("  - JIRA_API_TOKEN (generate at: https://id.atlassian.com/manage-profile/security/api-tokens)")
        print("  - JIRA_PROJECT_KEY (e.g., IT)")
        return 1
    
    # Step 3: Test JiraService
    tickets = test_jira_service()
    
    if not tickets:
        print("\n⚠️  No tickets returned from JiraService")
        print("\nPossible reasons:")
        print("  • No open tickets in the project")
        print("  • Incorrect project key")
        print("  • Insufficient permissions")
        print(f"\nJQL Query used: project = {settings.JIRA_PROJECT_KEY} AND status = Open")
        return 1
    
    # Step 4: Display tickets
    display_tickets(tickets)
    
    # Step 5: Show summary
    print_summary(tickets)
    
    # Step 6: Export to JSON
    export_to_json(tickets)
    
    print("="*80)
    print("  ✅ Test completed successfully!")
    print("="*80 + "\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
