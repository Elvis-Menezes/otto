#!/bin/bash

# =============================================================================
# Otto Bot Creator - Production Startup Script
# =============================================================================
#
# This script starts all services required for the Otto Bot Creator:
# 1. Parlant Server (port 8800) - The AI agent engine with MongoDB backing
# 2. API Server (port 8801) - REST API for web frontend
# 3. Web Server (port 3000) - Static files for the web UI
#
# Prerequisites:
# - Python 3.10+
# - MongoDB running (local or Atlas)
# - OpenAI API key configured
# - Dependencies installed: pip install -r requirements.txt
#
# Usage:
#   ./start_otto.sh          # Start all services
#   ./start_otto.sh parlant  # Start only Parlant server
#   ./start_otto.sh api      # Start only API server
#   ./start_otto.sh web      # Start only web server
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default ports
PARLANT_PORT=${PARLANT_PORT:-8800}
API_PORT=${API_PORT:-8801}
WEB_PORT=${WEB_PORT:-3000}

print_banner() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "    Otto Bot Creator - Production Mode"
    echo "=============================================="
    echo -e "${NC}"
}

check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required${NC}"
        exit 1
    fi
    
    # Check MongoDB URI
    if [ -z "$MONGODB_URI" ]; then
        echo -e "${RED}Error: MONGODB_URI not set. Please configure in .env${NC}"
        exit 1
    fi
    
    # Check OpenAI API Key
    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}Error: OPENAI_API_KEY not set. Please configure in .env${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All requirements met${NC}"
}

start_parlant() {
    echo -e "${BLUE}Starting Parlant Server on port $PARLANT_PORT...${NC}"
    python3 server.py &
    PARLANT_PID=$!
    echo -e "${GREEN}✓ Parlant Server started (PID: $PARLANT_PID)${NC}"
}

start_api() {
    echo -e "${BLUE}Starting API Server on port $API_PORT...${NC}"
    python3 -m uvicorn api_server:app --host 0.0.0.0 --port $API_PORT &
    API_PID=$!
    echo -e "${GREEN}✓ API Server started (PID: $API_PID)${NC}"
}

start_web() {
    echo -e "${BLUE}Starting Web Server on port $WEB_PORT...${NC}"
    python3 -m http.server $WEB_PORT --directory web &
    WEB_PID=$!
    echo -e "${GREEN}✓ Web Server started (PID: $WEB_PID)${NC}"
}

wait_for_parlant() {
    echo -e "${YELLOW}Waiting for Parlant to be ready...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:$PARLANT_PORT/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Parlant is ready${NC}"
            return 0
        fi
        sleep 1
    done
    echo -e "${RED}Warning: Parlant health check timed out${NC}"
    return 1
}

print_status() {
    echo ""
    echo -e "${GREEN}=============================================="
    echo "    All services started successfully!"
    echo "=============================================="
    echo ""
    echo "  📡 Parlant Server:  http://localhost:$PARLANT_PORT"
    echo "  🔌 API Server:      http://localhost:$API_PORT"
    echo "  🌐 Web Dashboard:   http://localhost:$WEB_PORT"
    echo ""
    echo "  📖 API Docs:        http://localhost:$API_PORT/docs"
    echo ""
    echo "=============================================="
    echo -e "${NC}"
    echo ""
    echo "Press Ctrl+C to stop all services"
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    [ -n "$PARLANT_PID" ] && kill $PARLANT_PID 2>/dev/null && echo "Stopped Parlant"
    [ -n "$API_PID" ] && kill $API_PID 2>/dev/null && echo "Stopped API Server"
    [ -n "$WEB_PID" ] && kill $WEB_PID 2>/dev/null && echo "Stopped Web Server"
    
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Handle Ctrl+C
trap cleanup SIGINT SIGTERM

# Main
print_banner

case "${1:-all}" in
    parlant)
        check_requirements
        start_parlant
        wait
        ;;
    api)
        start_api
        wait
        ;;
    web)
        start_web
        wait
        ;;
    all|*)
        check_requirements
        
        # Start all services
        start_parlant
        sleep 3
        
        # Wait for Parlant before starting API
        wait_for_parlant
        
        start_api
        sleep 2
        
        start_web
        
        print_status
        
        # Wait for all processes
        wait
        ;;
esac
