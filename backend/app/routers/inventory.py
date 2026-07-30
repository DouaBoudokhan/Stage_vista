"""Inventory Router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..models.inventory import InventoryMovement, Ticket
from ..schemas.inventory import (
    InventoryMovement as MovementSchema,
    StockIn, StockOut,
    Ticket as TicketSchema, TicketCreate,
    InventoryItem, StockHistoryRecord,
)
from ..schemas.dashboard import DashboardKPIs
from ..services.inventory_service import inventory_service
import uuid

router = APIRouter(prefix="", tags=["inventory"])


# Dashboard
@router.get("/dashboard/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(db: Session = Depends(get_db)):
    """Live dashboard KPIs calculated from inventory, products, tickets, and movements."""
    return inventory_service.get_dashboard_kpis(db)


# Stock Operations
@router.post("/stock/in", response_model=MovementSchema, status_code=status.HTTP_201_CREATED)
async def receive_stock(
    stock_data: StockIn,
    db: Session = Depends(get_db)
):
    """Receive stock into inventory"""
    
    try:
        movement = inventory_service.receive_stock(
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
        return movement
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/stock/out", response_model=MovementSchema, status_code=status.HTTP_201_CREATED)
async def assign_stock(
    stock_data: StockOut,
    db: Session = Depends(get_db)
):
    """Assign stock to a ticket"""
    
    try:
        movement = inventory_service.assign_stock(
            db=db,
            product_id=stock_data.productId,
            quantity=stock_data.quantity,
            ticket_id=stock_data.ticketId,
            technician=stock_data.technician,
            notes=stock_data.notes
        )
        return movement
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Inventory reads
@router.get("/inventory", response_model=List[InventoryItem])
async def list_inventory(
    db: Session = Depends(get_db),
    category: str = None,
    brand: str = None,
    search: str = None,
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


# History
@router.get("/history", response_model=List[StockHistoryRecord])
async def get_history(
    db: Session = Depends(get_db),
    limit: int = 100,
    action: str = None,
):
    """
    Stock activity from audit tables (stock_entries + stock_exits).

    Optional action filter: IN (received) or OUT (assigned/taken out).
    Falls back to inventory_movements when audit tables have no rows yet.
    """
    return inventory_service.get_stock_history(db, limit=limit, action=action)


@router.get("/history/movements", response_model=List[MovementSchema])
async def get_movement_feed(
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Raw inventory_movements feed (operational log, separate from audit tables)."""
    movements = db.query(InventoryMovement).order_by(
        InventoryMovement.timestamp.desc()
    ).limit(limit).all()
    return movements


# Tickets
@router.get("/tickets", response_model=List[TicketSchema])
async def get_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: str = None
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
        id=f"T{str(uuid.uuid4())[:8].upper()}",
        **ticket_data.model_dump()
    )
    
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    return new_ticket
