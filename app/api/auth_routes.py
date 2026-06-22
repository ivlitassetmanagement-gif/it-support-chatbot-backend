from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel
from app.services.auth_service import AuthService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()

class TokenRequest(BaseModel):
    pass

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600

@router.post("/request-key")
async def request_api_key(email: str, req: Request):
    '''Employee requests API key'''
    try:
        ip_address = req.client.host
        logger.info(f"API key requested by {email}")
        return {
            "status": "pending_approval",
            "message": f"API key request for {email} sent to admin"
        }
    except Exception as e:
        logger.error(f"Error requesting API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token", response_model=TokenResponse)
async def get_token(x_api_key: str = Header(None)):
    '''Exchange API key for JWT token'''
    try:
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key required")
        
        # For now, assume verification passed
        user_id = 1
        email = "user@company.com"
        
        token = auth_service.generate_jwt_token(user_id, email)
        logger.info(f"JWT token generated for user {user_id}")
        
        return TokenResponse(access_token=token)
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/verify")
async def verify_token(authorization: str = Header(None)):
    '''Verify JWT token'''
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization header required")
        
        token = authorization.replace("Bearer ", "")
        payload = auth_service.verify_jwt_token(token)
        
        return {
            "valid": True,
            "user_id": payload['user_id'],
            "email": payload['email']
        }
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
