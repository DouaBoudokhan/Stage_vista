#!/usr/bin/env python3
"""
Test Raw Jira API
Makes a direct call to Jira API and prints the raw response
"""

import sys
import os
import requests
import base64
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings

def main():
    print("\n" + "="*80)
    print("  Raw Jira API Test")
    print("="*80 + "\n")
    
    # Check configuration
    print("Configuration:")
    print(f"  JIRA_BASE_URL: {settings.JIRA_BASE_URL or 'NOT SET'}")
    print(f"  JIRA_USER_EMAIL: {settings.JIRA_USER_EMAIL or 'NOT SET'}")
    print(f"  JIRA_API_TOKEN: {'***' + settings.JIRA_API_TOKEN[-4:] if settings.JIRA_API_TOKEN else 'NOT SET'}")
    print(f"  JIRA_PROJECT_KEY: {settings.JIRA_PROJECT_KEY or 'NOT SET'}\n")
    
    if not all([settings.JIRA_BASE_URL, settings.JIRA_USER_EMAIL, settings.JIRA_API_TOKEN, settings.JIRA_PROJECT_KEY]):
        print("❌ Missing required Jira configuration!")
        print("\nPlease set the following in your .env file:")
        print("  JIRA_BASE_URL=https://your-domain.atlassian.net")
        print("  JIRA_USER_EMAIL=your-email@domain.com")
        print("  JIRA_API_TOKEN=your-api-token")
        print("  JIRA_PROJECT_KEY=IT")
        print("\nGenerate API token at: https://id.atlassian.com/manage-profile/security/api-tokens")
        return 1
    
    # Create auth header
    auth_string = f"{settings.JIRA_USER_EMAIL}:{settings.JIRA_API_TOKEN}"
    auth_bytes = auth_string.encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_string = base64_bytes.decode('ascii')
    
    headers = {
        "Authorization": f"Basic {base64_string}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Test 1: Get current user
    print("="*80)
    print("Test 1: Authenticating with Jira")
    print("="*80 + "\n")
    
    try:
        url = f"{settings.JIRA_BASE_URL}/rest/api/3/myself"
        print(f"GET {url}\n")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Authentication successful!")
            print(f"\nUser Info:")
            print(f"  Name: {user.get('displayName')}")
            print(f"  Email: {user.get('emailAddress')}")
            print(f"  Account ID: {user.get('accountId')}")
            print(f"  Active: {user.get('active')}\n")
        else:
            print(f"❌ Authentication failed!")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}\n")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return 1
    
    # Test 2: Search for open tickets
    print("="*80)
    print("Test 2: Fetching Open Tickets")
    print("="*80 + "\n")
    
    try:
        # Build JQL query - search for ANY tickets (not just Open)
        jql = f"project = {settings.JIRA_PROJECT_KEY} ORDER BY created DESC"
        
        params = {
            "jql": jql,
            "maxResults": 50,
            "fields": "summary,description,status,priority,created,updated,labels,customfield_10037,customfield_10038,customfield_10039"
        }
        
        # Use the new /search/jql endpoint (old /search endpoint was deprecated)
        url = f"{settings.JIRA_BASE_URL}/rest/api/3/search/jql"
        
        print(f"JQL Query: {jql}")
        print(f"URL: {url}\n")
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Request failed!")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}\n")
            return 1
        
        data = response.json()
        total = data.get('total', 0)
        issues = data.get('issues', [])
        
        print(f"✅ Query successful!")
        print(f"Total matching tickets: {total}")
        print(f"Tickets returned: {len(issues)}\n")
        
        if not issues:
            print("⚠️  No tickets found in project")
            print(f"\nTrying to list available projects...")
            
            # Try to list projects to help debug
            try:
                projects_url = f"{settings.JIRA_BASE_URL}/rest/api/3/project"
                projects_response = requests.get(projects_url, headers=headers, timeout=10)
                if projects_response.status_code == 200:
                    projects = projects_response.json()
                    print(f"\nAvailable projects ({len(projects)}):")
                    for proj in projects[:10]:  # Show first 10
                        print(f"  • {proj.get('key')} - {proj.get('name')}")
                    if len(projects) > 10:
                        print(f"  ... and {len(projects) - 10} more")
            except:
                pass
            
            return 0
        
        # Display each ticket
        print("="*80)
        print(f"Tickets (showing {len(issues)})")
        print("="*80 + "\n")
        
        for i, issue in enumerate(issues, 1):
            key = issue.get('key')
            fields = issue.get('fields', {})
            
            summary = fields.get('summary', 'N/A')
            status = fields.get('status', {}).get('name', 'N/A')
            priority = fields.get('priority', {}).get('name', 'N/A')
            created = fields.get('created', 'N/A')
            updated = fields.get('updated', 'N/A')
            labels = fields.get('labels', [])
            
            # Custom fields
            quantity = fields.get('customfield_10037', 'N/A')  # Requested Quantity
            cost_center = fields.get('customfield_10038', 'N/A')  # Cost Center
            component = fields.get('customfield_10039', 'N/A')  # Component
            
            # Description (can be ADF format)
            description_obj = fields.get('description')
            if description_obj and isinstance(description_obj, dict):
                # ADF format - extract text
                description = extract_text_from_adf(description_obj)
            else:
                description = str(description_obj) if description_obj else 'N/A'
            
            # Truncate description
            if len(description) > 150:
                description = description[:147] + "..."
            
            print(f"Ticket {i}: {key}")
            print(f"{'─' * 80}")
            print(f"  Summary: {summary}")
            print(f"  Status: {status}")
            print(f"  Priority: {priority}")
            print(f"  Labels: {', '.join(labels) if labels else 'None'}")
            print(f"  Quantity: {quantity}")
            print(f"  Cost Center: {cost_center}")
            print(f"  Component: {component}")
            print(f"  Created: {created}")
            print(f"  Updated: {updated}")
            print(f"  Description: {description}")
            print()
        
        # Save raw response to file
        output_file = "jira_raw_response.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print("="*80)
        print(f"✅ Raw response saved to: {output_file}")
        print("="*80 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def extract_text_from_adf(adf_doc):
    """Extract plain text from Atlassian Document Format"""
    if not adf_doc or not isinstance(adf_doc, dict):
        return ""
    
    text_parts = []
    
    def extract_from_node(node):
        if isinstance(node, dict):
            # Text node
            if node.get('type') == 'text':
                text_parts.append(node.get('text', ''))
            
            # Recurse into content
            if 'content' in node:
                for child in node['content']:
                    extract_from_node(child)
        
        elif isinstance(node, list):
            for item in node:
                extract_from_node(item)
    
    extract_from_node(adf_doc)
    return ' '.join(text_parts).strip()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
