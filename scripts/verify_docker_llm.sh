#!/bin/bash

# WealthPath AI - Docker LLM Integration Verification Script
# Verifies that multi-LLM features work correctly in Docker environment

set -e

echo "🐳 WealthPath AI Docker LLM Integration Verification"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Check if .env file exists
echo ""
echo "1. Environment Configuration Check"
echo "--------------------------------"
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure API keys."
    exit 1
fi

# Source environment variables
source .env

echo "✅ Environment file found"

print_status 0 ".env file exists"

# Check for required API keys
echo "Checking API key configuration..."

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
    print_warning "OpenAI API key not configured"
    OPENAI_CONFIGURED=false
else
    print_status 0 "OpenAI API key configured"
    OPENAI_CONFIGURED=true
fi

if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your-gemini-api-key-here" ]; then
    print_warning "Gemini API key not configured"
    GEMINI_CONFIGURED=false
else
    print_status 0 "Gemini API key configured"
    GEMINI_CONFIGURED=true
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-anthropic-api-key-here" ]; then
    print_warning "Anthropic API key not configured"
    CLAUDE_CONFIGURED=false
else
    print_status 0 "Anthropic API key configured"
    CLAUDE_CONFIGURED=true
fi

# Check if at least one provider is configured
if [ "$OPENAI_CONFIGURED" = false ] && [ "$GEMINI_CONFIGURED" = false ] && [ "$CLAUDE_CONFIGURED" = false ]; then
    echo "❌ No LLM providers configured. Please add at least one API key to .env"
    echo "   Get keys from:"
    echo "   - OpenAI: https://platform.openai.com/api-keys"
    echo "   - Gemini: https://makersuite.google.com/app/apikey"
    echo "   - Claude: https://console.anthropic.com/"
    exit 1
fi

# 2. Docker and Docker Compose Check
echo ""
echo "2. Docker Environment Check"
echo "--------------------------"

# Check if Docker is running
docker info > /dev/null 2>&1
print_status $? "Docker daemon is running"

# Check if Docker Compose is available
docker-compose version > /dev/null 2>&1 || docker compose version > /dev/null 2>&1
print_status $? "Docker Compose is available"

# 3. Build and Start Services
echo ""
echo "3. Building and Starting Services"
echo "--------------------------------"

echo "Building containers..."
docker-compose build --no-cache
print_status $? "Containers built successfully"

echo "Starting services..."
docker-compose up -d
print_status $? "Services started successfully"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# 4. Service Health Checks
echo ""
echo "4. Service Health Checks"
echo "----------------------"

# Check backend health
echo "Checking backend service..."
for i in {1..30}; do
    backend_health=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")
    if [[ $backend_health == *"healthy"* ]] || [[ $backend_health == *"ok"* ]]; then
        print_status 0 "Backend service is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend logs:"
        docker-compose logs backend | tail -20
        print_status 1 "Backend service health check failed"
    fi
    sleep 2
done

# Check frontend access
echo "Checking frontend service..."
frontend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3004 2>/dev/null || echo "000")
if [ "$frontend_status" = "200" ]; then
    print_status 0 "Frontend service is accessible"
else
    print_status 1 "Frontend service not accessible"
fi

# Check Redis
echo "Checking Redis service..."
redis_status=$(docker-compose exec -T redis redis-cli ping 2>/dev/null || echo "failed")
if [ "$redis_status" = "PONG" ]; then
    print_status 0 "Redis service is running"
else
    print_status 1 "Redis service check failed"
fi

# 5. LLM Integration Tests
echo ""
echo "5. LLM Integration Tests"
echo "----------------------"

# Check LLM providers endpoint
echo "Checking LLM providers endpoint..."
providers_response=$(curl -s http://localhost:8000/api/v1/llm/providers 2>/dev/null || echo "failed")
if [[ $providers_response == *"openai"* ]] && [[ $providers_response == *"gemini"* ]] && [[ $providers_response == *"claude"* ]]; then
    print_status 0 "LLM providers endpoint working"
    echo ""
    echo "📋 Available LLM Providers:"
    echo "$providers_response" | python3 -m json.tool 2>/dev/null || echo "$providers_response"
else
    print_status 1 "LLM providers endpoint failed"
fi

# Check knowledge base
echo ""
echo "Checking knowledge base endpoint..."
kb_response=$(curl -s http://localhost:8000/api/v1/llm/knowledge-base/documents 2>/dev/null || echo "failed")
if [[ $kb_response != "failed" ]]; then
    print_status 0 "Knowledge base endpoint accessible"
else
    print_warning "Knowledge base endpoint failed (may be empty - this is OK)"
fi

# Test LLM health endpoint
echo ""
echo "Testing LLM health endpoint..."
health_response=$(curl -s http://localhost:8000/api/v1/llm/health 2>/dev/null || echo "failed")
if [[ $health_response != "failed" ]]; then
    print_status 0 "LLM health endpoint accessible"
    echo ""
    echo "📊 LLM Service Health:"
    echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
else
    print_status 1 "LLM health endpoint failed"
fi

# 6. Container Status Check
echo ""
echo "6. Container Status Overview"
echo "---------------------------"

echo "Running containers:"
docker-compose ps

# 7. Final Summary
echo ""
echo "🎉 Verification Complete!"
echo "========================"
echo ""
echo "✅ NFP Platform is running with multi-LLM integration"
echo "🌐 Frontend: http://localhost:3004"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""

if [ "$OPENAI_CONFIGURED" = false ] && [ "$GEMINI_CONFIGURED" = false ] && [ "$CLAUDE_CONFIGURED" = false ]; then
    print_warning "Configure API keys in .env for full LLM functionality"
fi

echo ""
echo "📌 Next Steps:"
echo "1. Visit http://localhost:3004 to access the frontend"
echo "2. Navigate to Step 5 (Financial Advisory) to test LLM features"
echo "3. Use the 'AI Settings' button to configure providers"
echo "4. Test advisory generation with your configured providers"
echo ""
echo "🔧 Available Services:"
echo "- Frontend: http://localhost:3004"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- LLM Health: http://localhost:8000/api/v1/llm/health"
echo ""
echo "To stop services: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo "To restart: docker-compose restart"