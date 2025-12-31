#!/bin/bash

# GoTo Call Automation - One-Command Setup Script
# This script sets up the entire system with minimal user input

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Banner
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   GoTo Call Automation - Setup Wizard        ║"
echo "║   User-Friendly Dashboard for Small Business  ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker found: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
print_success "Docker Compose found"

# Check if .env exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env from .env.example"
    else
        # Create minimal .env if .env.example doesn't exist
        cat > .env << 'ENVEOF'
# GoTo Connect API
GOTO_API_KEY=test_key_change_me
GOTO_WEBHOOK_SECRET=test_secret_change_me
GOTO_API_BASE_URL=https://api.goto.com/v1

# OpenAI API
OPENAI_API_KEY=test_key_change_me
OPENAI_MODEL=gpt-4-turbo-preview
WHISPER_MODEL=whisper-1

# Database
DATABASE_URL=postgresql://goto_user:changeme@postgres:5432/goto_automation
DB_PASSWORD=changeme
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Application
APP_ENV=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Storage
TEMP_DIR=/tmp/goto-automation
MAX_AUDIO_SIZE_MB=100

# Processing
ASYNC_WORKERS=4
WEBHOOK_TIMEOUT_SECONDS=30
ENVEOF
        print_success "Created default .env file"
    fi
    
    echo ""
    print_warning "IMPORTANT: Edit .env and add your real API keys before production use!"
    print_info "For testing, the default values will work."
    echo ""
    
    read -p "Press Enter to continue with test configuration, or Ctrl+C to exit and edit .env..."
    echo ""
else
    print_success "Using existing .env file"
fi

# Stop any existing containers
print_info "Stopping any existing containers..."
docker-compose down > /dev/null 2>&1 || true
print_success "Cleaned up old containers"

# Build containers
print_info "Building Docker containers (this may take a few minutes)..."
docker-compose build --quiet 2>&1 | grep -v "^#" || docker-compose build
print_success "Containers built successfully"

# Start services
print_info "Starting services..."
docker-compose up -d
print_success "Services started"

# Wait for health checks
print_info "Waiting for services to be healthy..."

# Wait for database
print_info "Waiting for database..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U goto_user -d goto_automation > /dev/null 2>&1; then
        print_success "Database is ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        print_error "Database failed to start"
        docker-compose logs postgres
        exit 1
    fi
done

# Wait for Redis
print_info "Waiting for Redis..."
for i in {1..15}; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
        break
    fi
    sleep 1
done

# Wait for backend API
print_info "Waiting for backend API..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        print_error "Backend API failed to start"
        print_info "Checking backend logs:"
        docker-compose logs --tail=20 backend
        exit 1
    fi
done

# Check if frontend is configured
if docker-compose ps frontend > /dev/null 2>&1; then
    print_info "Waiting for frontend..."
    for i in {1..30}; do
        if curl -sf http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend is ready"
            FRONTEND_READY=true
            break
        fi
        sleep 1
    done
else
    print_warning "Frontend container not configured yet (will be added soon)"
    FRONTEND_READY=false
fi

# Display status
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║          GoTo Automation is Ready! ✓          ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Show running services
print_info "Running services:"
docker-compose ps

echo ""
print_info "Access points:"
echo "  • Backend API:    http://localhost:8000"
echo "  • API Docs:       http://localhost:8000/docs"
echo "  • Health Check:   http://localhost:8000/health"

if [ "$FRONTEND_READY" = true ]; then
    echo "  • Dashboard:      http://localhost:3000"
fi

echo ""
print_info "Quick test:"
echo "  curl http://localhost:8000/health"
echo ""

print_info "View logs:"
echo "  docker-compose logs -f backend"
echo ""

print_info "Stop services:"
echo "  docker-compose down"
echo ""

# Try to open browser
if [ "$FRONTEND_READY" = true ]; then
    print_info "Opening dashboard in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000 2>/dev/null || true
    elif command -v open &> /dev/null; then
        open http://localhost:3000 2>/dev/null || true
    fi
else
    print_info "Opening API docs in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000/docs 2>/dev/null || true
    elif command -v open &> /dev/null; then
        open http://localhost:8000/docs 2>/dev/null || true
    fi
fi

echo ""
print_success "Setup complete! Happy automating! 🚀"
echo ""
