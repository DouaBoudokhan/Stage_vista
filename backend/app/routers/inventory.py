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
    Ticket as TicketSchema, TicketCreate
)
from ..services.inventory_service import inventory_service
import uuid

router = APIRouter(prefix="", tags=["inventory"])


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


# History
@router.get("/history", response_model=List[MovementSchema])
async def get_history(
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get inventory movement history"""
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
