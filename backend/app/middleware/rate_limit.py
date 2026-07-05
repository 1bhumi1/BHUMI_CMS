import time
from typing import Dict, List
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        # In-memory store: IP -> list of timestamps
        self.request_history: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Bypass rate limit for localhost / local development environment
        if client_ip in ["127.0.0.1", "localhost", "::1"]:
            return await call_next(request)

        now = time.time()
        
        # Initialize or clean up history for the client IP
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
            
        history = self.request_history[client_ip]
        
        # Keep only requests within the last 60 seconds
        cutoff = now - 60.0
        history = [t for t in history if t > cutoff]
        self.request_history[client_ip] = history
        
        # Check limit
        if len(history) >= self.rate_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again in a minute."}
            )
            
        # Record request
        history.append(now)
        
        return await call_next(request)
