"""Inventory Router"""
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
from ..services.jira_service import JiraRecommendationService

router = APIRouter(prefix="", tags=["inventory"])

jira_service = JiraRecommendationService()


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
async def recommend_tickets(payload: dict):
    """Recommend the top three Jira tickets without assigning inventory automatically."""
    detected_product = payload.get("productRef") or payload.get("category") or payload.get("detectedProduct")
    category = payload.get("category") or payload.get("detectedProduct")
    quantity = int(payload.get("quantity") or 1)
    available_quantity = int(payload.get("availableQuantity") or 1)
    tickets = payload.get("tickets")

    ranked = jira_service.rank_tickets(
        detected_product=detected_product,
        category=category,
        quantity=quantity,
        available_quantity=available_quantity,
        tickets=tickets,
    )

    if not ranked:
        return {"recommendations": [], "confidence": 0, "ticket": None, "reason": "No Jira tickets available"}

    top = ranked[0]
    return {
        "recommendations": ranked,
        "confidence": min(95, 70 + top["score"]),
        "ticket": top["ticket"],
        "reason": top["reason"],
    }


@router.get("/tickets/search")
async def search_tickets(query: str):
    """Search tickets by ID, title, or requester."""
    return jira_service.search_tickets(query)


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
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None
):
    """Get all tickets, optionally filtered by status"""
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return tickets


@router.get("/tickets/{ticket_id}", response_model=TicketSchema)
async def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single ticket by ID"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    return ticket


@router.post("/tickets", response_model=TicketSchema, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ticket"""
    new_ticket = Ticket(
        id=f"T-{str(uuid.uuid4())[:8].upper()}",
        **ticket_data.model_dump()
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket
