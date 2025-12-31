"""
KPI aggregation and analytics router.

Provides endpoints for daily, weekly, and monthly metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import (
    get_db,
    Call,
    CallSummary,
    ActionItem,
    KPI,
    KPIRepository,
    SentimentType,
    ActionItemStatus,
    CallDirection,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kpi", tags=["kpi"])


# Response Models
class KPIMetrics(BaseModel):
    """KPI metrics response."""
    period_type: str
    period_start: datetime
    period_end: datetime
    total_calls: int
    total_duration_seconds: int
    avg_duration_seconds: Optional[float]
    inbound_calls: int
    outbound_calls: int
    calls_with_recordings: int
    calls_transcribed: int
    positive_sentiment_count: int
    neutral_sentiment_count: int
    negative_sentiment_count: int
    avg_urgency_score: Optional[float]
    total_action_items: int
    completed_action_items: int


class SentimentBreakdown(BaseModel):
    """Sentiment breakdown."""
    positive: int
    neutral: int
    negative: int
    total: int


class ActionItemMetrics(BaseModel):
    """Action item metrics."""
    total: int
    pending: int
    in_progress: int
    completed: int
    cancelled: int
    completion_rate: float


class CallVolumeMetrics(BaseModel):
    """Call volume metrics."""
    total_calls: int
    inbound: int
    outbound: int
    avg_duration_seconds: float
    total_duration_minutes: float


class DashboardMetrics(BaseModel):
    """Complete dashboard metrics."""
    period_start: datetime
    period_end: datetime
    call_volume: CallVolumeMetrics
    sentiment: SentimentBreakdown
    action_items: ActionItemMetrics
    avg_urgency_score: float
    calls_transcribed: int
    transcription_rate: float


# Helper functions
def calculate_kpi_for_period(
    db: Session,
    period_start: datetime,
    period_end: datetime
) -> KPIMetrics:
    """
    Calculate KPI metrics for a specific period.

    Args:
        db: Database session
        period_start: Period start datetime
        period_end: Period end datetime

    Returns:
        KPIMetrics object with calculated values
    """
    # Query calls in period
    calls_query = db.query(Call).filter(
        Call.start_time >= period_start,
        Call.start_time < period_end
    )

    total_calls = calls_query.count()

    if total_calls == 0:
        # Return empty metrics
        return KPIMetrics(
            period_type="custom",
            period_start=period_start,
            period_end=period_end,
            total_calls=0,
            total_duration_seconds=0,
            avg_duration_seconds=0,
            inbound_calls=0,
            outbound_calls=0,
            calls_with_recordings=0,
            calls_transcribed=0,
            positive_sentiment_count=0,
            neutral_sentiment_count=0,
            negative_sentiment_count=0,
            avg_urgency_score=0,
            total_action_items=0,
            completed_action_items=0
        )

    # Call metrics
    duration_stats = db.query(
        func.sum(Call.duration_seconds).label("total_duration"),
        func.avg(Call.duration_seconds).label("avg_duration")
    ).filter(
        Call.start_time >= period_start,
        Call.start_time < period_end
    ).first()

    total_duration = duration_stats.total_duration or 0
    avg_duration = duration_stats.avg_duration or 0

    # Direction breakdown
    inbound_calls = calls_query.filter(Call.direction == CallDirection.INBOUND).count()
    outbound_calls = calls_query.filter(Call.direction == CallDirection.OUTBOUND).count()

    # Recording stats
    calls_with_recordings = calls_query.filter(Call.recording_url.isnot(None)).count()

    # Get call IDs for summary queries
    call_ids = [call.id for call in calls_query.all()]

    # Transcription and sentiment stats
    summaries = db.query(CallSummary).filter(
        CallSummary.call_id.in_(call_ids)
    ).all()

    calls_transcribed = len([s for s in summaries if s.transcript])
    positive_count = len([s for s in summaries if s.sentiment == SentimentType.POSITIVE])
    neutral_count = len([s for s in summaries if s.sentiment == SentimentType.NEUTRAL])
    negative_count = len([s for s in summaries if s.sentiment == SentimentType.NEGATIVE])

    # Average urgency
    urgency_scores = [s.urgency_score for s in summaries if s.urgency_score]
    avg_urgency = sum(urgency_scores) / len(urgency_scores) if urgency_scores else 0

    # Action items
    action_items_query = db.query(ActionItem).filter(
        ActionItem.call_id.in_(call_ids)
    )
    total_action_items = action_items_query.count()
    completed_action_items = action_items_query.filter(
        ActionItem.status == ActionItemStatus.COMPLETED
    ).count()

    return KPIMetrics(
        period_type="custom",
        period_start=period_start,
        period_end=period_end,
        total_calls=total_calls,
        total_duration_seconds=total_duration,
        avg_duration_seconds=avg_duration,
        inbound_calls=inbound_calls,
        outbound_calls=outbound_calls,
        calls_with_recordings=calls_with_recordings,
        calls_transcribed=calls_transcribed,
        positive_sentiment_count=positive_count,
        neutral_sentiment_count=neutral_count,
        negative_sentiment_count=negative_count,
        avg_urgency_score=avg_urgency,
        total_action_items=total_action_items,
        completed_action_items=completed_action_items
    )


# Endpoints
@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    period: str = Query("today", regex="^(today|week|month)$"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard metrics for a period.

    Args:
        period: Time period (today, week, month)
        db: Database session

    Returns:
        Dashboard metrics
    """
    now = datetime.utcnow()

    # Determine period boundaries
    if period == "today":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)
    elif period == "week":
        period_start = now - timedelta(days=now.weekday())
        period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=7)
    else:  # month
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Next month
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)

    # Calculate metrics
    kpi = calculate_kpi_for_period(db, period_start, period_end)

    # Build dashboard response
    call_volume = CallVolumeMetrics(
        total_calls=kpi.total_calls,
        inbound=kpi.inbound_calls,
        outbound=kpi.outbound_calls,
        avg_duration_seconds=kpi.avg_duration_seconds or 0,
        total_duration_minutes=(kpi.total_duration_seconds or 0) / 60
    )

    sentiment = SentimentBreakdown(
        positive=kpi.positive_sentiment_count,
        neutral=kpi.neutral_sentiment_count,
        negative=kpi.negative_sentiment_count,
        total=kpi.positive_sentiment_count + kpi.neutral_sentiment_count + kpi.negative_sentiment_count
    )

    # Action items breakdown
    calls_query = db.query(Call).filter(
        Call.start_time >= period_start,
        Call.start_time < period_end
    )
    call_ids = [call.id for call in calls_query.all()]

    action_pending = db.query(ActionItem).filter(
        ActionItem.call_id.in_(call_ids),
        ActionItem.status == ActionItemStatus.PENDING
    ).count() if call_ids else 0

    action_in_progress = db.query(ActionItem).filter(
        ActionItem.call_id.in_(call_ids),
        ActionItem.status == ActionItemStatus.IN_PROGRESS
    ).count() if call_ids else 0

    action_cancelled = db.query(ActionItem).filter(
        ActionItem.call_id.in_(call_ids),
        ActionItem.status == ActionItemStatus.CANCELLED
    ).count() if call_ids else 0

    completion_rate = (
        kpi.completed_action_items / kpi.total_action_items * 100
        if kpi.total_action_items > 0 else 0
    )

    action_items_metrics = ActionItemMetrics(
        total=kpi.total_action_items,
        pending=action_pending,
        in_progress=action_in_progress,
        completed=kpi.completed_action_items,
        cancelled=action_cancelled,
        completion_rate=completion_rate
    )

    transcription_rate = (
        kpi.calls_transcribed / kpi.total_calls * 100
        if kpi.total_calls > 0 else 0
    )

    return DashboardMetrics(
        period_start=period_start,
        period_end=period_end,
        call_volume=call_volume,
        sentiment=sentiment,
        action_items=action_items_metrics,
        avg_urgency_score=kpi.avg_urgency_score or 0,
        calls_transcribed=kpi.calls_transcribed,
        transcription_rate=transcription_rate
    )


@router.get("/daily", response_model=List[KPIMetrics])
async def get_daily_kpis(
    days: int = Query(7, ge=1, le=90, description="Number of days to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get daily KPIs for the last N days.

    Args:
        days: Number of days to retrieve
        db: Database session

    Returns:
        List of daily KPI metrics
    """
    results = []
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(days):
        period_start = today - timedelta(days=i)
        period_end = period_start + timedelta(days=1)

        kpi = calculate_kpi_for_period(db, period_start, period_end)
        kpi.period_type = "daily"
        results.append(kpi)

    return results


@router.get("/weekly", response_model=List[KPIMetrics])
async def get_weekly_kpis(
    weeks: int = Query(4, ge=1, le=52, description="Number of weeks to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get weekly KPIs for the last N weeks.

    Args:
        weeks: Number of weeks to retrieve
        db: Database session

    Returns:
        List of weekly KPI metrics
    """
    results = []
    now = datetime.utcnow()
    current_week_start = now - timedelta(days=now.weekday())
    current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(weeks):
        period_start = current_week_start - timedelta(weeks=i)
        period_end = period_start + timedelta(days=7)

        kpi = calculate_kpi_for_period(db, period_start, period_end)
        kpi.period_type = "weekly"
        results.append(kpi)

    return results


@router.get("/monthly", response_model=List[KPIMetrics])
async def get_monthly_kpis(
    months: int = Query(3, ge=1, le=12, description="Number of months to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get monthly KPIs for the last N months.

    Args:
        months: Number of months to retrieve
        db: Database session

    Returns:
        List of monthly KPI metrics
    """
    results = []
    now = datetime.utcnow()

    for i in range(months):
        # Calculate month boundaries
        if i == 0:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            period_start = now.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate period end (first day of next month)
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)

        kpi = calculate_kpi_for_period(db, period_start, period_end)
        kpi.period_type = "monthly"
        results.append(kpi)

    return results


@router.get("/custom", response_model=KPIMetrics)
async def get_custom_kpis(
    start_date: datetime = Query(..., description="Period start date"),
    end_date: datetime = Query(..., description="Period end date"),
    db: Session = Depends(get_db)
):
    """
    Get KPIs for a custom date range.

    Args:
        start_date: Period start
        end_date: Period end
        db: Database session

    Returns:
        KPI metrics for the period
    """
    if end_date <= start_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    kpi = calculate_kpi_for_period(db, start_date, end_date)
    return kpi


if __name__ == "__main__":
    print("KPI router initialized successfully!")
