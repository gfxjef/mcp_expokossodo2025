#!/bin/bash
# Script para probar todas las herramientas MCP

echo "🔐 Generando token fresco..."
TOKEN=$(python3 generate_token.py | grep "export TOKEN=" | head -1 | cut -d'"' -f2)
echo "Token generado: ${TOKEN:0:50}..."

echo ""
echo "🎯 Probando herramientas MCP..."

echo "1. 📊 getAforo - Evento ID 1:"
curl -s -X POST http://localhost:8000/mcp/tools/getAforo \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"eventoId": 1}' | python3 -m json.tool

echo ""
echo "2. 👥 getInscritos - Evento ID 1 (primera página):"
curl -s -X POST http://localhost:8000/mcp/tools/getInscritos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"eventoId": 1, "page": 1, "pageSize": 5}' | python3 -m json.tool

echo ""
echo "3. 🔍 buscarRegistro - Buscar 'Angel':"
curl -s -X POST http://localhost:8000/mcp/tools/buscarRegistro \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Angel", "campos": ["nombre", "email"]}' | python3 -m json.tool

echo ""
echo "4. 📈 getEstadisticas - KPIs básicos:"
curl -s -X POST http://localhost:8000/mcp/tools/getEstadisticas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"granularidad": "DIA", "rango": {"inicio": "2025-09-01", "fin": "2025-09-02"}, "kpis": ["inscritos", "tasaAsistencia"]}' | python3 -m json.tool

echo ""
echo "✅ Pruebas completadas!"