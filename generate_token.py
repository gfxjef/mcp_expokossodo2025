#!/usr/bin/env python3
"""
Generate JWT tokens for testing MCP tools
"""
import sys
import os
sys.path.append(os.getcwd())

from app.auth import create_access_token, UserRole

def main():
    print("🔐 Generando tokens JWT para pruebas MCP-Expokossodo")
    print("=" * 60)
    
    # Token COORDINADOR (acceso completo)
    coordinador_token = create_access_token(
        user_id="coord_001",
        username="admin_coordinator",
        role=UserRole.COORDINADOR
    )
    
    # Token STAFF_PUERTA (para confirmar asistencia)
    staff_token = create_access_token(
        user_id="staff_001", 
        username="maria_recepcion",
        role=UserRole.STAFF_PUERTA
    )
    
    # Token LECTOR (solo lectura)
    lector_token = create_access_token(
        user_id="lect_001",
        username="guest_reader", 
        role=UserRole.LECTOR
    )
    
    print("✅ COORDINADOR TOKEN (acceso completo):")
    print(f"export TOKEN_COORDINADOR=\"{coordinador_token}\"")
    print()
    
    print("✅ STAFF_PUERTA TOKEN (+ confirmarAsistencia):")
    print(f"export TOKEN_STAFF=\"{staff_token}\"")
    print()
    
    print("✅ LECTOR TOKEN (solo lectura):")
    print(f"export TOKEN_LECTOR=\"{lector_token}\"")
    print()
    
    print("🎯 Para usar en curl:")
    print(f'export TOKEN="{coordinador_token}"')
    print()
    print("📝 Token válido por 30 minutos")
    
    return coordinador_token

if __name__ == "__main__":
    token = main()
    # También guardamos en variable de entorno para uso inmediato
    os.environ["TOKEN"] = token
    print(f"\n💡 Token guardado en variable TOKEN para uso inmediato")