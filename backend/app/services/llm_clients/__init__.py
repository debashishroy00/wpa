"""
WealthPath AI - LLM Clients Module
Multi-LLM client implementations
"""
from .openai_client import OpenAIClient

try:
    from .gemini_client import GeminiClient
    HAS_GEMINI = True
except ImportError as e:
    # Create a placeholder class when Gemini is not available
    class GeminiClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(f"Gemini client unavailable: {e}")
    HAS_GEMINI = False

try:
    from .claude_client import ClaudeClient
    HAS_CLAUDE = True
except ImportError as e:
    # Create a placeholder class when Claude is not available
    class ClaudeClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(f"Claude client unavailable: {e}")
    HAS_CLAUDE = False

__all__ = ['OpenAIClient', 'GeminiClient', 'ClaudeClient']