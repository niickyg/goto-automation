"""
Unit tests for webhook handling.

Tests webhook signature validation, payload parsing, and call processing.
"""

import pytest
import json
import hmac
import hashlib
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, AsyncMock

# Import the application components
from backend.webhooks import (
    router,
    validate_webhook_signature,
    WebhookCallData,
    GoToWebhook,
)
from backend.database import Base, get_db, Call, CallRepository
from backend.config import get_settings


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create a test client with database override."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    # Override database dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)


@pytest.fixture
def mock_webhook_payload():
    """Load mock webhook payload."""
    with open("/home/user0/goto-automation/tests/mock_call.json", "r") as f:
        return json.load(f)


@pytest.fixture
def webhook_secret():
    """Test webhook secret."""
    return "test-webhook-secret-key"


class TestWebhookSignatureValidation:
    """Test webhook signature validation."""

    def test_valid_signature(self, webhook_secret):
        """Test that valid signatures are accepted."""
        payload = b'{"test": "data"}'
        signature = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        assert validate_webhook_signature(payload, signature, webhook_secret)

    def test_invalid_signature(self, webhook_secret):
        """Test that invalid signatures are rejected."""
        payload = b'{"test": "data"}'
        invalid_signature = "invalid_signature_here"

        assert not validate_webhook_signature(payload, invalid_signature, webhook_secret)

    def test_missing_signature(self, webhook_secret):
        """Test that missing signatures are rejected."""
        payload = b'{"test": "data"}'

        assert not validate_webhook_signature(payload, None, webhook_secret)

    def test_tampered_payload(self, webhook_secret):
        """Test that tampered payloads are rejected."""
        original_payload = b'{"test": "data"}'
        tampered_payload = b'{"test": "tampered"}'

        signature = hmac.new(
            webhook_secret.encode(),
            original_payload,
            hashlib.sha256
        ).hexdigest()

        assert not validate_webhook_signature(tampered_payload, signature, webhook_secret)


class TestWebhookPayloadParsing:
    """Test webhook payload parsing."""

    def test_parse_valid_payload(self, mock_webhook_payload):
        """Test parsing of valid webhook payload."""
        webhook = GoToWebhook(**mock_webhook_payload)

        assert webhook.event_type == "call.ended"
        assert webhook.data.call_id == "GOTO-CALL-123456789"
        assert webhook.data.direction == "inbound"
        assert webhook.data.caller.name == "John Smith"
        assert webhook.data.duration == 345

    def test_parse_payload_with_missing_optional_fields(self):
        """Test parsing payload with missing optional fields."""
        minimal_payload = {
            "event_type": "call.ended",
            "timestamp": "2025-01-15T14:30:45Z",
            "data": {
                "call_id": "TEST-123",
                "direction": "outbound",
                "start_time": "2025-01-15T14:25:00Z",
                "duration": 100,
                "status": "completed"
            }
        }

        webhook = GoToWebhook(**minimal_payload)
        assert webhook.data.caller is None
        assert webhook.data.called is None
        assert webhook.data.recording_url is None

    def test_parse_invalid_payload(self):
        """Test that invalid payloads raise validation errors."""
        invalid_payload = {
            "event_type": "call.ended",
            # Missing required fields
        }

        with pytest.raises(Exception):  # Pydantic validation error
            GoToWebhook(**invalid_payload)


class TestWebhookEndpoint:
    """Test webhook HTTP endpoint."""

    @patch("backend.webhooks.get_settings")
    def test_webhook_with_valid_signature(
        self,
        mock_get_settings,
        client,
        mock_webhook_payload,
        webhook_secret
    ):
        """Test webhook endpoint accepts valid signatures."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.goto_webhook_secret = webhook_secret
        mock_get_settings.return_value = mock_settings

        # Create signature
        payload_bytes = json.dumps(mock_webhook_payload).encode()
        signature = hmac.new(
            webhook_secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Make request
        response = client.post(
            "/webhooks/goto/call-ended",
            content=payload_bytes,
            headers={
                "X-GoTo-Signature": signature,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["call_id"] == "GOTO-CALL-123456789"

    @patch("backend.webhooks.get_settings")
    def test_webhook_with_invalid_signature(
        self,
        mock_get_settings,
        client,
        mock_webhook_payload,
        webhook_secret
    ):
        """Test webhook endpoint rejects invalid signatures."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.goto_webhook_secret = webhook_secret
        mock_get_settings.return_value = mock_settings

        # Make request with invalid signature
        payload_bytes = json.dumps(mock_webhook_payload).encode()
        response = client.post(
            "/webhooks/goto/call-ended",
            content=payload_bytes,
            headers={
                "X-GoTo-Signature": "invalid_signature",
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    @patch("backend.webhooks.get_settings")
    def test_webhook_creates_call_record(
        self,
        mock_get_settings,
        client,
        test_db,
        mock_webhook_payload,
        webhook_secret
    ):
        """Test that webhook creates a call record in database."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.goto_webhook_secret = webhook_secret
        mock_get_settings.return_value = mock_settings

        # Create signature
        payload_bytes = json.dumps(mock_webhook_payload).encode()
        signature = hmac.new(
            webhook_secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Make request
        response = client.post(
            "/webhooks/goto/call-ended",
            content=payload_bytes,
            headers={
                "X-GoTo-Signature": signature,
                "Content-Type": "application/json"
            }
        )

        assert response.status_code == 200

        # Verify call was created in database
        call = CallRepository.get_by_goto_id(test_db, "GOTO-CALL-123456789")
        assert call is not None
        assert call.caller_name == "John Smith"
        assert call.duration_seconds == 345
        assert call.recording_url is not None

    @patch("backend.webhooks.get_settings")
    def test_webhook_ignores_duplicate_calls(
        self,
        mock_get_settings,
        client,
        test_db,
        mock_webhook_payload,
        webhook_secret
    ):
        """Test that duplicate webhook calls are ignored."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.goto_webhook_secret = webhook_secret
        mock_get_settings.return_value = mock_settings

        # Create signature
        payload_bytes = json.dumps(mock_webhook_payload).encode()
        signature = hmac.new(
            webhook_secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-GoTo-Signature": signature,
            "Content-Type": "application/json"
        }

        # First request
        response1 = client.post(
            "/webhooks/goto/call-ended",
            content=payload_bytes,
            headers=headers
        )
        assert response1.status_code == 200
        assert response1.json()["status"] == "accepted"

        # Second request (duplicate)
        response2 = client.post(
            "/webhooks/goto/call-ended",
            content=payload_bytes,
            headers=headers
        )
        assert response2.status_code == 200
        assert response2.json()["status"] == "duplicate"

    def test_webhook_health_endpoint(self, client):
        """Test webhook health check endpoint."""
        response = client.get("/webhooks/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "webhook-handler"


class TestBackgroundProcessing:
    """Test background call processing."""

    @pytest.mark.asyncio
    @patch("backend.webhooks.get_transcription_service")
    @patch("backend.webhooks.get_analysis_service")
    @patch("backend.webhooks.get_notification_service")
    async def test_process_call_recording(
        self,
        mock_notification_service,
        mock_analysis_service,
        mock_transcription_service,
        test_db
    ):
        """Test complete call processing workflow."""
        from backend.webhooks import process_call_recording
        from backend.database import CallDirection, SummaryRepository

        # Create a test call
        call = CallRepository.create(
            test_db,
            goto_call_id="TEST-CALL-001",
            direction=CallDirection.INBOUND,
            caller_name="Test Caller",
            start_time=datetime.utcnow(),
            duration_seconds=300,
            recording_url="https://example.com/recording.mp3"
        )

        # Mock transcription service
        mock_transcription = AsyncMock()
        mock_transcription.transcribe_from_url = AsyncMock(return_value={
            "text": "This is a test transcript of the call.",
            "language": "en",
            "duration": 300,
            "file_size_bytes": 1024000
        })
        mock_transcription_service.return_value = mock_transcription

        # Mock analysis service
        mock_analysis = AsyncMock()
        mock_analysis_result = Mock()
        mock_analysis_result.summary = "Test call summary"
        mock_analysis_result.sentiment = "positive"
        mock_analysis_result.urgency_score = 3
        mock_analysis_result.key_topics = ["topic1", "topic2"]
        mock_analysis_result.action_items = []
        mock_analysis.analyze_call = AsyncMock(return_value=mock_analysis_result)
        mock_analysis_service.return_value = mock_analysis

        # Mock notification service
        mock_notification = AsyncMock()
        mock_notification.send_call_summary_notification = AsyncMock()
        mock_notification_service.return_value = mock_notification

        # Process the call
        await process_call_recording(call.id, call.recording_url, test_db)

        # Verify transcript was created
        summary = SummaryRepository.get_by_call_id(test_db, call.id)
        assert summary is not None
        assert summary.transcript == "This is a test transcript of the call."
        assert summary.summary == "Test call summary"
        assert str(summary.sentiment) == "positive"

        # Verify services were called
        mock_transcription.transcribe_from_url.assert_called_once()
        mock_analysis.analyze_call.assert_called_once()
        mock_notification.send_call_summary_notification.assert_called_once()


def test_webhook_routes_registered():
    """Test that all expected webhook routes are registered."""
    from backend.webhooks import router

    route_paths = [route.path for route in router.routes]

    assert "/webhooks/goto/call-ended" in route_paths
    assert "/webhooks/health" in route_paths
    assert "/webhooks/goto/manual-process/{call_id}" in route_paths


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
