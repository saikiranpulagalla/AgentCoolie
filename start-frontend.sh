#!/bin/bash

# CoolieAssistant Frontend Startup Script
# Run this from the project root directory

echo "🚀 Starting CoolieAssistant Frontend..."
echo ""

# Check if we're in the right directory
if [ ! -d "client" ]; then
    echo "❌ Error: client directory not found!"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "client/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd client
    npm install
    cd ..
fi

# Start the development server
echo ""
echo "✅ Starting Vite development server..."
echo "📍 Frontend running at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd client
npm run dev
