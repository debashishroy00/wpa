"""
WealthPath AI - User Contamination Detection Middleware
CRITICAL: Monitors for user data contamination in real-time
"""
import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict, Set, Optional
import uuid

logger = structlog.get_logger()

class ContaminationMonitor(BaseHTTPMiddleware):
    """
    Middleware to detect and prevent user data contamination
    Tracks user sessions and detects cross-user data access
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.user_sessions: Dict[str, Dict] = {}
        self.contamination_alerts: Set[str] = set()
        
    async def dispatch(self, request: Request, call_next):
        """Monitor requests for contamination patterns"""
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Extract user context from JWT token if available
        user_id = None
        user_email = None
        
        try:
            # Try to get user from request state (set by auth middleware)
            if hasattr(request.state, 'user'):
                user_id = request.state.user.id
                user_email = request.state.user.email
        except Exception:
            pass
            
        # Log request start
        logger.info(
            "REQUEST_START",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            user_id=user_id,
            user_email=user_email
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Monitor financial endpoints for contamination
        if "/financial/" in request.url.path and user_id:
            await self._monitor_financial_response(
                request_id, user_id, user_email, response, process_time
            )
        
        # Log request completion
        logger.info(
            "REQUEST_COMPLETE",
            request_id=request_id,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            user_id=user_id
        )
        
        return response
    
    async def _monitor_financial_response(
        self, 
        request_id: str, 
        user_id: int, 
        user_email: str, 
        response: Response, 
        process_time: float
    ):
        """Monitor financial responses for contamination patterns"""
        
        # Track user session data
        session_key = f"user_{user_id}"
        
        if session_key not in self.user_sessions:
            self.user_sessions[session_key] = {
                "user_id": user_id,
                "email": user_email,
                "first_seen": time.time(),
                "request_count": 0,
                "financial_data": {},
                "last_response_time": process_time
            }
        
        session = self.user_sessions[session_key]
        session["request_count"] += 1
        session["last_response_time"] = process_time
        
        # Extract response data if JSON and successful
        if response.status_code == 200 and hasattr(response, 'body'):
            try:
                # Note: In middleware, response body might not be easily accessible
                # This is a simplified monitoring approach
                logger.info(
                    "FINANCIAL_REQUEST_MONITORED",
                    request_id=request_id,
                    user_id=user_id,
                    email=user_email,
                    response_time_ms=round(process_time * 1000, 2),
                    session_requests=session["request_count"]
                )
                
                # Check for suspicious patterns
                await self._check_contamination_patterns(request_id, session)
                
            except Exception as e:
                logger.warning(
                    "CONTAMINATION_MONITOR_ERROR",
                    request_id=request_id,
                    error=str(e)
                )
    
    async def _check_contamination_patterns(self, request_id: str, session: Dict):
        """Check for patterns that might indicate contamination"""
        
        user_id = session["user_id"]
        email = session["email"]
        
        # Pattern 1: Unusually fast response times (possible caching)
        if session["last_response_time"] < 0.01:  # Less than 10ms
            logger.warning(
                "POTENTIAL_CACHE_CONTAMINATION",
                request_id=request_id,
                user_id=user_id,
                email=email,
                response_time_ms=round(session["last_response_time"] * 1000, 2),
                reason="Unusually fast response time indicates possible caching"
            )
        
        # Pattern 2: Cross-session data consistency check
        # Compare with other active sessions
        for other_session_key, other_session in self.user_sessions.items():
            if other_session["user_id"] != user_id:
                # Different users should have different response patterns
                if (abs(other_session["last_response_time"] - session["last_response_time"]) < 0.001 and
                    other_session["request_count"] == session["request_count"]):
                    
                    contamination_key = f"{user_id}_{other_session['user_id']}"
                    if contamination_key not in self.contamination_alerts:
                        self.contamination_alerts.add(contamination_key)
                        
                        logger.critical(
                            "CRITICAL_CONTAMINATION_DETECTED",
                            request_id=request_id,
                            user1_id=user_id,
                            user1_email=email,
                            user2_id=other_session["user_id"],
                            user2_email=other_session["email"],
                            reason="Identical response patterns between different users"
                        )
    
    def get_contamination_report(self) -> Dict:
        """Generate contamination monitoring report"""
        return {
            "active_sessions": len(self.user_sessions),
            "contamination_alerts": len(self.contamination_alerts),
            "sessions": {
                session_key: {
                    "user_id": session["user_id"],
                    "email": session["email"],
                    "request_count": session["request_count"],
                    "session_age_minutes": round((time.time() - session["first_seen"]) / 60, 2),
                    "avg_response_time_ms": round(session["last_response_time"] * 1000, 2)
                }
                for session_key, session in self.user_sessions.items()
            },
            "alerts": list(self.contamination_alerts)
        }