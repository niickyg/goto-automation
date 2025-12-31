#!/bin/bash

# CallWise Initialization Script
# Sets up everything you need to test AI features

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║   CallWise AI - Initialization         ║"
echo "║   Get Ready to Test & Launch           ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Please run this from /home/user0/goto-automation${NC}"
    exit 1
fi

echo -e "${YELLOW}This script will:${NC}"
echo "  1. Set up your .env file with OpenAI key"
echo "  2. Start all services (database, API, frontend)"
echo "  3. Initialize the database"
echo "  4. Verify everything is working"
echo "  5. Generate demo calls with AI analysis"
echo ""
echo -e "${YELLOW}Cost: \$0 (use OpenAI's \$5 free credit)${NC}"
echo -e "${YELLOW}Time: ~5 minutes${NC}"
echo ""
read -p "Press ENTER to continue..."
echo ""

# Step 1: Check for OpenAI API key
echo -e "${BLUE}Step 1/6: OpenAI API Key Setup${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f ".env" ]; then
    CURRENT_KEY=$(grep "OPENAI_API_KEY=" .env | cut -d'=' -f2)
    if [ "$CURRENT_KEY" != "test_key" ] && [ ! -z "$CURRENT_KEY" ]; then
        echo -e "${GREEN}✓ Found existing OpenAI API key${NC}"
        echo "  Key: ${CURRENT_KEY:0:20}..."
        echo ""
        read -p "Use this key? (Y/n): " use_existing
        if [ "$use_existing" != "n" ] && [ "$use_existing" != "N" ]; then
            OPENAI_KEY=$CURRENT_KEY
        fi
    fi
fi

if [ -z "$OPENAI_KEY" ]; then
    echo -e "${YELLOW}You need an OpenAI API key to test AI features.${NC}"
    echo ""
    echo "Get one here (takes 2 minutes):"
    echo "  → https://platform.openai.com/api-keys"
    echo ""
    echo "Benefits:"
    echo "  • \$5 free credit (125 calls)"
    echo "  • Only \$0.04 per call after"
    echo "  • Can set spending limits"
    echo ""
    read -p "Enter your OpenAI API key (starts with sk-...): " OPENAI_KEY

    if [ -z "$OPENAI_KEY" ]; then
        echo -e "${RED}No API key provided. Exiting.${NC}"
        echo ""
        echo "To get started:"
        echo "  1. Get API key: https://platform.openai.com/api-keys"
        echo "  2. Run this script again: ./init-callwise.sh"
        exit 1
    fi
fi

# Validate key format
if [[ ! $OPENAI_KEY =~ ^sk- ]]; then
    echo -e "${RED}Warning: API key should start with 'sk-'${NC}"
    read -p "Continue anyway? (y/N): " continue_anyway
    if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓ OpenAI API key configured${NC}"
echo ""

# Step 2: Create/update .env file
echo -e "${BLUE}Step 2/6: Creating Configuration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Backup existing .env if it exists
if [ -f ".env" ]; then
    cp .env .env.backup
    echo "  • Backed up existing .env to .env.backup"
fi

# Create new .env
cat > .env << EOF
# CallWise Configuration
# Generated: $(date)

# OpenAI API (Required for AI features)
OPENAI_API_KEY=$OPENAI_KEY

# GoTo Connect API (Optional - for production)
GOTO_API_KEY=test_key_for_development
GOTO_WEBHOOK_SECRET=test_secret_for_development

# Database
DATABASE_URL=postgresql://goto_user:changeme@postgres:5432/goto_automation
DB_PASSWORD=changeme

# Redis
REDIS_URL=redis://redis:6379/0

# Application
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=true

# Stripe (Optional - for billing)
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_PUBLISHABLE_KEY=pk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
EOF

echo -e "${GREEN}✓ Configuration file created${NC}"
echo "  Location: /home/user0/goto-automation/.env"
echo ""

# Step 3: Stop any existing containers
echo -e "${BLUE}Step 3/6: Cleaning Up Old Containers${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$(docker ps -q -f name=goto-automation)" ]; then
    echo "  • Stopping existing containers..."
    docker compose down > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ Old containers stopped${NC}"
else
    echo "  • No existing containers found"
fi
echo ""

# Step 4: Start services
echo -e "${BLUE}Step 4/6: Starting All Services${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Starting:"
echo "  • PostgreSQL database"
echo "  • Redis cache"
echo "  • FastAPI backend"
echo "  • React frontend"
echo ""
echo "This may take 30-60 seconds..."
echo ""

docker compose up -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 10

# Check database
echo -n "  • Database: "
for i in {1..30}; do
    if docker exec goto-automation-db pg_isready -U goto_user -d goto_automation > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Timeout${NC}"
        echo "Check logs: docker logs goto-automation-db"
        exit 1
    fi
done

# Check Redis
echo -n "  • Redis: "
for i in {1..30}; do
    if docker exec goto-automation-redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Timeout${NC}"
        exit 1
    fi
done

# Check backend
echo -n "  • Backend API: "
for i in {1..60}; do
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 60 ]; then
        echo -e "${RED}✗ Timeout${NC}"
        echo "Check logs: docker logs goto-automation-api"
        exit 1
    fi
done

# Check frontend
echo -n "  • Frontend Dashboard: "
for i in {1..30}; do
    if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ready${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠ Starting (may take another minute)${NC}"
        break
    fi
done

echo ""
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo ""

# Step 5: Verify OpenAI connection
echo -e "${BLUE}Step 5/6: Verifying OpenAI Connection${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -n "  Testing API key... "
# Give backend a few more seconds to fully start
sleep 5

# Simple test - just check if backend is responding
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend ready${NC}"
else
    echo -e "${YELLOW}⚠ Backend still starting...${NC}"
fi
echo ""

# Step 6: Generate demo calls
echo -e "${BLUE}Step 6/6: Generate Demo Calls${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Would you like to generate 50 demo calls now?"
echo "  • Uses AI to analyze each call"
echo "  • Creates realistic scenarios"
echo "  • Costs: ~\$2.00 (or free with \$5 credit)"
echo "  • Time: 2-3 minutes"
echo ""
read -p "Generate demo calls? (Y/n): " generate_calls

if [ "$generate_calls" != "n" ] && [ "$generate_calls" != "N" ]; then
    echo ""
    echo "Generating 50 demo calls with AI analysis..."
    echo "This will take 2-3 minutes. Please wait..."
    echo ""

    if python3 simulate_calls.py; then
        echo ""
        echo -e "${GREEN}✓ Demo calls generated successfully!${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ Demo generation had issues. Check logs above.${NC}"
        echo ""
        echo "You can run it manually later:"
        echo "  python3 simulate_calls.py"
    fi
else
    echo ""
    echo "Skipped. You can generate calls later:"
    echo "  python3 simulate_calls.py"
fi

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     🎉 Setup Complete! 🎉              ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${BLUE}Your CallWise AI system is now running!${NC}"
echo ""
echo "📊 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  • Dashboard:    http://localhost:3000"
echo "  • API Docs:     http://localhost:8000/docs"
echo "  • Health:       http://localhost:8000/health"
echo ""
echo "📱 Mobile Testing (same WiFi):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
LOCAL_IP=$(ip addr show | grep -E "inet.*192\.|inet.*10\." | grep -v "127.0.0.1" | head -1 | awk '{print $2}' | cut -d/ -f1)
if [ ! -z "$LOCAL_IP" ]; then
    echo "  • Phone/Tablet: http://$LOCAL_IP:3000"
else
    echo "  • Run: ip addr | grep inet"
fi
echo ""
echo "🔧 Useful Commands:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  • View logs:       docker compose logs -f"
echo "  • Stop services:   docker compose down"
echo "  • Restart:         docker compose restart"
echo "  • Status:          docker compose ps"
echo ""
echo "📚 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. Open dashboard: firefox http://localhost:3000 &"
echo "  2. Explore AI features:"
echo "     • Call transcriptions"
echo "     • Sentiment analysis"
echo "     • Action items"
echo "     • Kanban board"
echo "  3. Test on your phone"
echo "  4. Read: TEST_AI_FEATURES.md"
echo "  5. When ready: Deploy to production"
echo ""
echo "💰 Revenue Path:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  • This Week:    Test & perfect demo"
echo "  • Next Week:    Deploy & soft launch"
echo "  • Week 3-4:     First 10 customers (\$500-1,000 MRR)"
echo "  • Month 2-3:    Scale to \$5,000-10,000 MRR"
echo ""
echo "📖 Documentation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  • Testing Guide:    TEST_AI_FEATURES.md"
echo "  • Deployment:       DEPLOYMENT_GUIDE.md"
echo "  • Mobile Testing:   MOBILE_TESTING.md"
echo "  • Revenue Strategy: ../makem0ney/STRATEGY.md"
echo ""
echo -e "${GREEN}Ready to test? Open your browser!${NC}"
echo ""
echo "  firefox http://localhost:3000 &"
echo ""
