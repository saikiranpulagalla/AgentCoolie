#!/bin/bash

# AgentCoolie Frontend Startup Script
# Run this from the project root directory.

echo "Starting AgentCoolie Frontend..."
echo ""

if [ ! -f "package.json" ]; then
    echo "Error: package.json not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "Starting Vite development server..."
echo "Frontend running at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
