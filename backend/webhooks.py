"""
GoTo Connect webhook handler.

Receives call-ended webhooks, validates signatures, and triggers async processing.
"""

import logging
import hmac
import hashlib
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import get_settings
from database import (
    get_db,
    Call,
    CallSummary,
    CallRepository,
    SummaryRepository,
    ActionItemRepository,
    CallDirection,
)
from transcription import get_transcription_service
from ai_analysis import get_analysis_service
from notifications import get_notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Request/Response Models
class CallParticipant(BaseModel):
    """Call participant information."""
    number: Optional[str] = None
    name: Optional[str] = None


class WebhookCallData(BaseModel):
    """Call data from GoTo webhook."""
    call_id: str = Field(..., description="Unique call identifier")
    direction: str = Field(..., description="Call direction: inbound or outbound")
    caller: Optional[CallParticipant] = None
    called: Optional[CallParticipant] = None
    start_time: str = Field(..., description="Call start time ISO format")
    end_time: Optional[str] = None
    duration: int = Field(..., description="Duration in seconds")
    recording_url: Optional[str] = None
    status: str = Field(..., description="Call status")


class GoToWebhook(BaseModel):
    """GoTo Connect webhook payload."""
    event_type: str = Field(..., description="Event type (e.g., call.ended)")
    timestamp: str = Field(..., description="Event timestamp ISO format")
    data: WebhookCallData = Field(..., description="Call data")


class WebhookResponse(BaseModel):
    """Webhook response."""
    status: str
    message: str
    call_id: Optional[str] = None


# Webhook signature validation
def validate_webhook_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str
) -> bool:
    """
    Validate GoTo webhook signature.

    Args:
        payload: Raw request body
        signature: Signature from header
        secret: Webhook secret

    Returns:
        True if signature is valid
    """
    if not signature:
        logger.warning("No signature provided in webhook")
        return False

    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)


# Background processing
async def process_call_recording(
    call_id: int,
    recording_url: str,
    db_session: Session
):
    """
    Process call recording in background.

    Steps:
    1. Download and transcribe audio
    2. Analyze transcript with GPT-4
    3. Save results to database
    4. Send notifications

    Args:
        call_id: Database call ID
        recording_url: URL to download recording
        db_session: Database session
    """
    logger.info(f"Processing call recording for call_id={call_id}")

    try:
        # Get call from database
        call = CallRepository.get_by_id(db_session, call_id)
        if not call:
            logger.error(f"Call not found: {call_id}")
            return

        # Get or create summary record
        summary = SummaryRepository.get_by_call_id(db_session, call_id)
        if not summary:
            summary = SummaryRepository.create(
                db_session,
                call_id=call_id,
                transcription_started_at=datetime.utcnow()
            )
        else:
            summary.transcription_started_at = datetime.utcnow()
            db_session.commit()

        # Step 1: Transcribe audio
        logger.info(f"Starting transcription for call {call.goto_call_id}")
        transcription_service = get_transcription_service()

        # Build auth headers if needed
        settings = get_settings()
        headers = {"Authorization": f"Bearer {settings.goto_api_key}"}

        transcription_result = await transcription_service.transcribe_from_url(
            url=recording_url,
            headers=headers
        )

        transcript = transcription_result["text"]
        logger.info(f"Transcription complete: {len(transcript)} chars")

        # Update summary with transcript
        summary.transcript = transcript
        summary.transcription_completed_at = datetime.utcnow()
        summary.analysis_started_at = datetime.utcnow()
        db_session.commit()

        # Step 2: Analyze with GPT-4
        logger.info(f"Starting AI analysis for call {call.goto_call_id}")
        analysis_service = get_analysis_service()

        # Build metadata for context
        metadata = {
            "caller_name": call.caller_name,
            "called_name": call.called_name,
            "duration_seconds": call.duration_seconds,
            "direction": call.direction.value
        }

        analysis = await analysis_service.analyze_call(transcript, metadata)

        # Update summary with analysis
        summary.summary = analysis.summary
        summary.sentiment = analysis.sentiment
        summary.urgency_score = analysis.urgency_score
        summary.key_topics = ",".join(analysis.key_topics)  # Store as CSV
        summary.analysis_completed_at = datetime.utcnow()
        db_session.commit()

        logger.info(f"Analysis complete for call {call.goto_call_id}")

        # Step 3: Save action items
        action_items = []
        for ai_action_item in analysis.action_items:
            action_item = ActionItemRepository.create(
                db_session,
                call_id=call_id,
                description=ai_action_item.description,
                assigned_to=ai_action_item.assigned_to,
                priority=ai_action_item.priority
            )
            action_items.append(action_item)

        logger.info(f"Created {len(action_items)} action items")

        # Step 4: Send notifications
        logger.info(f"Sending notifications for call {call.goto_call_id}")
        notification_service = get_notification_service()

        await notification_service.send_call_summary_notification(
            call=call,
            summary=summary,
            action_items=action_items
        )

        logger.info(f"Successfully processed call {call.goto_call_id}")

    except Exception as e:
        logger.error(f"Error processing call {call_id}: {e}", exc_info=True)
        # Update summary to mark failure
        try:
            if summary:
                db_session.rollback()
                # Could add error tracking fields here
                db_session.commit()
        except:
            pass


# Webhook endpoint
@router.post("/goto/call-ended", response_model=WebhookResponse)
async def handle_call_ended_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle call-ended webhook from GoTo Connect.

    Validates signature, saves call data, and triggers async processing.

    Args:
        request: FastAPI request
        background_tasks: Background task handler
        db: Database session

    Returns:
        Webhook response

    Raises:
        HTTPException: If validation fails
    """
    settings = get_settings()

    # Get raw body for signature validation
    body = await request.body()

    # Validate signature
    signature = request.headers.get("X-GoTo-Signature")
    if not validate_webhook_signature(body, signature, settings.goto_webhook_secret):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse webhook payload
    try:
        webhook_data = GoToWebhook.parse_raw(body)
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Validate event type
    if webhook_data.event_type != "call.ended":
        logger.info(f"Ignoring event type: {webhook_data.event_type}")
        return WebhookResponse(
            status="ignored",
            message=f"Event type {webhook_data.event_type} not handled"
        )

    call_data = webhook_data.data
    logger.info(f"Received call-ended webhook: {call_data.call_id}")

    # Check if call already exists
    existing_call = CallRepository.get_by_goto_id(db, call_data.call_id)
    if existing_call:
        logger.info(f"Call {call_data.call_id} already processed")
        return WebhookResponse(
            status="duplicate",
            message="Call already processed",
            call_id=call_data.call_id
        )

    # Parse timestamps
    try:
        start_time = datetime.fromisoformat(
            call_data.start_time.replace("Z", "+00:00")
        )
        end_time = None
        if call_data.end_time:
            end_time = datetime.fromisoformat(
                call_data.end_time.replace("Z", "+00:00")
            )
    except Exception as e:
        logger.error(f"Failed to parse timestamps: {e}")
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # Determine call direction
    direction = CallDirection.INBOUND
    if call_data.direction.lower() == "outbound":
        direction = CallDirection.OUTBOUND

    # Create call record
    call = CallRepository.create(
        db,
        goto_call_id=call_data.call_id,
        direction=direction,
        caller_number=call_data.caller.number if call_data.caller else None,
        caller_name=call_data.caller.name if call_data.caller else None,
        called_number=call_data.called.number if call_data.called else None,
        called_name=call_data.called.name if call_data.called else None,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=call_data.duration,
        recording_url=call_data.recording_url,
        webhook_received_at=datetime.utcnow()
    )

    logger.info(f"Created call record: {call.id}")

    # Trigger background processing if recording available
    if call_data.recording_url:
        logger.info(f"Scheduling background processing for call {call.id}")
        background_tasks.add_task(
            process_call_recording,
            call.id,
            call_data.recording_url,
            db
        )
    else:
        logger.warning(f"No recording URL for call {call_data.call_id}")

    return WebhookResponse(
        status="accepted",
        message="Call webhook received and processing started",
        call_id=call_data.call_id
    )


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhooks."""
    return {
        "status": "healthy",
        "service": "webhook-handler",
        "timestamp": datetime.utcnow().isoformat()
    }


# Manual trigger for testing
@router.post("/goto/manual-process/{call_id}")
async def manual_process_call(
    call_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger processing for a call (for testing/retry).

    Args:
        call_id: Database call ID
        background_tasks: Background task handler
        db: Database session

    Returns:
        Response with processing status
    """
    call = CallRepository.get_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    if not call.recording_url:
        raise HTTPException(status_code=400, detail="No recording URL available")

    logger.info(f"Manual processing triggered for call {call_id}")

    background_tasks.add_task(
        process_call_recording,
        call.id,
        call.recording_url,
        db
    )

    return {
        "status": "processing",
        "message": f"Processing started for call {call_id}",
        "call_id": call.goto_call_id
    }


if __name__ == "__main__":
    # Test webhook validation
    secret = "test-secret"
    payload = b'{"event_type": "call.ended", "data": {}}'
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    assert validate_webhook_signature(payload, signature, secret)
    assert not validate_webhook_signature(payload, "invalid", secret)

    print("Webhook validation tests passed!")
