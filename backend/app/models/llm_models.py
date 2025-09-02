"""
WealthPath AI - Multi-LLM Models
Pydantic models for multi-LLM integration system
"""
from typing import Dict, List, Optional, Union, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class LLMProvider(BaseModel):
    """LLM Provider Configuration"""
    provider_id: str = Field(..., description="Unique provider identifier")
    name: str = Field(..., description="Display name")
    is_enabled: bool = Field(default=True)
    cost_per_1k_tokens_input: Decimal = Field(..., description="Cost per 1K input tokens")
    cost_per_1k_tokens_output: Decimal = Field(..., description="Cost per 1K output tokens")
    models: Dict[str, Dict[str, Any]] = Field(..., description="Available models by tier")


class LLMRequest(BaseModel):
    """LLM Generation Request"""
    provider: Literal["openai", "gemini", "claude"] = Field(..., description="LLM provider")
    model_tier: Literal["dev", "prod"] = Field(default="dev", description="Model tier for cost optimization")
    system_prompt: str = Field(..., description="System prompt")
    user_prompt: str = Field(..., description="User prompt")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Step 4 data context")
    knowledge_base_query: Optional[str] = Field(None, description="Knowledge base search query")
    max_tokens: Optional[int] = Field(default=2000)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    mode: Literal["direct", "balanced", "comprehensive"] = Field(default="balanced", description="Response mode affecting depth and creativity")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseDocument(BaseModel):
    """Knowledge Base Document"""
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    doc_type: Literal["playbook", "regulation", "research", "template"] = Field(..., description="Document type")
    category: str = Field(..., description="Document category")
    tags: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    """Citation Reference"""
    doc_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    excerpt: str = Field(..., description="Relevant excerpt")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    page_number: Optional[int] = Field(None)
    section: Optional[str] = Field(None)


class NumberValidation(BaseModel):
    """Number Validation Result"""
    original_number: Union[int, float, Decimal]
    validated_number: Union[int, float, Decimal]
    is_valid: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_method: str
    error_message: Optional[str] = None


class LLMResponse(BaseModel):
    """LLM Generation Response"""
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Specific model used")
    content: str = Field(..., description="Generated content")
    citations: List[Citation] = Field(default_factory=list)
    number_validations: List[NumberValidation] = Field(default_factory=list)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    cost: Decimal = Field(..., description="Generation cost in USD")
    generation_time: float = Field(..., description="Generation time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LLMComparison(BaseModel):
    """Multi-LLM Comparison Result"""
    request_id: str = Field(..., description="Unique request identifier")
    responses: List[LLMResponse] = Field(..., description="Responses from different providers")
    total_cost: Decimal = Field(..., description="Total cost across all providers")
    fastest_provider: str = Field(..., description="Fastest responding provider")
    most_cost_effective: str = Field(..., description="Most cost-effective provider")
    consensus_score: float = Field(ge=0.0, le=1.0, description="Agreement between providers")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RAGQuery(BaseModel):
    """RAG Knowledge Base Query"""
    query: str = Field(..., description="Search query")
    doc_types: Optional[List[str]] = Field(None, description="Filter by document types")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    max_results: int = Field(default=5, ge=1, le=20)
    min_relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)


class RAGResult(BaseModel):
    """RAG Search Result"""
    documents: List[KnowledgeBaseDocument] = Field(..., description="Retrieved documents")
    citations: List[Citation] = Field(..., description="Generated citations")
    search_metadata: Dict[str, Any] = Field(default_factory=dict)
    total_results: int = Field(..., description="Total matching documents")
    search_time: float = Field(..., description="Search time in seconds")


class AdvisoryGeneration(BaseModel):
    """Advisory Content Generation Request"""
    step4_data: Dict[str, Any] = Field(..., description="Step 4 deterministic data")
    generation_type: Literal["summary", "recommendations", "analysis", "comparison"] = Field(..., description="Type of content to generate")
    provider_preferences: Optional[List[str]] = Field(None, description="Preferred LLM providers")
    enable_comparison: bool = Field(default=False, description="Generate with multiple providers")
    custom_prompts: Optional[Dict[str, str]] = Field(None, description="Custom prompt overrides")


class AdvisoryContent(BaseModel):
    """Generated Advisory Content"""
    generation_id: str = Field(..., description="Unique generation identifier")
    content_type: str = Field(..., description="Type of generated content")
    content: str = Field(..., description="Generated advisory content")
    llm_response: LLMResponse = Field(..., description="LLM response details")
    rag_results: Optional[RAGResult] = Field(None, description="RAG search results")
    validation_results: List[NumberValidation] = Field(default_factory=list)
    quality_score: float = Field(ge=0.0, le=1.0, description="Content quality score")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CostOptimization(BaseModel):
    """Cost Optimization Settings"""
    max_cost_per_request: Decimal = Field(default=Decimal("1.00"), description="Maximum cost per request")
    prefer_dev_models: bool = Field(default=True, description="Prefer cheaper dev models")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_duration_hours: int = Field(default=24, ge=1, le=168)
    cost_alert_threshold: Decimal = Field(default=Decimal("0.50"), description="Cost alert threshold")