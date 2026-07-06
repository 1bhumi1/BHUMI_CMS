import time
import uuid
import logging
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# ContextVar for request ID
request_id_contextvar = ContextVar("request_id", default="-")

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_contextvar.get()
        return True

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Config console logging if not configured
if not logger.handlers:
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [ReqID: %(request_id)s] %(message)s"))
    sh.addFilter(RequestIDFilter())
    logger.addHandler(sh)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check for existing request ID or generate one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Set context variable and store token
        token = request_id_contextvar.set(request_id)
        
        # Make request_id accessible in request state just in case
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request {request.method} {request.url.path} failed with: {str(e)} in {process_time:.2f}ms"
            )
            request_id_contextvar.reset(token)
            raise e

        process_time = (time.time() - start_time) * 1000
        
        # Log request info
        logger.info(
            f"{request.method} {request.url.path} - Status: {response.status_code} in {process_time:.2f}ms"
        )
        
        # Append Request ID header to response
        response.headers["X-Request-ID"] = request_id
        
        # Reset context variable
        request_id_contextvar.reset(token)
        return response
