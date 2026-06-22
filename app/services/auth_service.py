import jwt
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    '''Handle authentication: API keys and JWT tokens'''
    
    def __init__(self):
        self.jwt_secret = settings.jwt_secret
        self.jwt_algorithm = "HS256"
        self.api_key_prefix = "sk_live_"
    
    def hash_api_key(self, api_key: str) -> str:
        '''Hash API key for secure storage'''
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def generate_api_key(self) -> str:
        '''Generate random API key'''
        random_part = secrets.token_urlsafe(32)
        api_key = f"{self.api_key_prefix}{random_part}"
        return api_key
    
    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        '''Verify API key matches stored hash'''
        provided_hash = self.hash_api_key(api_key)
        return provided_hash == stored_hash
    
    def generate_jwt_token(self, user_id: int, email: str) -> str:
        '''Generate JWT token (time-limited)'''
        payload = {
            'user_id': user_id,
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token: str) -> dict:
        '''Verify JWT token and extract info'''
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise
