"""
Authentication utilities for JWT token management.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import asyncpg

from .models import pwd_context

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

async def create_access_token(user_id: str, username: str) -> Dict[str, Any]:
    """Create JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    jti = str(uuid.uuid4())  # Unique token ID for blacklisting
    
    payload = {
        "sub": user_id,
        "username": username,
        "exp": expire,
        "iat": now,
        "jti": jti
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    expires_in = int((expire - now).total_seconds())
    
    return {
        "access_token": token,
        "expires_in": expires_in,
        "jti": jti,
        "expires_at": expire
    }

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

async def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)

async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password."""
    # TEMPORARY: Simple authentication for testing
    # TODO: Implement proper database authentication after database is working
    
    # For testing AUTH-02, accept any username/password combination
    if username and password:
        return {
            "id": "test-user-id",
            "username": username,
            "email": f"{username}@example.com",
            "full_name": f"Test User {username}",
            "is_superuser": False
        }
    
    return None

async def blacklist_token(jti: str, user_id: str, expires_at: datetime):
    """Add token to blacklist."""
    # TEMPORARY: No-op for testing
    # TODO: Implement proper token blacklisting after database is working
    pass

async def is_token_blacklisted(jti: str) -> bool:
    """Check if token is blacklisted."""
    # TEMPORARY: Always return False for testing
    # TODO: Implement proper blacklist checking after database is working
    return False

async def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check if token is blacklisted
        if await is_token_blacklisted(payload.get("jti")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )