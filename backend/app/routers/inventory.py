"""Inventory Router - Jira as single source of truth"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.ticket import Ticket
from ..schemas.inventory import (
    StockIn, StockOut,
    Ticket as TicketSchema, TicketCreate,
    InventoryItem, StockHistoryRecord,
)
from ..schemas.dashboard import DashboardKPIs
from ..services.inventory_service import inventory_service
from ..services.jira_service import jira_service, JiraServiceError
from ..services.ai_recommendation_service import ai_recommendation_service

router = APIRouter(prefix="", tags=["inventory"])


# Dashboard
@router.get("/dashboard/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(db: Session = Depends(get_db)):
    """Live dashboard KPIs from inventory, products, tickets, stock_entries, and stock_exits."""
    return inventory_service.get_dashboard_kpis(db)


# Stock Operations
@router.post("/stock/in", status_code=status.HTTP_201_CREATED)
async def receive_stock(
    stock_data: StockIn,
    db: Session = Depends(get_db)
):
    """Receive stock into inventory"""
    try:
        result = inventory_service.receive_stock(
            db=db,
            product_ref=stock_data.ref,
            quantity=stock_data.quantity,
            technician=stock_data.technician,
            po_id=stock_data.poId,
            category=stock_data.category,
            brand=stock_data.brand,
            product_name=stock_data.productName,
            article_number=stock_data.articleNumber,
            serial_numbers=stock_data.serialNumbers,
            notes=stock_data.notes
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/stock/out", status_code=status.HTTP_201_CREATED)
async def assign_stock(
    stock_data: StockOut,
    db: Session = Depends(get_db)
):
    """Assign stock to a ticket after the user confirms the decision."""
    try:
        result = inventory_service.assign_stock(
            db=db,
            product_id=stock_data.productId,
            quantity=stock_data.quantity,
            ticket_id=stock_data.ticketId,
            technician=stock_data.technician,
            notes=stock_data.notes
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/stock/recommend-tickets")
async def recommend_tickets(payload: dict, db: Session = Depends(get_db)):
    """
    Recommend the top three Jira tickets using AI analysis.
    
    Workflow:
    1. Use tickets from request payload (mobile app already fetched them)
    2. If no tickets in payload, fetch from Jira
    3. Check cached AI analysis
    4. Run AI analysis for new/modified tickets
    5. Return top 3 recommendations
    """
    try:
        # Extract parameters
        detected_product = payload.get("productRef") or payload.get("category") or payload.get("detectedProduct")
        category = payload.get("category") or payload.get("detectedProduct")
        quantity = int(payload.get("quantity") or 1)
        available_quantity = int(payload.get("availableQuantity") or 1)
        
        # Check if tickets are provided in payload (avoid duplicate Jira fetch)
        tickets_data = payload.get("tickets", [])
        
        if tickets_data:
            # Use tickets from request payload (already fetched by mobile app)
            print(f"📦 Using {len(tickets_data)} tickets from request payload (avoiding duplicate Jira fetch)")
            
            # Convert ticket dicts to Ticket objects from database
            ticket_ids = [t.get("jira_key") or t.get("id") for t in tickets_data if t.get("jira_key") or t.get("id")]
            tickets = db.query(Ticket).filter(Ticket.jira_key.in_(ticket_ids)).all()
            
            if not tickets:
                print("⚠️ Tickets from payload not found in database, fetching from Jira...")
                tickets = jira_service.get_tickets(db)
        else:
            # No tickets in payload, fetch from Jira
            print("📡 No tickets in payload, fetching from Jira...")
            try:
                tickets = jira_service.get_tickets(db)
            except JiraServiceError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Jira service unavailable: {str(e)}"
                )
        
        if not tickets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No open tickets available"
            )
        
        # Rank tickets using AI (with caching)
        ranked = await ai_recommendation_service.rank_tickets_with_ai(
            db=db,
            tickets=tickets,
            detected_product=detected_product,
            category=category,
            quantity=quantity,
            available_quantity=available_quantity,
        )
        
        if not ranked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No matching tickets found"
            )
        
        # Return top recommendation
        top = ranked[0]
        return {
            "recommendations": ranked,
            "confidence": top["confidence"],
            "ticket": top["ticket"],
            "reason": top["reason"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Recommendation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/tickets/search")
async def search_tickets(query: str, db: Session = Depends(get_db)):
    """
    Search tickets by ID, title, or requester.
    Always fetches fresh data from Jira first.
    """
    try:
        tickets = jira_service.search_tickets(db, query)
        return [_ticket_to_dict(t) for t in tickets]
    except JiraServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Jira service unavailable: {str(e)}"
        )


# Inventory reads
@router.get("/inventory", response_model=List[InventoryItem])
async def list_inventory(
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
):
    """List all inventory rows (current on-hand stock)."""
    return inventory_service.list_inventory_items(
        db,
        category=category,
        brand=brand,
        search=search,
        limit=limit,
    )


@router.get("/inventory/{inventory_id}", response_model=InventoryItem)
async def get_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    """Get a single inventory row by primary key."""
    item = inventory_service.get_inventory_item(db, inventory_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory item {inventory_id} not found",
        )
    return item


# History — UNION of stock_entries + stock_exits, no dedicated movement table
@router.get("/history", response_model=List[StockHistoryRecord])
async def get_history(
    db: Session = Depends(get_db),
    limit: int = 100,
    action: Optional[str] = None,
):
    """
    Stock activity from audit tables (stock_entries + stock_exits).
    Optional action filter: IN (received) or OUT (assigned).
    """
    return inventory_service.get_stock_history(db, limit=limit, action=action)


# Tickets
@router.get("/tickets", response_model=List[TicketSchema])
async def get_tickets(
    db: Session = Depends(get_db),
    status: Optional[str] = None
):
    """
    Get all tickets from Jira (live data, synced with local cache).
    Optionally filter by status.
    """
    print("\n" + "="*80)
    print("🎫 GET /tickets endpoint called")
    print(f"   Status filter: {status}")
    print("="*80)
    
    try:
        print("📞 Calling jira_service.get_tickets()...")
        
        # Fetch and sync from Jira
        tickets = jira_service.get_tickets(db)
        
        print(f"✅ Received {len(tickets)} tickets from jira_service")
        
        # Apply status filter if provided
        if status:
            print(f"🔍 Applying status filter: {status}")
            original_count = len(tickets)
            tickets = [t for t in tickets if t.status.lower() == status.lower()]
            print(f"   Filtered from {original_count} to {len(tickets)} tickets")
        
        print(f"📤 Returning {len(tickets)} tickets to client")
        print("="*80 + "\n")
        
        return tickets
        
    except JiraServiceError as e:
        print(f"❌ JiraServiceError: {e}")
        print("="*80 + "\n")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Jira service unavailable: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("="*80 + "\n")
        raise


@router.get("/tickets/{ticket_id}", response_model=TicketSchema)
async def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db)
):
    """
    Get single ticket by Jira key.
    Fetches fresh data from Jira first.
    """
    try:
        # Fetch and sync from Jira
        tickets = jira_service.get_tickets(db)
        
        # Find ticket by jira_key or id
        ticket = next(
            (t for t in tickets if t.jira_key == ticket_id or t.id == ticket_id),
            None
        )
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found in Jira"
            )
        
        return ticket
        
    except JiraServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Jira service unavailable: {str(e)}"
        )


# Helper function
def _ticket_to_dict(ticket: Ticket) -> dict:
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
