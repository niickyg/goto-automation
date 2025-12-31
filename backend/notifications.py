"""
Slack and Email notification service.

Sends formatted notifications about call summaries and action items.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime
import httpx

from config import get_settings
from database import Call, CallSummary, ActionItem

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending Slack and email notifications."""

    def __init__(self):
        """Initialize notification service."""
        self.settings = get_settings()

    async def send_call_summary_notification(
        self,
        call: Call,
        summary: CallSummary,
        action_items: List[ActionItem]
    ):
        """
        Send notification about a completed call analysis.

        Args:
            call: Call record
            summary: Call summary with analysis
            action_items: List of action items
        """
        logger.info(f"Sending notification for call {call.goto_call_id}")

        # Send to both Slack and Email concurrently
        tasks = []

        if self.settings.has_slack_configured():
            tasks.append(self._send_slack_notification(call, summary, action_items))

        if self.settings.has_email_configured():
            tasks.append(self._send_email_notification(call, summary, action_items))

        if not tasks:
            logger.warning("No notification channels configured")
            return

        # Send all notifications
        import asyncio
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Notification {i} failed: {result}")
            else:
                logger.info(f"Notification {i} sent successfully")

    async def _send_slack_notification(
        self,
        call: Call,
        summary: CallSummary,
        action_items: List[ActionItem]
    ):
        """Send Slack notification."""
        try:
            message = self._format_slack_message(call, summary, action_items)

            if self.settings.slack_webhook_url:
                # Use webhook
                await self._send_slack_webhook(message)
            elif self.settings.slack_bot_token:
                # Use bot token
                await self._send_slack_bot_message(message)
            else:
                logger.warning("Slack configured but no webhook or bot token")

        except Exception as e:
            logger.error(f"Slack notification failed: {e}", exc_info=True)
            raise

    async def _send_slack_webhook(self, message: dict):
        """Send message via Slack webhook."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.settings.slack_webhook_url,
                json=message
            )
            response.raise_for_status()
            logger.info("Slack webhook message sent")

    async def _send_slack_bot_message(self, message: dict):
        """Send message via Slack bot API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.settings.slack_bot_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": self.settings.slack_channel,
                    **message
                }
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error')}")
            logger.info("Slack bot message sent")

    def _format_slack_message(
        self,
        call: Call,
        summary: CallSummary,
        action_items: List[ActionItem]
    ) -> dict:
        """Format message for Slack."""
        # Emoji for sentiment
        sentiment_emoji = {
            "positive": ":smile:",
            "neutral": ":neutral_face:",
            "negative": ":disappointed:"
        }

        # Urgency indicator
        urgency_text = "🔴" * summary.urgency_score + "⚪" * (5 - summary.urgency_score)

        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📞 Call Summary - {call.caller_name or call.caller_number}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Call ID:*\n{call.goto_call_id[:20]}..."
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Direction:*\n{call.direction.value.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Duration:*\n{call.duration_seconds // 60}m {call.duration_seconds % 60}s"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{call.start_time.strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary.summary}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Sentiment:*\n{sentiment_emoji.get(summary.sentiment.value, ':question:')} {summary.sentiment.value.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Urgency:*\n{urgency_text} {summary.urgency_score}/5"
                    }
                ]
            }
        ]

        # Add action items if any
        if action_items:
            action_items_text = "\n".join([
                f"• {item.description} (Priority: {item.priority}/5)"
                for item in action_items[:5]  # Show first 5
            ])
            if len(action_items) > 5:
                action_items_text += f"\n_...and {len(action_items) - 5} more_"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Items ({len(action_items)}):*\n{action_items_text}"
                }
            })

        return {"blocks": blocks}

    async def _send_email_notification(
        self,
        call: Call,
        summary: CallSummary,
        action_items: List[ActionItem]
    ):
        """Send email notification."""
        try:
            # Format email
            subject = f"Call Summary: {call.caller_name or call.caller_number} - {summary.sentiment.value.title()}"
            html_body = self._format_email_html(call, summary, action_items)
            text_body = self._format_email_text(call, summary, action_items)

            # Send email
            await self._send_email(
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                recipients=self.settings.notification_email_recipients
            )

            logger.info("Email notification sent")

        except Exception as e:
            logger.error(f"Email notification failed: {e}", exc_info=True)
            raise

    async def _send_email(
        self,
        subject: str,
        html_body: str,
        text_body: str,
        recipients: List[str]
    ):
        """Send email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.settings.smtp_from_email
        msg["To"] = ", ".join(recipients)

        # Attach both text and HTML versions
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Send via SMTP
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)

    def _format_email_html(
        self,
        call: Call,
        summary: CallSummary,
        action_items: List[ActionItem]
    ) -> str:
        """Format HTML email body."""
        action_items_html = ""
        if action_items:
            items_list = "\n".join([
                f"<li><strong>{item.description}</strong> (Priority: {item.priority}/5)"
                + (f" - Assigned to: {item.assigned_to}" if item.assigned_to else "")
                + "</li>"
                for item in action_items
            ])
            action_items_html = f"""
            <h3>Action Items ({len(action_items)})</h3>
            <ul>
                {items_list}
            </ul>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4A90E2; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 20px 0; }}
                .info-item {{ padding: 10px; background-color: #f5f5f5; border-radius: 5px; }}
                .sentiment-positive {{ color: #4CAF50; }}
                .sentiment-neutral {{ color: #FF9800; }}
                .sentiment-negative {{ color: #F44336; }}
                .urgency {{ color: #FF5722; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📞 Call Summary</h1>
            </div>
            <div class="content">
                <h2>{call.caller_name or call.caller_number}</h2>

                <div class="info-grid">
                    <div class="info-item">
                        <strong>Call ID:</strong><br>
                        {call.goto_call_id}
                    </div>
                    <div class="info-item">
                        <strong>Direction:</strong><br>
                        {call.direction.value.title()}
                    </div>
                    <div class="info-item">
                        <strong>Duration:</strong><br>
                        {call.duration_seconds // 60}m {call.duration_seconds % 60}s
                    </div>
                    <div class="info-item">
                        <strong>Time:</strong><br>
                        {call.start_time.strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>

                <h3>Summary</h3>
                <p>{summary.summary}</p>

                <div class="info-grid">
                    <div class="info-item">
                        <strong>Sentiment:</strong><br>
                        <span class="sentiment-{summary.sentiment.value}">
                            {summary.sentiment.value.title()}
                        </span>
                    </div>
                    <div class="info-item">
                        <strong>Urgency:</strong><br>
                        <span class="urgency">{summary.urgency_score}/5</span>
                    </div>
                </div>

                {action_items_html}

                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from the GoTo Call Automation System.
                    Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                </p>
            </div>
        </body>
        </html>
        """
        return html

    def _format_email_text(
        self,
        call: Call,
        summary: CallSummary,
        action_items: List[ActionItem]
    ) -> str:
        """Format plain text email body."""
        lines = [
            "CALL SUMMARY",
            "=" * 60,
            "",
            f"Caller: {call.caller_name or call.caller_number}",
            f"Call ID: {call.goto_call_id}",
            f"Direction: {call.direction.value.title()}",
            f"Duration: {call.duration_seconds // 60}m {call.duration_seconds % 60}s",
            f"Time: {call.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 60,
            summary.summary,
            "",
            f"Sentiment: {summary.sentiment.value.title()}",
            f"Urgency: {summary.urgency_score}/5",
            "",
        ]

        if action_items:
            lines.append(f"ACTION ITEMS ({len(action_items)})")
            lines.append("-" * 60)
            for item in action_items:
                lines.append(f"• {item.description} (Priority: {item.priority}/5)")
                if item.assigned_to:
                    lines.append(f"  Assigned to: {item.assigned_to}")
            lines.append("")

        lines.append("-" * 60)
        lines.append("This is an automated notification from the GoTo Call Automation System.")
        lines.append(f"Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        return "\n".join(lines)

    async def send_daily_digest(self, calls_count: int, summaries: List[dict]):
        """
        Send daily digest email/Slack message.

        Args:
            calls_count: Total calls processed today
            summaries: List of summary data
        """
        logger.info(f"Sending daily digest: {calls_count} calls")

        subject = f"Daily Call Summary Digest - {calls_count} calls"
        # Implementation similar to above but with aggregated data
        # TODO: Implement daily digest formatting


# Global service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


if __name__ == "__main__":
    # Test notifications
    import asyncio
    from config import configure_logging

    configure_logging()
    print("Notification service initialized successfully!")
