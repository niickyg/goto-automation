# GoTo Call Automation System - User-Friendly Dashboard

A production-ready system for automated call recording transcription, AI-powered analysis, and intelligent notifications for GoTo Connect.

## 🚀 One-Command Setup

```bash
cd /home/user0/goto-automation
./setup.sh
```

That's it! The script will:
- ✅ Build all Docker containers
- ✅ Start the database, Redis, backend API, and frontend dashboard
- ✅ Run health checks to ensure everything is working
- ✅ Open the dashboard in your browser automatically

## 📊 What's Included

### Enhanced Features (Phase 1 - COMPLETE ✅)
- [x] **Beautiful Dashboard** with KPI cards showing trends
- [x] **Visual Charts** - Bar charts for call volume, pie charts for sentiment
- [x] **Real-time Updates** - Dashboard auto-refreshes every 10 seconds
- [x] **Professional UI** - Modern sidebar navigation with mobile support
- [x] **Dark Mode Toggle** - Switch between light and dark themes
- [x] **Period Selector** - View data for Today, This Week, or This Month
- [x] **Recent Activity Feed** - See latest calls and pending action items
- [x] **Advanced Call List** - Search, filter, sort, and paginate through calls
- [x] **Call Detail Modal** - View full transcripts, summaries, and recordings
- [x] **Action Items Kanban** - Drag-and-drop task management board
- [x] **Table View** - Alternative list view for action items
- [x] **Export to CSV** - Download calls and action items as CSV files
- [x] **Loading States** - Skeleton screens while data loads
- [x] **Responsive Design** - Works on desktop, tablet, and mobile

### Tech Stack
**Frontend:**
- React 18 + Vite 5 (lightning-fast builds)
- shadcn/ui components (beautiful, accessible UI)
- React Query (smart data fetching with auto-refresh)
- Zustand (simple state management)
- Recharts (interactive charts)
- TailwindCSS (modern styling)

**Backend:**
- FastAPI (high-performance Python API)
- PostgreSQL 15 (reliable data storage)
- Redis 7 (caching & job queue)
- OpenAI Whisper (speech-to-text)
- GPT-4 (AI analysis & summaries)

## 📱 Access Points

After running `./setup.sh`, you can access:

- **Dashboard:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 🎯 Quick Test

1. **Check services are running:**
   ```bash
   docker-compose ps
   ```

2. **Test with a webhook:**
   ```bash
   python3 /tmp/test_webhook.py
   ```

3. **View the call in dashboard:**
   Open http://localhost:3000 and see the test call appear!

## 📂 Project Structure

```
/home/user0/goto-automation/
├── backend/                 # FastAPI application
│   ├── main.py             # API entry point
│   ├── webhooks.py         # GoTo webhook handler
│   ├── calls.py            # Calls API
│   ├── actions.py          # Action items API
│   ├── kpi.py              # Analytics & KPIs
│   ├── ai_analysis.py      # GPT-4 integration
│   ├── transcription.py    # Whisper integration
│   └── notifications.py    # Slack/Email alerts
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── components/     # UI components
│   │   │   ├── Dashboard.jsx    # Main dashboard
│   │   │   ├── Sidebar.jsx      # Navigation
│   │   │   ├── TopBar.jsx       # Header
│   │   │   └── ui/              # shadcn components
│   │   ├── hooks/          # React Query hooks
│   │   ├── store/          # Zustand state
│   │   └── lib/            # Utilities
│   └── Dockerfile
├── docker-compose.yml      # All services
├── setup.sh               # One-command setup ✨
├── .env                   # Configuration
└── INIT.md               # Session recovery info
```

## ⚙️ Configuration

Edit `.env` to configure:

```bash
# GoTo Connect
GOTO_API_KEY=your_key_here
GOTO_WEBHOOK_SECRET=your_secret_here

# OpenAI
OPENAI_API_KEY=your_key_here

# Database (leave as-is for Docker)
DATABASE_URL=postgresql://goto_user:changeme@postgres:5432/goto_automation
```

## 🔄 Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after code changes
docker-compose build
docker-compose up -d

# Run setup again
./setup.sh
```

## 📈 Features Overview

### Dashboard
- **4 KPI Cards:** Total Calls, Avg Duration, Pending Actions, Transcription Rate
- **Call Volume Chart:** 7-day trend with bar chart
- **Sentiment Pie Chart:** Distribution of positive/neutral/negative calls
- **Recent Calls:** Last 10 calls with sentiment badges
- **Pending Actions:** Top 5 action items needing attention
- **Quick Stats:** At-a-glance sentiment and completion metrics

### Sidebar Navigation
- Dashboard (home) - KPI overview with charts
- Calls - Advanced search, filter, sort, and view call details
- Action Items - Kanban board with drag-and-drop task management
- Analytics (advanced reports) - coming soon in Phase 2
- Settings (configuration) - coming soon in Phase 2

### Auto-Refresh
- Dashboard updates every 10 seconds
- Recent calls refresh automatically
- No need to manually reload

## 🎨 UI Features

- **Responsive:** Works on all screen sizes (desktop, tablet, mobile)
- **Dark Mode:** Toggle in top bar (moon/sun icon)
- **Period Selector:** Today / This Week / This Month (global state)
- **Advanced Search:** Debounced search in Call List (500ms delay)
- **Filters:** Sentiment, direction, recording status with badge count
- **Sortable Tables:** Click column headers to sort
- **Pagination:** Navigate through large datasets (20 items per page)
- **Drag & Drop:** Kanban board for action items with status changes
- **Export:** Download calls and action items as CSV
- **Notifications:** Toast messages for all actions (success, error, info)
- **Loading States:** Smooth skeleton screens and loading indicators
- **Modal Dialogs:** Call details, create/edit forms

## 🚧 Next Steps (Phase 2)

**Phase 1 Complete! ✅** All core features are now implemented.

The following features are planned for Phase 2:

- [ ] User Authentication (username/password login)
- [ ] User Roles & Permissions (Admin vs Regular User)
- [ ] Setup Wizard for API keys and initial configuration
- [ ] Advanced Analytics Dashboard with custom reports
- [ ] Real-time WebSocket updates (instead of polling)
- [ ] Email notifications for urgent action items
- [ ] PDF export with formatted reports
- [ ] Team collaboration features (comments, mentions)

## 🔧 Troubleshooting

### Frontend won't start
```bash
cd frontend
npm install
npm run build
docker-compose build frontend
docker-compose up -d frontend
```

### Backend API errors
```bash
docker logs goto-automation-api --tail 50
```

### Database connection issues
```bash
docker exec -it goto-automation-db psql -U goto_user -d goto_automation
```

### Clear everything and start fresh
```bash
docker-compose down -v
./setup.sh
```

## 📝 API Endpoints

See full API documentation at http://localhost:8000/docs

**Key endpoints:**
- `POST /webhooks/goto/call-ended` - Receive call webhooks
- `GET /api/calls` - List all calls
- `GET /api/calls/{id}` - Call details with transcript
- `GET /api/actions` - List action items
- `GET /api/kpi/dashboard?period=week` - Dashboard KPIs

## 💡 Tips

1. **Test Mode:** The system works with test API keys. Real keys needed for production.

2. **Mobile:** The dashboard is fully responsive. Try it on your phone!

3. **Dark Mode:** Click the moon icon in the top bar.

4. **Period Switching:** Use the Today/Week/Month buttons to change timeframes.

5. **Navigation:** Click the GoTo Automation logo to return to dashboard.

## 📞 Support

- Documentation: /home/user0/goto-automation/INIT.md
- Plan: /home/user0/.claude/plans/steady-humming-rose.md
- Logs: `docker-compose logs -f`

## 🎉 You're All Set!

Run `./setup.sh` and enjoy your beautiful, user-friendly call automation dashboard!
