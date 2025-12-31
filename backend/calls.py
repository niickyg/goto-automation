"""
Calls API router.

Provides endpoints for listing calls, getting call details, and summaries.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import (
    get_db,
    Call,
    CallSummary,
    ActionItem,
    CallRepository,
    SummaryRepository,
    CallDirection,
    SentimentType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calls", tags=["calls"])


# Response Models
class CallListItem(BaseModel):
    """Call list item response."""
    id: int
    goto_call_id: str
    direction: str
    caller_number: Optional[str]
    caller_name: Optional[str]
    called_number: Optional[str]
    called_name: Optional[str]
    start_time: datetime
    duration_seconds: Optional[int]
    has_recording: bool
    has_transcript: bool
    sentiment: Optional[str]
    urgency_score: Optional[int]

    class Config:
        orm_mode = True


class CallSummaryResponse(BaseModel):
    """Call summary response."""
    transcript: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    urgency_score: Optional[int]
    key_topics: List[str]
    transcription_completed_at: Optional[datetime]
    analysis_completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class ActionItemResponse(BaseModel):
    """Action item response."""
    id: int
    description: str
    assigned_to: Optional[str]
    priority: Optional[int]
    status: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True


class CallDetailResponse(BaseModel):
    """Complete call details response."""
    id: int
    goto_call_id: str
    direction: str
    caller_number: Optional[str]
    caller_name: Optional[str]
    called_number: Optional[str]
    called_name: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    recording_url: Optional[str]
    has_recording: bool
    webhook_received_at: datetime
    created_at: datetime
    summary: Optional[CallSummaryResponse]
    action_items: List[ActionItemResponse]

    class Config:
        orm_mode = True


class CallsListResponse(BaseModel):
    """Paginated calls list response."""
    calls: List[CallListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


# Endpoints
@router.get("/", response_model=CallsListResponse)
async def list_calls(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by caller/called name or number"),
    direction: Optional[CallDirection] = Query(None, description="Filter by direction"),
    sentiment: Optional[SentimentType] = Query(None, description="Filter by sentiment"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (from)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (to)"),
    has_recording: Optional[bool] = Query(None, description="Filter by recording availability"),
    db: Session = Depends(get_db)
):
    """
    List calls with pagination and filters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        search: Search text (searches caller/called names and numbers)
        direction: Optional direction filter
        sentiment: Optional sentiment filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        has_recording: Optional recording filter
        db: Database session

    Returns:
        Paginated list of calls
    """
    # Build query
    query = db.query(Call).order_by(Call.start_time.desc())

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Call.caller_name.ilike(search_pattern),
                Call.caller_number.ilike(search_pattern),
                Call.called_name.ilike(search_pattern),
                Call.called_number.ilike(search_pattern),
                Call.goto_call_id.ilike(search_pattern)
            )
        )

    # Apply filters
    if direction:
        query = query.filter(Call.direction == direction)

    if start_date:
        query = query.filter(Call.start_time >= start_date)

    if end_date:
        query = query.filter(Call.start_time <= end_date)

    if has_recording is not None:
        if has_recording:
            query = query.filter(Call.recording_url.isnot(None))
        else:
            query = query.filter(Call.recording_url.is_(None))

    # Apply sentiment filter (requires join)
    if sentiment:
        query = query.join(CallSummary).filter(CallSummary.sentiment == sentiment)

    # Get total count
    total = query.count()

    # Apply pagination
    skip = (page - 1) * page_size
    calls = query.offset(skip).limit(page_size).all()

    # Build response items
    call_items = []
    for call in calls:
        # Get summary if exists
        summary = SummaryRepository.get_by_call_id(db, call.id)

        call_items.append(CallListItem(
            id=call.id,
            goto_call_id=call.goto_call_id,
            direction=call.direction.value,
            caller_number=call.caller_number,
            caller_name=call.caller_name,
            called_number=call.called_number,
            called_name=call.called_name,
            start_time=call.start_time,
            duration_seconds=call.duration_seconds,
            has_recording=call.recording_url is not None,
            has_transcript=summary.transcript is not None if summary else False,
            sentiment=summary.sentiment.value if summary and summary.sentiment else None,
            urgency_score=summary.urgency_score if summary else None
        ))

    has_more = (skip + page_size) < total

    return CallsListResponse(
        calls=call_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_details(
    call_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete details for a specific call.

    Args:
        call_id: Call database ID
        db: Database session

    Returns:
        Complete call details with summary and action items

    Raises:
        HTTPException: If call not found
    """
    # Get call
    call = CallRepository.get_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Get summary
    summary = SummaryRepository.get_by_call_id(db, call_id)
    summary_response = None
    if summary:
        key_topics = []
        if summary.key_topics:
            key_topics = [t.strip() for t in summary.key_topics.split(",")]

        summary_response = CallSummaryResponse(
            transcript=summary.transcript,
            summary=summary.summary,
            sentiment=summary.sentiment.value if summary.sentiment else None,
            urgency_score=summary.urgency_score,
            key_topics=key_topics,
            transcription_completed_at=summary.transcription_completed_at,
            analysis_completed_at=summary.analysis_completed_at
        )

    # Get action items
    action_items = db.query(ActionItem).filter(ActionItem.call_id == call_id).all()
    action_items_response = [
        ActionItemResponse(
            id=item.id,
            description=item.description,
            assigned_to=item.assigned_to,
            priority=item.priority,
            status=item.status.value,
            due_date=item.due_date,
            completed_at=item.completed_at,
            created_at=item.created_at
        )
        for item in action_items
    ]

    return CallDetailResponse(
        id=call.id,
        goto_call_id=call.goto_call_id,
        direction=call.direction.value,
        caller_number=call.caller_number,
        caller_name=call.caller_name,
        called_number=call.called_number,
        called_name=call.called_name,
        start_time=call.start_time,
        end_time=call.end_time,
        duration_seconds=call.duration_seconds,
        recording_url=call.recording_url,
        has_recording=call.recording_url is not None,
        webhook_received_at=call.webhook_received_at,
        created_at=call.created_at,
        summary=summary_response,
        action_items=action_items_response
    )


@router.get("/{call_id}/transcript")
async def get_call_transcript(
    call_id: int,
    db: Session = Depends(get_db)
):
    """
    Get full transcript for a call.

    Args:
        call_id: Call database ID
        db: Database session

    Returns:
        Transcript text

    Raises:
        HTTPException: If call or transcript not found
    """
    # Get call
    call = CallRepository.get_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Get summary with transcript
    summary = SummaryRepository.get_by_call_id(db, call_id)
    if not summary or not summary.transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return {
        "call_id": call.goto_call_id,
        "transcript": summary.transcript,
        "transcription_completed_at": summary.transcription_completed_at
    }


@router.get("/search/by-goto-id/{goto_call_id}", response_model=CallDetailResponse)
async def search_call_by_goto_id(
    goto_call_id: str,
    db: Session = Depends(get_db)
):
    """
    Search for a call by GoTo call ID.

    Args:
        goto_call_id: GoTo Connect call identifier
        db: Database session

    Returns:
        Complete call details

    Raises:
        HTTPException: If call not found
    """
    call = CallRepository.get_by_goto_id(db, goto_call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Reuse the get_call_details logic
    return await get_call_details(call.id, db)


@router.get("/recent/summary")
async def get_recent_calls_summary(
    limit: int = Query(10, ge=1, le=100, description="Number of recent calls"),
    db: Session = Depends(get_db)
):
    """
    Get a quick summary of recent calls.

    Args:
        limit: Number of recent calls to include
        db: Database session

    Returns:
        Summary of recent calls
    """
    calls = CallRepository.list_calls(db, skip=0, limit=limit)

    summary_data = []
    for call in calls:
        summary = SummaryRepository.get_by_call_id(db, call.id)

        summary_data.append({
            "id": call.id,
            "goto_call_id": call.goto_call_id,
            "caller": call.caller_name or call.caller_number,
            "start_time": call.start_time,
            "duration_seconds": call.duration_seconds,
            "sentiment": summary.sentiment.value if summary and summary.sentiment else None,
            "urgency": summary.urgency_score if summary else None,
            "summary": summary.summary if summary else None
        })

    return {
        "recent_calls": summary_data,
        "count": len(summary_data)
    }


# Simulation endpoint for testing
class SimulateCallRequest(BaseModel):
    """Request model for simulating calls with complete data"""
    caller_name: str
    caller_number: str
    called_number: str
    called_name: str
    start_time: str
    end_time: str
    duration_seconds: int
    direction: str
    status: str
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[dict] = None


@router.post("/simulate")
async def simulate_call(
    request: SimulateCallRequest,
    db: Session = Depends(get_db)
):
    """
    Create a simulated call with complete data for testing.

    This endpoint bypasses the normal webhook flow and creates
    calls directly with transcripts, summaries, and action items.
    """
    try:
        # Parse start time
        start_time = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))

        # Parse end time
        end_time = datetime.fromisoformat(request.end_time.replace('Z', '+00:00'))

        # Create call record
        call = Call(
            goto_call_id=f"SIM-{int(start_time.timestamp())}",
            caller_number=request.caller_number,
            caller_name=request.caller_name,
            called_number=request.called_number,
            called_name=request.called_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=request.duration_seconds,
            direction=CallDirection.INBOUND if request.direction == "inbound" else CallDirection.OUTBOUND,
            recording_url=request.recording_url
        )
        db.add(call)
        db.flush()  # Get call ID

        # Create summary if provided
        if request.summary:
            sentiment_map = {
                "positive": SentimentType.POSITIVE,
                "neutral": SentimentType.NEUTRAL,
                "negative": SentimentType.NEGATIVE
            }

            summary = CallSummary(
                call_id=call.id,
                transcript=request.transcript,
                summary=request.summary.get("summary"),
                sentiment=sentiment_map.get(request.summary.get("sentiment"), SentimentType.NEUTRAL),
                urgency_score=request.summary.get("urgency_score", 3),
                key_topics=", ".join(request.summary.get("key_topics", [])),
                transcription_completed_at=start_time,
                analysis_completed_at=start_time
            )
            db.add(summary)

            # Create action items if provided
            if "action_items" in request.summary:
                for item_data in request.summary["action_items"]:
                    due_date = None
                    if item_data.get("due_date"):
                        try:
                            due_date = datetime.fromisoformat(item_data["due_date"].replace('Z', '+00:00'))
                        except:
                            pass

                    action_item = ActionItem(
                        call_id=call.id,
                        description=item_data.get("description"),
                        assigned_to=item_data.get("assigned_to"),
                        priority=item_data.get("priority", 3),
                        due_date=due_date,
                        status="pending"
                    )
                    db.add(action_item)

        db.commit()

        return {
            "status": "success",
            "call_id": call.id,
            "message": "Simulated call created successfully"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating simulated call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create simulated call: {str(e)}")


if __name__ == "__main__":
    print("Calls router initialized successfully!")
