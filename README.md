# GoTo Call Automation

Call recording transcription and analysis system for GoTo Connect. Automatically transcribes calls, analyzes sentiment, and extracts action items.

## Setup

```bash
./setup.sh
```

This builds the Docker containers, starts services, and opens the dashboard at http://localhost:3000.

## What It Does

- Receives webhooks from GoTo Connect when calls end
- Downloads and transcribes call recordings using OpenAI Whisper
- Analyzes transcripts with GPT-4 for sentiment and action items
- Displays everything in a React dashboard

## Stack

**Backend:** FastAPI, PostgreSQL, Redis, OpenAI
**Frontend:** React, Vite, TailwindCSS, shadcn/ui

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
GOTO_API_KEY=your_key
OPENAI_API_KEY=your_key
DATABASE_URL=postgresql://goto_user:changeme@postgres:5432/goto_automation
```

## Usage

Start services:
```bash
docker-compose up -d
```

Stop services:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f backend
```

## Features

**Dashboard:**
- Call volume and sentiment charts
- Recent calls list with transcripts
- Action items kanban board
- Dark mode toggle

**Call List:**
- Search and filter calls
- View full transcripts
- Download recordings
- Export to CSV

**Action Items:**
- Drag-and-drop status updates
- Assignable to team members
- Export to CSV

## API

Full docs at http://localhost:8000/docs

Main endpoints:
- `POST /webhooks/goto/call-ended` - Webhook receiver
- `GET /api/calls` - List calls
- `GET /api/actions` - List action items
- `GET /api/kpi/dashboard` - Dashboard stats

## Structure

```
backend/          # FastAPI application
frontend/         # React dashboard
docker-compose.yml
setup.sh
```

## Troubleshooting

**Frontend won't build:**
```bash
cd frontend && npm install && npm run build
docker-compose build frontend
```

**Database issues:**
```bash
docker-compose down -v
./setup.sh
```

**View backend errors:**
```bash
docker logs goto-automation-api
```
