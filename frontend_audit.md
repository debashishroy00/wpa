=== FRONTEND CHAT API CALLS ===
Generated: Sun, Aug 31, 2025 11:12:28 PM

## Current Chat Endpoints Used
frontend/src/components/Chat/ConversationHistory.tsx:      const response = await fetch(`${baseUrl}/api/v1/chat-memory/sessions/${user.id}`, {
frontend/src/components/Chat/FinancialAdvisorChat.tsx:            const endpoint = useIntelligentChat ? '/api/v1/chat/intelligent' : '/api/v1/chat/message';
frontend/src/components/Dashboard/MonitoringDashboard.tsx:        fetchWithAuth('/chat-metrics'),
frontend/src/services/VectorDBService.ts:            const url = new URL(`${this.baseURL}/api/v1/vector/chat-context/${userId}`);
