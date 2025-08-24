#!/bin/bash

# WealthPath AI - Shadow Mode Startup Script
# This script starts the backend with shadow mode enabled and monitoring

echo "🚀 Starting WealthPath AI with Shadow Mode Monitoring"
echo "=================================================="
echo "Shadow Mode: ENABLED (Zero user impact)"
echo "Hybrid System: DISABLED (Using existing system)"
echo "Redis: Available at localhost:6379"
echo "OpenAI API: Configured and ready"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the /backend directory"
    echo "Current directory: $(pwd)"
    echo "Expected: /mnt/c/projects/wpa/backend/"
    exit 1
fi

# Check if .env file exists in parent directory
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found in parent directory"
    echo "Please ensure /mnt/c/projects/wpa/.env exists"
    exit 1
fi

# Source environment variables from parent .env
export $(grep -v '^#' ../.env | xargs)

# Verify shadow mode configuration
echo "🔧 Configuration Check:"
echo "  EMBEDDING_SHADOW_MODE: ${EMBEDDING_SHADOW_MODE:-not_set}"
echo "  USE_HYBRID_EMBEDDINGS: ${USE_HYBRID_EMBEDDINGS:-not_set}"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:+configured}"
echo "  REDIS_URL: ${REDIS_URL:-not_set}"

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if timeout 5 redis-cli -u "${REDIS_URL:-redis://localhost:6379}" ping >/dev/null 2>&1; then
    echo "  ✅ Redis is running and accessible"
else
    echo "  ⚠️  Redis not accessible - will use in-memory cache fallback"
fi

# Check if required packages are installed
echo "🔍 Checking Python dependencies..."
python3 -c "import sentence_transformers, torch, faiss" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ ML dependencies available"
else
    echo "  ⚠️  Some ML dependencies may be missing"
    echo "  Run: pip install -r requirements.txt"
fi

# Start the application
echo ""
echo "🚀 Starting FastAPI server..."
echo "=================================================="

# Kill any existing processes on port 8000
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "  🔄 Stopping existing server on port 8000..."
    kill -9 $(lsof -ti:8000) 2>/dev/null || true
    sleep 2
fi

# Start uvicorn with shadow mode enabled
echo "  📡 Server starting on http://localhost:8000"
echo "  🔍 Shadow mode logging enabled"
echo "  📊 Monitoring endpoints available"
echo ""

# Set environment variables explicitly for the session
export EMBEDDING_SHADOW_MODE=true
export USE_HYBRID_EMBEDDINGS=false

# Start the server in background
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
echo "  ⏳ Waiting for server to initialize..."
sleep 5

# Check if server is running
if curl -s http://localhost:8000/docs >/dev/null 2>&1; then
    echo "  ✅ Server is running successfully!"
else
    echo "  ❌ Server failed to start properly"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "📊 MONITORING DASHBOARDS:"
echo "========================="
echo "🏠 API Documentation:     http://localhost:8000/docs"
echo "🔍 Production Readiness:   http://localhost:8000/api/v1/embeddings/production-readiness"
echo "📈 Live Metrics:          http://localhost:8000/api/v1/embeddings/metrics"
echo "💚 System Health:         http://localhost:8000/api/v1/embeddings/health"
echo "🚨 Active Alerts:         http://localhost:8000/api/v1/embeddings/alerts"
echo ""
echo "🔧 TESTING COMMANDS:"
echo "===================="
echo "Test shadow mode:         python3 test_shadow_mode.py"
echo "Live monitoring:          python3 monitor_shadow.py"
echo "Load testing:             python3 scripts/load_test_embeddings.py"
echo "Rollback verification:    python3 scripts/verify_rollback.py"
echo ""

# Create a simple health check function
check_health() {
    curl -s http://localhost:8000/api/v1/embeddings/health | python3 -m json.tool
}

echo "📋 QUICK HEALTH CHECK:"
echo "======================"
check_health
echo ""

echo "✅ Shadow Mode Setup Complete!"
echo "================================"
echo "💡 Next Steps:"
echo "  1. Use WealthPath AI normally (frontend, API calls, etc.)"
echo "  2. Monitor progress: run 'python3 monitor_shadow.py' in another terminal"
echo "  3. Check metrics periodically at the dashboard URLs above"
echo "  4. Look for 'Shadow mode checkpoint' messages in the logs"
echo ""
echo "🎯 Success Criteria (48-72 hours):"
echo "  • 100+ comparisons collected"
echo "  • >95% average similarity"
echo "  • No critical alerts"
echo "  • Readiness score >90%"
echo ""
echo "⏹️  To stop: Press Ctrl+C or run 'pkill -f uvicorn'"
echo "📱 Server PID: $SERVER_PID"
echo ""

# Keep script running and show periodic updates
trap 'echo ""; echo "🛑 Stopping shadow mode..."; kill $SERVER_PID 2>/dev/null; exit 0' INT

echo "🔄 Shadow mode is now active. Press Ctrl+C to stop."
echo "   Monitoring will show periodic updates..."

# Show periodic status updates
while true; do
    sleep 300  # 5 minutes
    echo ""
    echo "⏰ $(date '+%Y-%m-%d %H:%M:%S') - Shadow Mode Status Update"
    echo "=================================================="
    
    # Quick health check
    if curl -s http://localhost:8000/api/v1/embeddings/production-readiness >/dev/null 2>&1; then
        echo "✅ Server: Running"
        
        # Get basic metrics
        READINESS=$(curl -s http://localhost:8000/api/v1/embeddings/production-readiness | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data.get('readiness_score', 0):.1%}\")" 2>/dev/null || echo "unavailable")
        echo "📊 Readiness Score: $READINESS"
        
        # Get shadow stats if available
        COMPARISONS=$(curl -s http://localhost:8000/api/v1/embeddings/production-readiness | python3 -c "import sys, json; data=json.load(sys.stdin); shadow=data.get('shadow_mode_stats', {}); print(shadow.get('total_comparisons', 0))" 2>/dev/null || echo "0")
        echo "🔍 Total Comparisons: $COMPARISONS"
        
        if [ "$COMPARISONS" -gt 0 ]; then
            SIMILARITY=$(curl -s http://localhost:8000/api/v1/embeddings/production-readiness | python3 -c "import sys, json; data=json.load(sys.stdin); shadow=data.get('shadow_mode_stats', {}); quality=shadow.get('quality_metrics', {}); print(f\"{quality.get('average_similarity', 0):.1%}\")" 2>/dev/null || echo "unavailable")
            echo "✨ Avg Similarity: $SIMILARITY"
        fi
        
    else
        echo "❌ Server: Not responding"
    fi
    
    echo "=================================================="
done