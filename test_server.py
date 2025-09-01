#!/usr/bin/env python3
"""
Quick test script for MCP-Expokossodo server
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.main import app
from app.config import settings
from app.auth import create_access_token, UserRole

async def test_server():
    """Test server startup and basic functionality"""
    print("🔧 Testing MCP-Expokossodo Server")
    print("=" * 50)
    
    # Test configuration
    print(f"✅ App Name: {settings.app_name}")
    print(f"✅ Version: {settings.app_version}")
    print(f"✅ Database URL: {settings.database_url}")
    print(f"✅ Debug Mode: {settings.debug}")
    
    # Test JWT token creation
    test_token = create_access_token(
        user_id="test_user",
        username="test_coordinator",
        role=UserRole.COORDINADOR
    )
    print(f"✅ JWT Token created: {test_token[:50]}...")
    
    # Test database connection (basic check)
    try:
        from app.db.session import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection: OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    print("\n🎯 Server ready for testing!")
    print("Available endpoints:")
    print("- GET  /health")
    print("- GET  /mcp/tools/health")
    print("- POST /mcp/tools/getEventos")
    print("- POST /mcp/tools/getInscritos")
    print("- POST /mcp/tools/getAforo")
    print("- POST /mcp/tools/confirmarAsistencia")
    print("- POST /mcp/tools/getEstadisticas")
    print("- POST /mcp/tools/buscarRegistro")
    print("- POST /mcp/tools/mapaSalaEvento")
    
    print(f"\n🚀 Start server with: python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_server())