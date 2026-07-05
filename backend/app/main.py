from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.middleware import (
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    setup_exception_handlers,
)

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-Ready REST API for College Management System backend",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Setup Exception Handlers (Standard Error Responses)
setup_exception_handlers(app)

# 2. Add Standard Middlewares
# Trusted Hosts Header Injection Protection
allowed_hosts = [host.strip() for host in settings.ALLOWED_HOSTS.split(",")]
if "*" not in allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Add Custom Middlewares (Request Tracing, Security Headers, Rate Limiting)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limit=settings.RATE_LIMIT_PER_MINUTE)

# 4. Attach Routers
app.include_router(api_router, prefix="/api/v1")

# Health Check / Welcome Endpoint
@app.get("/", tags=["Health Check"])
async def root():
    return {
        "success": True,
        "message": f"Welcome to the {settings.APP_NAME}!",
        "status": "online",
        "environment": settings.APP_ENV
    }

# Favicon handler to prevent 404 logging errors
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)
