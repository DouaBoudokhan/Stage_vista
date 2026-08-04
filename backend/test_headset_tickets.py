#!/usr/bin/env python3
"""
Check which tickets in the database mention headsets
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.models.ticket import Ticket

def main():
    db = SessionLocal()
    
    print("\n" + "="*80)
    print("Searching for Headset Tickets in Database")
    print("="*80 + "\n")
    
    # Get all tickets
    tickets = db.query(Ticket).all()
    print(f"Total tickets in database: {len(tickets)}\n")
    
    # Search for headset mentions
    headset_tickets = []
    
    for ticket in tickets:
        title = (ticket.title or "").lower()
        description = (ticket.description or "").lower()
        text = f"{title} {description}"
        
        if "headset" in text or "headphone" in text or "audio" in text or "casque" in text:
            headset_tickets.append(ticket)
    
    print(f"Found {len(headset_tickets)} tickets mentioning headset/audio:\n")
    
    for i, ticket in enumerate(headset_tickets[:10], 1):
        print(f"{i}. {ticket.jira_key}: {ticket.title}")
        print(f"   Status: {ticket.status}")
        print(f"   Priority: {ticket.priority}")
        if ticket.description:
            desc_preview = ticket.description[:100].replace('\n', ' ')
            print(f"   Description: {desc_preview}...")
        print()
    
    if len(headset_tickets) > 10:
        print(f"... and {len(headset_tickets) - 10} more")
    
    db.close()

if __name__ == "__main__":
    main()
