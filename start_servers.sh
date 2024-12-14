#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Python virtual environment is not active${NC}"
    echo -e "${YELLOW}Please activate the virtual environment first:${NC}"
    echo -e "cd backend"
    echo -e "source .venv/bin/activate"
    echo -e "cd .."
    echo -e "Then run this script again"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Kill existing processes on ports if they exist
if check_port 8000; then
    echo -e "${YELLOW}Port 8000 is in use. Killing existing process...${NC}"
    lsof -ti:8000 | xargs kill -9
fi

if check_port 8080; then
    echo -e "${YELLOW}Port 8080 is in use. Killing existing process...${NC}"
    lsof -ti:8080 | xargs kill -9
fi

# Start backend server
echo -e "${GREEN}Starting backend server...${NC}"
cd backend
python -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend server
echo -e "${GREEN}Starting frontend server...${NC}"
cd ../frontend
npm run serve &
FRONTEND_PID=$!

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Setup cleanup on script termination
trap cleanup SIGINT SIGTERM

echo -e "\n${GREEN}Servers are starting...${NC}"
echo -e "Backend will be available at: ${YELLOW}http://localhost:8000${NC}"
echo -e "Frontend will be available at: ${YELLOW}http://localhost:8080${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to stop both servers${NC}"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
