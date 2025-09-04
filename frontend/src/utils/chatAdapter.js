/**
 * Adapter to make new chat endpoint compatible with existing UI
 */

export const adaptNewChatResponse = (newResponse) => {
  return {
    // Map new format to old format
    message: {
      content: newResponse.response
    },
    // Convert facts to context string
    context_used: JSON.stringify(newResponse.facts_used || {}),
    // Placeholder metrics (new endpoint doesn't track these)
    tokens_used: { total: 0 },
    cost_breakdown: { total: 0 },
    // New fields to preserve
    confidence: newResponse.confidence,
    assumptions: newResponse.assumptions || [],
    warnings: newResponse.warnings || [],
    // Clarifier support
    is_clarify: !!newResponse.is_clarify,
    clarify: newResponse.clarify || null,
    session_id: newResponse.session_id
  };
};

export const shouldUseNewEndpoint = () => {
  // Temporarily default to true for testing Context+LLM Intelligence
  return localStorage.getItem('use_new_chat') !== 'false';
};
