=== FRONTEND CHAT API CALLS ===
Generated: Sun, Aug 31, 2025 11:12:28 PM

## Current Chat Endpoints Used
frontend/src/components/Chat/ConversationHistory.tsx:      const response = await fetch(`${baseUrl}/api/v1/chat-memory/sessions/${user.id}`, {
frontend/src/components/Chat/FinancialAdvisorChat.tsx:            const endpoint = useIntelligentChat ? '/api/v1/chat/intelligent' : '/api/v1/chat/message';
frontend/src/components/Dashboard/MonitoringDashboard.tsx:        fetchWithAuth('/chat-metrics'),
frontend/src/services/VectorDBService.ts:            const url = new URL(`${this.baseURL}/api/v1/vector/chat-context/${userId}`);

## Chat Components Found
frontend/src/components/Chat
frontend/src/components/Chat/ChatInterface.tsx
frontend/src/components/Chat/FinancialAdvisorChat.tsx
frontend/src/styles/mobile-chat.css

## Authentication Pattern
frontend/src/App.tsx:        // Load any existing tokens from storage first
frontend/src/App.tsx:        console.log('📋 Loading tokens from localStorage...')
frontend/src/App.tsx:        const existingTokensCheck = localStorage.getItem('auth_tokens')
frontend/src/App.tsx:        console.log('🔍 Initial token check:', existingTokensCheck ? 'TOKENS FOUND' : 'NO TOKENS')
frontend/src/App.tsx:          console.log('✅ User already authenticated from stored tokens:', userData)
frontend/src/App.tsx:          // CRITICAL FIX: Manually populate auth store from existing tokens
frontend/src/App.tsx:          const existingTokens = localStorage.getItem('auth_tokens')
frontend/src/App.tsx:          console.log('📋 Existing tokens:', existingTokens ? 'FOUND' : 'NOT FOUND')
frontend/src/App.tsx:            console.log('🔧 Manually populating auth store from existing tokens')
frontend/src/App.tsx:            const tokens = JSON.parse(existingTokens)

## Response Handling
frontend/src/components/Chat/ConversationHistory.tsx:      if (!response.ok) {
frontend/src/components/Chat/ConversationHistory.tsx:        throw new Error(`Failed to load sessions: ${response.statusText}`);
frontend/src/components/Chat/ConversationHistory.tsx:      const data = await response.json();
frontend/src/components/Chat/FinancialAdvisorChat.tsx:            if (response.ok) {
frontend/src/components/Chat/FinancialAdvisorChat.tsx:                const data = await response.json();
frontend/src/components/Chat/FinancialAdvisorChat.tsx:            if (response.ok) {
frontend/src/components/Chat/FinancialAdvisorChat.tsx:                const data = await response.json();
frontend/src/components/Chat/FinancialAdvisorChat.tsx:                const errorData = await response.json();
frontend/src/components/Chat/FinancialAdvisorChat.tsx:            if (!response.ok) {
frontend/src/components/Chat/FinancialAdvisorChat.tsx:                const errorText = await response.text();
