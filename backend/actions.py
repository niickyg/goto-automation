"""
Action items API router.

Provides endpoints for managing action items extracted from calls.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import (
    get_db,
    ActionItem,
    ActionItemStatus,
    ActionItemRepository,
    Call,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/actions", tags=["actions"])


# Request/Response Models
class ActionItemResponse(BaseModel):
    """Action item response."""
    id: int
    call_id: int
    goto_call_id: str
    description: str
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    status: str
    priority: Optional[int]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    call_info: Optional[dict]

    class Config:
        orm_mode = True


class ActionItemUpdate(BaseModel):
    """Action item update request."""
    status: Optional[ActionItemStatus] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class ActionItemsListResponse(BaseModel):
    """Paginated action items list response."""
    action_items: List[ActionItemResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ActionItemStats(BaseModel):
    """Action item statistics."""
    total: int
    pending: int
    in_progress: int
    completed: int
    cancelled: int
    completion_rate: float
    avg_priority: float


# Helper functions
def build_action_item_response(
    action_item: ActionItem,
    db: Session,
    include_call_info: bool = True
) -> ActionItemResponse:
    """Build action item response with optional call info."""
    call_info = None
    goto_call_id = ""

    if include_call_info:
        call = db.query(Call).filter(Call.id == action_item.call_id).first()
        if call:
            goto_call_id = call.goto_call_id
            call_info = {
                "goto_call_id": call.goto_call_id,
                "caller": call.caller_name or call.caller_number,
                "start_time": call.start_time.isoformat(),
                "direction": call.direction.value
            }

    return ActionItemResponse(
        id=action_item.id,
        call_id=action_item.call_id,
        goto_call_id=goto_call_id,
        description=action_item.description,
        assigned_to=action_item.assigned_to,
        due_date=action_item.due_date,
        status=action_item.status.value,
        priority=action_item.priority,
        completed_at=action_item.completed_at,
        created_at=action_item.created_at,
        updated_at=action_item.updated_at,
        call_info=call_info
    )


# Endpoints
@router.get("/", response_model=ActionItemsListResponse)
async def list_action_items(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[ActionItemStatus] = Query(None, description="Filter by status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    min_priority: Optional[int] = Query(None, ge=1, le=5, description="Minimum priority"),
    db: Session = Depends(get_db)
):
    """
    List action items with pagination and filters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Optional status filter
        assigned_to: Optional assignee filter
        min_priority: Optional minimum priority filter
        db: Database session

    Returns:
        Paginated list of action items
    """
    # Build query
    query = db.query(ActionItem).order_by(
        ActionItem.priority.desc().nullslast(),
        ActionItem.created_at.desc()
    )

    # Apply filters
    if status:
        query = query.filter(ActionItem.status == status)

    if assigned_to:
        query = query.filter(ActionItem.assigned_to.ilike(f"%{assigned_to}%"))

    if min_priority:
        query = query.filter(ActionItem.priority >= min_priority)

    # Get total count
    total = query.count()

    # Apply pagination
    skip = (page - 1) * page_size
    action_items = query.offset(skip).limit(page_size).all()

    # Build response
    items_response = [
        build_action_item_response(item, db)
        for item in action_items
    ]

    has_more = (skip + page_size) < total

    return ActionItemsListResponse(
        action_items=items_response,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/stats", response_model=ActionItemStats)
async def get_action_item_stats(
    db: Session = Depends(get_db)
):
    """
    Get action item statistics.

    Args:
        db: Database session

    Returns:
        Action item statistics
    """
    total = db.query(ActionItem).count()
    pending = db.query(ActionItem).filter(
        ActionItem.status == ActionItemStatus.PENDING
    ).count()
    in_progress = db.query(ActionItem).filter(
        ActionItem.status == ActionItemStatus.IN_PROGRESS
    ).count()
    completed = db.query(ActionItem).filter(
        ActionItem.status == ActionItemStatus.COMPLETED
    ).count()
    cancelled = db.query(ActionItem).filter(
        ActionItem.status == ActionItemStatus.CANCELLED
    ).count()

    completion_rate = (completed / total * 100) if total > 0 else 0

    # Calculate average priority
    priorities = db.query(ActionItem.priority).filter(
        ActionItem.priority.isnot(None)
    ).all()
    avg_priority = (
        sum(p[0] for p in priorities) / len(priorities)
        if priorities else 0
    )

    return ActionItemStats(
        total=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        cancelled=cancelled,
        completion_rate=completion_rate,
        avg_priority=avg_priority
    )


@router.get("/{action_id}", response_model=ActionItemResponse)
async def get_action_item(
    action_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific action item by ID.

    Args:
        action_id: Action item ID
        db: Database session

    Returns:
        Action item details

    Raises:
        HTTPException: If action item not found
    """
    action_item = ActionItemRepository.get_by_id(db, action_id)
    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")

    return build_action_item_response(action_item, db)


@router.patch("/{action_id}", response_model=ActionItemResponse)
async def update_action_item(
    action_id: int,
    update_data: ActionItemUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an action item.

    Args:
        action_id: Action item ID
        update_data: Fields to update
        db: Database session

    Returns:
        Updated action item

    Raises:
        HTTPException: If action item not found
    """
    action_item = ActionItemRepository.get_by_id(db, action_id)
    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")

    # Build update dict (only include non-None values)
    update_dict = {}
    if update_data.status is not None:
        update_dict["status"] = update_data.status
    if update_data.assigned_to is not None:
        update_dict["assigned_to"] = update_data.assigned_to
    if update_data.due_date is not None:
        update_dict["due_date"] = update_data.due_date
    if update_data.priority is not None:
        update_dict["priority"] = update_data.priority

    # Update action item
    updated_item = ActionItemRepository.update(db, action_item, **update_dict)

    logger.info(f"Updated action item {action_id}: {update_dict}")

    return build_action_item_response(updated_item, db)


@router.post("/{action_id}/complete", response_model=ActionItemResponse)
async def complete_action_item(
    action_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark an action item as completed.

    Args:
        action_id: Action item ID
        db: Database session

    Returns:
        Updated action item

    Raises:
        HTTPException: If action item not found
    """
    action_item = ActionItemRepository.get_by_id(db, action_id)
    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")

    if action_item.status == ActionItemStatus.COMPLETED:
        logger.info(f"Action item {action_id} already completed")
        return build_action_item_response(action_item, db)

    # Update to completed
    updated_item = ActionItemRepository.update(
        db,
        action_item,
        status=ActionItemStatus.COMPLETED,
        completed_at=datetime.utcnow()
    )

    logger.info(f"Completed action item {action_id}")

    return build_action_item_response(updated_item, db)


@router.post("/{action_id}/reopen", response_model=ActionItemResponse)
async def reopen_action_item(
    action_id: int,
    db: Session = Depends(get_db)
):
    """
    Reopen a completed or cancelled action item.

    Args:
        action_id: Action item ID
        db: Database session

    Returns:
        Updated action item

    Raises:
        HTTPException: If action item not found
    """
    action_item = ActionItemRepository.get_by_id(db, action_id)
    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")

    # Update to pending
    updated_item = ActionItemRepository.update(
        db,
        action_item,
        status=ActionItemStatus.PENDING,
        completed_at=None
    )

    logger.info(f"Reopened action item {action_id}")

    return build_action_item_response(updated_item, db)


@router.delete("/{action_id}")
async def delete_action_item(
    action_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an action item.

    Args:
        action_id: Action item ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If action item not found or deletion fails
    """
    action_item = ActionItemRepository.get_by_id(db, action_id)
    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")

    # Delete the action item
    success = ActionItemRepository.delete(db, action_item)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete action item"
        )

    logger.info(f"Deleted action item {action_id}")

    return {
        "success": True,
        "message": f"Action item {action_id} deleted successfully"
    }


@router.get("/by-call/{call_id}", response_model=List[ActionItemResponse])
async def get_action_items_by_call(
    call_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all action items for a specific call.

    Args:
        call_id: Call database ID
        db: Database session

    Returns:
        List of action items for the call
    """
    # Verify call exists
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Get action items
    action_items = db.query(ActionItem).filter(
        ActionItem.call_id == call_id
    ).order_by(
        ActionItem.priority.desc().nullslast(),
        ActionItem.created_at.desc()
    ).all()

    return [
        build_action_item_response(item, db, include_call_info=False)
        for item in action_items
    ]


@router.get("/pending/urgent")
async def get_urgent_pending_actions(
    min_priority: int = Query(4, ge=1, le=5, description="Minimum priority level"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
    db: Session = Depends(get_db)
):
    """
    Get urgent pending action items.

    Args:
        min_priority: Minimum priority level (default 4)
        limit: Maximum number of items
        db: Database session

    Returns:
        List of urgent pending action items
    """
    action_items = db.query(ActionItem).filter(
        ActionItem.status == ActionItemStatus.PENDING,
        ActionItem.priority >= min_priority
    ).order_by(
        ActionItem.priority.desc(),
        ActionItem.created_at.asc()
    ).limit(limit).all()

    return {
        "urgent_actions": [
            build_action_item_response(item, db)
            for item in action_items
        ],
        "count": len(action_items)
    }


@router.get("/overdue/list")
async def get_overdue_action_items(
    db: Session = Depends(get_db)
):
    """
    Get action items that are overdue.

    Args:
        db: Database session

    Returns:
        List of overdue action items
    """
    now = datetime.utcnow()

    action_items = db.query(ActionItem).filter(
        ActionItem.status.in_([ActionItemStatus.PENDING, ActionItemStatus.IN_PROGRESS]),
        ActionItem.due_date < now
    ).order_by(
        ActionItem.due_date.asc()
    ).all()

    return {
        "overdue_actions": [
            build_action_item_response(item, db)
            for item in action_items
        ],
        "count": len(action_items)
    }


if __name__ == "__main__":
    print("Actions router initialized successfully!")
