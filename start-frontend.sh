#!/bin/bash

# CoolieAssistant Frontend Startup Script
# Run this from the project root directory

echo "🚀 Starting CoolieAssistant Frontend..."
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found!"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo ""
echo "✅ Starting Vite development server..."
echo "📍 Frontend running at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
