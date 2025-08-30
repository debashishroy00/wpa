"""
Token Management Service for Chat Memory System
Prevents context overflow and optimizes token usage for LLM calls
"""
import re
from typing import Dict, List, Tuple
import structlog

logger = structlog.get_logger()


class TokenManager:
    """Manages token counting and context trimming for optimal LLM performance"""
    
    def __init__(self, max_tokens: int = 1500):
        self.max_tokens = max_tokens
        self.tokens_per_char = 0.25  # Rough estimate: 1 token ≈ 4 characters
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        Uses character-based approximation with adjustments for structure
        """
        if not text:
            return 0
        
        # Base character count
        char_count = len(text)
        
        # Adjust for JSON structure, whitespace, and formatting
        # JSON typically has more tokens per character due to syntax
        if self._is_json_like(text):
            multiplier = 0.3  # JSON is more token-dense
        else:
            multiplier = 0.25  # Regular text
        
        # Account for common patterns that increase token density
        # Numbers, URLs, code snippets are more token-dense
        if re.search(r'[\d\$\%\.\,]{3,}', text):  # Financial numbers
            multiplier += 0.05
        
        if re.search(r'http|www|\.com', text):  # URLs
            multiplier += 0.1
        
        return int(char_count * multiplier)
    
    def _is_json_like(self, text: str) -> bool:
        """Check if text contains JSON-like structure"""
        json_indicators = ['{', '}', '[', ']', ':', '"']
        return sum(text.count(indicator) for indicator in json_indicators) > len(text) * 0.05
    
    def trim_context(self, context: str, max_tokens: int = None) -> Tuple[str, Dict[str, int]]:
        """
        Intelligently trim context to fit token limit while preserving key information
        
        Priority order for trimming:
        1. Keep conversation memory (highest priority)
        2. Keep user profile summary
        3. Trim financial data (keep only relevant parts)
        4. Reduce historical context
        """
        max_tokens = max_tokens or self.max_tokens
        current_tokens = self.count_tokens(context)
        
        if current_tokens <= max_tokens:
            return context, {
                'original_tokens': current_tokens,
                'final_tokens': current_tokens,
                'trimmed': False
            }
        
        logger.info(f"Context trimming required: {current_tokens} -> {max_tokens} tokens")
        
        # Parse context into sections
        sections = self._parse_context_sections(context)
        
        # Trim sections by priority
        trimmed_sections = self._trim_sections_by_priority(sections, max_tokens)
        
        # Rebuild context
        trimmed_context = self._rebuild_context(trimmed_sections)
        final_tokens = self.count_tokens(trimmed_context)
        
        return trimmed_context, {
            'original_tokens': current_tokens,
            'final_tokens': final_tokens,
            'trimmed': True,
            'sections_kept': list(trimmed_sections.keys()),
            'compression_ratio': final_tokens / current_tokens if current_tokens > 0 else 1.0
        }
    
    def _parse_context_sections(self, context: str) -> Dict[str, str]:
        """Parse context into identifiable sections"""
        sections = {}
        
        # Split by common section markers
        lines = context.split('\n')
        current_section = 'general'
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Identify section headers
            if line_stripped.startswith('CONVERSATION MEMORY:'):
                self._save_current_section(sections, current_section, current_content)
                current_section = 'conversation_memory'
                current_content = [line]
            elif line_stripped.startswith('CURRENT USER QUESTION:'):
                self._save_current_section(sections, current_section, current_content)
                current_section = 'user_question'
                current_content = [line]
            elif line_stripped.startswith('FINANCIAL PROFILE:'):
                self._save_current_section(sections, current_section, current_content)
                current_section = 'financial_profile'
                current_content = [line]
            elif line_stripped.startswith('FOCUS:'):
                self._save_current_section(sections, current_section, current_content)
                current_section = 'intent_guidance'
                current_content = [line]
            elif line_stripped.startswith('CONVERSATION GUIDELINES:'):
                self._save_current_section(sections, current_section, current_content)
                current_section = 'guidelines'
                current_content = [line]
            else:
                current_content.append(line)
        
        # Save final section
        self._save_current_section(sections, current_section, current_content)
        
        return sections
    
    def _save_current_section(self, sections: Dict[str, str], section_name: str, content: List[str]):
        """Save current section content"""
        if content:
            sections[section_name] = '\n'.join(content)
    
    def _trim_sections_by_priority(self, sections: Dict[str, str], max_tokens: int) -> Dict[str, str]:
        """Trim sections based on priority order"""
        # Priority order (highest to lowest)
        priority_order = [
            'user_question',      # Always keep - essential
            'conversation_memory', # High priority - core feature
            'intent_guidance',    # Medium-high - helps focus
            'financial_profile',  # Medium - can be trimmed
            'guidelines',         # Low - can be removed
            'general'            # Lowest - miscellaneous
        ]
        
        trimmed_sections = {}
        used_tokens = 0
        
        # Reserve tokens for essential sections
        reserved_tokens = 200  # Buffer for user question + basic structure
        available_tokens = max_tokens - reserved_tokens
        
        for section_name in priority_order:
            if section_name not in sections:
                continue
            
            section_content = sections[section_name]
            section_tokens = self.count_tokens(section_content)
            
            if section_name == 'user_question':
                # Always include user question
                trimmed_sections[section_name] = section_content
                used_tokens += section_tokens
            elif used_tokens + section_tokens <= available_tokens:
                # Include full section if it fits
                trimmed_sections[section_name] = section_content
                used_tokens += section_tokens
            elif section_name in ['conversation_memory', 'financial_profile']:
                # Try to include partial content for important sections
                partial_content = self._trim_section_content(
                    section_content, 
                    available_tokens - used_tokens
                )
                if partial_content:
                    trimmed_sections[section_name] = partial_content
                    used_tokens += self.count_tokens(partial_content)
            # Skip less important sections if no room
        
        logger.info(f"Trimmed context: {used_tokens}/{max_tokens} tokens, kept sections: {list(trimmed_sections.keys())}")
        return trimmed_sections
    
    def _trim_section_content(self, content: str, max_tokens: int) -> str:
        """Trim content within a section to fit token limit"""
        current_tokens = self.count_tokens(content)
        if current_tokens <= max_tokens:
            return content
        
        # Simple truncation by lines
        lines = content.split('\n')
        trimmed_lines = []
        used_tokens = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line)
            if used_tokens + line_tokens <= max_tokens:
                trimmed_lines.append(line)
                used_tokens += line_tokens
            else:
                # Add truncation indicator
                if trimmed_lines:
                    trimmed_lines.append('... [content trimmed for length]')
                break
        
        return '\n'.join(trimmed_lines)
    
    def _rebuild_context(self, sections: Dict[str, str]) -> str:
        """Rebuild context from trimmed sections"""
        # Rebuild in logical order
        rebuild_order = [
            'conversation_memory',
            'financial_profile', 
            'user_question',
            'intent_guidance',
            'guidelines',
            'general'
        ]
        
        context_parts = []
        for section_name in rebuild_order:
            if section_name in sections:
                context_parts.append(sections[section_name])
        
        return '\n\n'.join(context_parts)
    
    def get_token_budget(self) -> Dict[str, int]:
        """Get recommended token allocation for different context sections"""
        return {
            'conversation_memory': int(self.max_tokens * 0.3),  # 450 tokens
            'financial_profile': int(self.max_tokens * 0.4),   # 600 tokens
            'user_question': int(self.max_tokens * 0.1),       # 150 tokens
            'intent_guidance': int(self.max_tokens * 0.1),     # 150 tokens
            'guidelines': int(self.max_tokens * 0.1),          # 150 tokens
            'buffer': int(self.max_tokens * 0.1)               # 150 tokens buffer
        }


# Global token manager instance
token_manager = TokenManager(max_tokens=1500)