"""
WealthPath AI - Analytics and ML Models
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from decimal import Decimal

from app.db.session import Base


class ModelType(enum.Enum):
    target_setting = "target_setting"
    portfolio_optimization = "portfolio_optimization"
    behavioral_prediction = "behavioral_prediction"
    gap_analysis = "gap_analysis"
    risk_assessment = "risk_assessment"


class PredictionStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class InteractionType(enum.Enum):
    page_view = "page_view"
    button_click = "button_click"
    form_submit = "form_submit"
    goal_create = "goal_create"
    goal_update = "goal_update"
    recommendation_view = "recommendation_view"
    recommendation_accept = "recommendation_accept"
    recommendation_decline = "recommendation_decline"
    calculation_request = "calculation_request"


class ModelPrediction(Base):
    """
    ML model predictions and results
    """
    __tablename__ = "model_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Model Information
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    model_name = Column(String(100), nullable=True)
    
    # Input Data
    input_data = Column(Text, nullable=False)  # JSON string with input parameters
    input_hash = Column(String(64), nullable=False, index=True)  # SHA256 of input for caching
    
    # Output Data
    output_data = Column(Text, nullable=True)  # JSON string with prediction results
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Processing Information
    status = Column(SQLEnum(PredictionStatus), default=PredictionStatus.pending, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    context = Column(Text, nullable=True)  # JSON with additional context
    session_id = Column(String(36), nullable=True)  # UUID for grouping related predictions
    request_id = Column(String(36), nullable=True)  # UUID for request tracking
    
    # Validation and Feedback
    human_feedback_score = Column(Numeric(3, 2), nullable=True)  # User rating of prediction
    feedback_notes = Column(Text, nullable=True)
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="model_predictions")

    def __repr__(self):
        return f"<ModelPrediction(id={self.id}, type='{self.model_type.value}', confidence={self.confidence_score})>"


class UserInteraction(Base):
    """
    User interaction tracking for analytics and ML
    """
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Can be null for anonymous
    
    # Interaction Details
    interaction_type = Column(SQLEnum(InteractionType), nullable=False, index=True)
    page_url = Column(String(500), nullable=True)
    element_id = Column(String(100), nullable=True)
    element_text = Column(String(200), nullable=True)
    
    # Context Information
    session_id = Column(String(36), nullable=False, index=True)  # UUID for session grouping
    request_id = Column(String(36), nullable=True)
    referrer_url = Column(String(500), nullable=True)
    
    # Technical Details
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(20), nullable=True)  # desktop, mobile, tablet
    browser_name = Column(String(50), nullable=True)
    screen_resolution = Column(String(20), nullable=True)
    
    # Interaction Data
    interaction_data = Column(Text, nullable=True)  # JSON with interaction-specific data
    duration_ms = Column(Integer, nullable=True)  # How long interaction lasted
    scroll_depth = Column(Integer, nullable=True)  # Percentage of page scrolled
    
    # A/B Testing
    experiment_id = Column(String(50), nullable=True)
    variant_id = Column(String(50), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="interactions")

    def __repr__(self):
        return f"<UserInteraction(id={self.id}, type='{self.interaction_type.value}', user_id={self.user_id})>"


class ModelPerformanceMetric(Base):
    """
    Model performance tracking and validation
    """
    __tablename__ = "model_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Model Information
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    evaluation_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Performance Metrics
    accuracy_score = Column(Numeric(5, 4), nullable=True)  # 0.0000 to 1.0000
    precision_score = Column(Numeric(5, 4), nullable=True)
    recall_score = Column(Numeric(5, 4), nullable=True)
    f1_score = Column(Numeric(5, 4), nullable=True)
    mae = Column(Numeric(10, 4), nullable=True)  # Mean Absolute Error
    mse = Column(Numeric(10, 4), nullable=True)  # Mean Squared Error
    rmse = Column(Numeric(10, 4), nullable=True)  # Root Mean Squared Error
    
    # Custom Metrics (JSON)
    custom_metrics = Column(Text, nullable=True)
    
    # Test Set Information
    test_set_size = Column(Integer, nullable=True)
    test_set_description = Column(String(200), nullable=True)
    cross_validation_folds = Column(Integer, nullable=True)
    
    # Metadata
    evaluation_notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)  # Who ran the evaluation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ModelPerformanceMetric(id={self.id}, model='{self.model_type.value}', accuracy={self.accuracy_score})>"


class FeatureImportance(Base):
    """
    Feature importance scores for model interpretability
    """
    __tablename__ = "feature_importance"

    id = Column(Integer, primary_key=True, index=True)
    
    # Model Information
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    
    # Feature Information
    feature_name = Column(String(100), nullable=False)
    feature_category = Column(String(50), nullable=True)  # demographic, financial, behavioral
    importance_score = Column(Numeric(8, 6), nullable=False)  # Normalized importance score
    
    # Interpretation
    interpretation = Column(Text, nullable=True)  # Human-readable explanation
    correlation_direction = Column(String(10), nullable=True)  # positive, negative, complex
    
    # Metadata
    calculation_method = Column(String(50), nullable=False)  # SHAP, permutation, etc.
    evaluation_date = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<FeatureImportance(model='{self.model_type.value}', feature='{self.feature_name}', score={self.importance_score})>"


class ABTestExperiment(Base):
    """
    A/B testing experiments for model and feature validation
    """
    __tablename__ = "ab_test_experiments"

    id = Column(Integer, primary_key=True, index=True)
    
    # Experiment Information
    experiment_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)
    
    # Configuration
    control_variant = Column(String(50), nullable=False)
    test_variants = Column(Text, nullable=False)  # JSON array of variant names
    traffic_allocation = Column(Text, nullable=False)  # JSON with allocation percentages
    
    # Target Metrics
    primary_metric = Column(String(100), nullable=False)
    secondary_metrics = Column(Text, nullable=True)  # JSON array
    
    # Status and Timing
    status = Column(String(20), default="draft", nullable=False)  # draft, running, paused, completed
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    target_sample_size = Column(Integer, nullable=True)
    
    # Results
    results = Column(Text, nullable=True)  # JSON with statistical results
    conclusion = Column(Text, nullable=True)
    statistical_significance = Column(Boolean, nullable=True)
    
    # Metadata
    created_by = Column(String(100), nullable=False)
    tags = Column(Text, nullable=True)  # JSON array of tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<ABTestExperiment(id='{self.experiment_id}', name='{self.name}', status='{self.status}')>"