"""
Authentication and RBAC system
"""
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum
import jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from app.config import settings

logger = structlog.get_logger()


class UserRole(str, Enum):
    """User roles for RBAC"""
    LECTOR = "LECTOR"
    STAFF_PUERTA = "STAFF_PUERTA"
    COORDINADOR = "COORDINADOR"


class MCPUser:
    """MCP User with role information"""
    def __init__(self, user_id: str, username: str, role: UserRole, permissions: List[str] = None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.permissions = permissions or []


# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.LECTOR: [
        "getEventos",
        "getInscritos", 
        "getAforo",
        "getEstadisticas",
        "buscarRegistro",
        "mapaSalaEvento"
    ],
    UserRole.STAFF_PUERTA: [
        "getEventos",
        "getInscritos", 
        "getAforo",
        "getEstadisticas",
        "buscarRegistro",
        "mapaSalaEvento",
        "confirmarAsistencia"
    ],
    UserRole.COORDINADOR: [
        "getEventos",
        "getInscritos", 
        "getAforo",
        "getEstadisticas",
        "buscarRegistro",
        "mapaSalaEvento",
        "confirmarAsistencia",
        "estadisticasDetalladas"
    ]
}


def create_access_token(user_id: str, username: str, role: UserRole) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    payload = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def verify_token(token: str) -> Optional[MCPUser]:
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role_str: str = payload.get("role")
        
        if user_id is None or username is None or role_str is None:
            return None
        
        role = UserRole(role_str)
        permissions = ROLE_PERMISSIONS.get(role, [])
        
        return MCPUser(
            user_id=user_id,
            username=username,
            role=role,
            permissions=permissions
        )
    
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired", token_prefix=token[:20] if token else None)
        return None
    except jwt.JWTError as e:
        logger.warning("jwt_error", error=str(e), token_prefix=token[:20] if token else None)
        return None


# Security scheme
security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> MCPUser:
    """Get current authenticated user"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer", "X-Trace-ID": trace_id},
    )
    
    user = verify_token(credentials.credentials)
    if user is None:
        logger.warning(
            "authentication_failed",
            trace_id=trace_id,
            token_prefix=credentials.credentials[:20] if credentials.credentials else None
        )
        raise credentials_exception
    
    logger.info(
        "user_authenticated",
        user_id=user.user_id,
        username=user.username,
        role=user.role.value,
        trace_id=trace_id
    )
    
    return user


def require_permission(required_permission: str):
    """Decorator to require specific permission"""
    def permission_checker(user: MCPUser = Depends(get_current_user)):
        if required_permission not in user.permissions:
            logger.warning(
                "permission_denied",
                user_id=user.user_id,
                required_permission=required_permission,
                user_permissions=user.permissions,
                user_role=user.role.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
        return user
    return permission_checker


def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def role_checker(user: MCPUser = Depends(get_current_user)):
        if user.role.value != required_role.value:
            logger.warning(
                "role_access_denied",
                user_id=user.user_id,
                required_role=required_role.value,
                user_role=user.role.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required"
            )
        return user
    return role_checker


# Rate limiting middleware (simple in-memory implementation)
from collections import defaultdict
from time import time

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        """Check if request is allowed based on rate limit"""
        now = time()
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        # Check current count
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(request: Request, user: MCPUser, tool_name: str):
    """Check rate limits based on user role and tool type"""
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Define limits based on tool type
    write_tools = ["confirmarAsistencia"]
    is_write_tool = tool_name in write_tools
    
    # Set limits based on tool type
    if is_write_tool:
        limit = settings.rate_limit_writes_per_second
    else:
        limit = settings.rate_limit_reads_per_second
    
    # Create rate limit key
    rate_key = f"{user.user_id}:{tool_name}"
    
    # Check rate limit
    if not rate_limiter.is_allowed(rate_key, limit, 60):
        logger.warning(
            "rate_limit_exceeded",
            user_id=user.user_id,
            tool_name=tool_name,
            limit=limit,
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"X-Trace-ID": trace_id}
        )
    
    logger.debug(
        "rate_limit_ok",
        user_id=user.user_id,
        tool_name=tool_name,
        limit=limit,
        trace_id=trace_id
    )


# Middleware function for authentication (not used in this implementation)
async def auth_middleware(request: Request, call_next):
    """Optional auth middleware - currently not used"""
    response = await call_next(request)
    return response