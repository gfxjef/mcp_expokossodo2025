# MCP-Expokossodo 2025

Sistema MCP (Model Context Protocol) para gestión de eventos Expokossodo con FastAPI, SQLAlchemy y autenticación JWT.

## Características Principales

- 🔧 **7 Herramientas MCP**: getEventos, getInscritos, getAforo, confirmarAsistencia, getEstadisticas, buscarRegistro, mapaSalaEvento
- 🗃️ **Base de Datos Real**: Integración con MySQL (48 eventos, 1,010+ usuarios, 2,224+ inscripciones)
- 🛡️ **Seguridad**: Autenticación JWT con 3 roles (LECTOR, STAFF_PUERTA, COORDINADOR)
- 📊 **Logging Estructurado**: JSON logs con trace IDs
- ⚡ **Rate Limiting**: 10 rps lecturas, 3 rps escrituras
- 🐳 **Docker Ready**: Containerización incluida

## Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/gfxjef/mcp_expokossodo2025.git
cd mcp_expokossodo2025

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
cp .env.example .env
# Editar .env con credenciales

# Iniciar servidor
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Generar tokens de prueba
python3 generate_token.py

# Probar herramientas MCP
./test_tools.sh
```

## Estado del Proyecto

✅ **Sistema Completamente Funcional**
- Todas las herramientas MCP operativas
- Conexión a base de datos real verificada
- Autenticación y permisos implementados
- Pruebas exitosas realizadas

🚀 **Listo para Producción**

Desarrollado para Expokossodo 2025 - Sistema de gestión de eventos y asistencia en tiempo real.

