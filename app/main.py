from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import routes, auth_routes, websocket_routes, analytics_routes, document_routes
from app.core.config import settings
from app.services.auth_service import AuthService
import logging
import os

auth_service = AuthService()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='IT Support Chatbot v2.0',
    version='2.0.0',
    description='Secure chatbot with ChromaDB + Authentication'
)

# CORS Middleware (from .env configuration)
try:
    allowed_origins = settings.cors_allowed_origins
except:
    # Fallback if config fails to load
    allowed_origins = [
        "https://yourcompany.com",
        "https://intranet.yourcompany.com",
        "http://localhost:3000",
        "http://localhost:8001",
        "https://*.vercel.app",      
        "https://*.onrender.com"
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"]
)
logger.info(f"CORS enabled for: {allowed_origins}")

# Authentication Middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Skip auth for health and auth endpoints
    if request.url.path in ["/health", "/auth/token", "/auth/request-key"] or request.url.path.startswith("/frontend"):
        return await call_next(request)

    # Verify JWT token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            payload = auth_service.verify_jwt_token(token)
            request.state.user_id = payload.get("user_id", 1)
            request.state.email = payload.get("email", "unknown")
            logger.debug(f"Authenticated user {request.state.user_id}")
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            request.state.user_id = "unknown"
    else:
        request.state.user_id = "unknown"

    return await call_next(request)

# Include routers with /api prefix
app.include_router(routes.router, prefix="/api")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(websocket_routes.router, prefix="/api")
app.include_router(analytics_routes.router, prefix="/api")
app.include_router(document_routes.router, prefix="/api")

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Frontend mounted at /frontend from {frontend_dir}")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0-chromadb-secure"}

@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check for debugging"""
    try:
        from app.services.chromadb_service import ChromaDBService
        chromadb_service = ChromaDBService()

        return {
            "status": "ok",
            "version": "2.0-chromadb-secure",
            "services": {
                "chromadb": "ready",
                "embeddings": "lazy-loaded",
                "llm": "configured"
            },
            "config": {
                "llm_provider": settings.llm_provider,
                "embedding_model": settings.embedding_model,
                "cors_origins": settings.cors_allowed_origins
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "detail": str(e)}

logger.info("Application started")
