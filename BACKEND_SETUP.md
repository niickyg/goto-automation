# GoTo Call Automation System - Backend Setup Guide

## Overview

Production-ready backend system for automated call processing with:
- **Webhook handling** for GoTo Connect call events
- **AI transcription** using OpenAI Whisper
- **Intelligent analysis** with GPT-4 for summaries, sentiment, and action items
- **Multi-channel notifications** (Slack & Email)
- **RESTful API** for call management and KPI analytics
- **Comprehensive testing** with pytest

## Architecture

```
┌─────────────────┐
│  GoTo Connect   │
│   (Webhooks)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  FastAPI Server │◄────►│  PostgreSQL  │
│   (webhooks.py) │      │   Database   │
└────────┬────────┘      └──────────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌─────┐  ┌─────────┐ ┌──────┐
│Whisper │ │GPT-4│  │  Slack  │ │Email │
│  API   │ │ API │  │Webhook  │ │SMTP  │
└────────┘ └─────┘  └─────────┘ └──────┘
```

## Project Structure

```
backend/
├── __init__.py           # Package initialization
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── database.py          # SQLAlchemy models & repositories
├── webhooks.py          # GoTo webhook handler
├── transcription.py     # OpenAI Whisper integration
├── ai_analysis.py       # GPT-4 analysis service
├── notifications.py     # Slack & Email notifications
├── calls.py             # Calls API router
├── actions.py           # Action items API router
├── kpi.py               # KPI analytics router
├── .env.example         # Environment template
└── requirements.txt     # Python dependencies

database/
└── schema.sql           # PostgreSQL database schema

tests/
├── test_webhooks.py     # Webhook unit tests
└── mock_call.json       # Sample webhook payload
```

## Prerequisites

### System Requirements
- **Python 3.10+**
- **PostgreSQL 14+**
- **FFmpeg** (for audio processing)

### API Keys Required
- **GoTo Connect API Key** (with webhook access)
- **OpenAI API Key** (for Whisper & GPT-4)
- **Slack Webhook URL** or **Bot Token** (optional)
- **SMTP Credentials** (optional)

## Installation

### 1. Clone and Setup

```bash
cd /home/user0/goto-automation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y ffmpeg postgresql-client
```

### 2. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createdb goto_automation

# Apply schema
psql -U postgres -d goto_automation -f database/schema.sql

# Verify tables created
psql -U postgres -d goto_automation -c "\dt"
```

### 3. Environment Configuration

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit with your credentials
nano backend/.env
```

**Required Configuration:**

```env
# GoTo Connect
GOTO_API_KEY=your_goto_api_key_here
GOTO_WEBHOOK_SECRET=your_webhook_secret_here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/goto_automation
```

**Optional Configuration:**

```env
# Slack (at least one required for notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# OR
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=#call-summaries

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-email-password
SMTP_FROM_EMAIL=noreply@yourcompany.com
NOTIFICATION_EMAIL_RECIPIENTS=user1@company.com,user2@company.com
```

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
python -m backend.main

# Server runs on http://0.0.0.0:8000
```

### Production Mode

```bash
# Set production environment
export APP_ENV=production

# Run with Gunicorn (install first: pip install gunicorn)
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info
```

### Using Docker (Alternative)

```bash
# Build image
docker build -t goto-automation .

# Run container
docker run -d \
  --name goto-automation \
  -p 8000:8000 \
  --env-file backend/.env \
  goto-automation
```

## API Documentation

Once running, access interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Webhooks
- `POST /webhooks/goto/call-ended` - GoTo webhook receiver
- `GET /webhooks/health` - Webhook health check

#### Calls
- `GET /api/calls/` - List calls (paginated)
- `GET /api/calls/{call_id}` - Get call details
- `GET /api/calls/{call_id}/transcript` - Get transcript

#### Action Items
- `GET /api/actions/` - List action items
- `PATCH /api/actions/{action_id}` - Update action item
- `POST /api/actions/{action_id}/complete` - Mark complete

#### KPIs
- `GET /api/kpi/dashboard?period=today` - Dashboard metrics
- `GET /api/kpi/daily?days=7` - Daily metrics
- `GET /api/kpi/weekly?weeks=4` - Weekly metrics

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_webhooks.py -v
```

### Manual Testing

```bash
# Test webhook endpoint with mock data
curl -X POST http://localhost:8000/webhooks/goto/call-ended \
  -H "Content-Type: application/json" \
  -H "X-GoTo-Signature: $(echo -n @tests/mock_call.json | openssl dgst -sha256 -hmac 'your-secret')" \
  -d @tests/mock_call.json

# Check health
curl http://localhost:8000/health
```

## Configuration Details

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOTO_API_KEY` | Yes | - | GoTo Connect API key |
| `GOTO_WEBHOOK_SECRET` | Yes | - | Webhook signature secret |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `DATABASE_URL` | Yes | - | PostgreSQL connection URL |
| `SLACK_WEBHOOK_URL` | No | - | Slack incoming webhook |
| `SMTP_HOST` | No | - | SMTP server host |
| `APP_ENV` | No | `development` | Environment (development/production) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `API_PORT` | No | `8000` | Server port |

### Webhook Signature Validation

GoTo webhooks are validated using HMAC-SHA256:

```python
signature = hmac.new(
    secret.encode(),
    payload,
    hashlib.sha256
).hexdigest()
```

Configure the webhook in GoTo Connect Admin:
1. Go to Settings → Webhooks
2. Add new webhook URL: `https://your-domain.com/webhooks/goto/call-ended`
3. Set secret key (use the same value in `GOTO_WEBHOOK_SECRET`)
4. Subscribe to `call.ended` event

## Database Schema

The system uses 4 main tables:

1. **calls** - Call records from GoTo
2. **call_summaries** - AI transcripts and analysis
3. **action_items** - Extracted action items
4. **kpis** - Aggregated metrics

See `/home/user0/goto-automation/database/schema.sql` for complete schema.

## Workflow

1. **Call Ends** → GoTo sends webhook
2. **Webhook Received** → Validated and call record created
3. **Audio Download** → Recording downloaded from GoTo
4. **Transcription** → OpenAI Whisper transcribes audio
5. **Analysis** → GPT-4 generates summary, sentiment, action items
6. **Storage** → Results saved to database
7. **Notifications** → Slack/Email sent with summary
8. **API Access** → Data available via REST API

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health | jq '.components.database'
```

### Logs

```bash
# View application logs
tail -f logs/goto-automation.log

# Or if using systemd
journalctl -u goto-automation -f
```

### Metrics

Access KPI dashboard for system metrics:
- Call volume trends
- Sentiment distribution
- Action item completion rates
- Average urgency scores

## Troubleshooting

### Common Issues

**Database Connection Error:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U postgres -d goto_automation -c "SELECT 1"
```

**OpenAI API Error:**
```bash
# Verify API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**FFmpeg Not Found:**
```bash
# Install FFmpeg
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

## Security Considerations

### Production Deployment

1. **Use HTTPS** - Always use TLS/SSL certificates
2. **Secure Secrets** - Never commit `.env` to version control
3. **Validate Webhooks** - Always verify signatures
4. **Rate Limiting** - Implement rate limiting for public endpoints
5. **Database Security** - Use strong passwords, restrict access
6. **API Keys** - Rotate regularly, use separate keys per environment

### Example Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name api.yourcompany.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review API documentation at `/docs`
3. Run tests to verify functionality
4. Check database schema and migrations

## License

Copyright 2025 - All Rights Reserved
