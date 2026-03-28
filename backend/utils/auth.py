import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from core.config import settings

# Token expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30    # 30 days

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(email: str, additional_claims: Dict[str, Any] = None) -> str:
    """
    Create a short-lived access token (JWT)
    
    Args:
        email: User's email address
        additional_claims: Extra claims to include in the token (e.g., is_tester, is_admin)
    
    Returns:
        Encoded JWT access token
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(email: str) -> str:
    """
    Create a long-lived refresh token
    
    Args:
        email: User's email address
    
    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)  # Unique token ID for revocation
    }
    
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_token_pair(email: str, additional_claims: Dict[str, Any] = None) -> Tuple[str, str]:
    """
    Create both access and refresh tokens
    
    Args:
        email: User's email address
        additional_claims: Extra claims for access token
    
    Returns:
        Tuple of (access_token, refresh_token)
    """
    access_token = create_access_token(email, additional_claims)
    refresh_token = create_refresh_token(email)
    return access_token, refresh_token

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify a refresh token and return the email if valid
    
    Args:
        token: Refresh token string
    
    Returns:
        User's email if token is valid, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload.get("sub")
    return None

def generate_password_reset_token() -> str:
    """Generate a secure password reset token"""
    return secrets.token_urlsafe(32)

def is_token_expired(token: str) -> bool:
    """Check if a token has expired"""
    payload = decode_token(token)
    return payload is None
