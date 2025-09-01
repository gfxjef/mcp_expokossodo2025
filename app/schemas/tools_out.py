"""
Pydantic schemas for MCP tool outputs
"""
from datetime import date, datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class EventoInfo(BaseModel):
    """Event information schema"""
    id: int
    titulo: str
    sede: Optional[str] = None
    sala: str
    fechaInicio: date
    fechaFin: Optional[date] = None
    cupoTotal: int
    estado: str = "ACTIVO"
    expositor: Optional[str] = None
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "id": 123,
                "titulo": "Innovaciones en Salud Digital",
                "sede": "Centro de Convenciones",
                "sala": "Auditorio A",
                "fechaInicio": "2025-09-15",
                "cupoTotal": 60,
                "estado": "ACTIVO",
                "expositor": "Dr. Juan Pérez"
            }
        }


class GetEventosOutput(BaseModel):
    """Output schema for getEventos tool"""
    eventos: List[EventoInfo] = Field(..., description="Lista de eventos")
    total: Optional[int] = Field(None, description="Total de eventos encontrados")
    
    class Config:
        json_schema_extra = {
            "example": {
                "eventos": [
                    {
                        "id": 123,
                        "titulo": "Innovaciones en Salud Digital",
                        "sala": "Auditorio A",
                        "fechaInicio": "2025-09-15",
                        "cupoTotal": 60,
                        "estado": "ACTIVO"
                    }
                ],
                "total": 1
            }
        }


class InscritoInfo(BaseModel):
    """Inscribed user information schema"""
    registroId: int
    nombre: str
    empresa: Optional[str] = None
    email: str
    estado: str
    creadoEn: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "registroId": 1037,
                "nombre": "Juan Pérez",
                "empresa": "Tech Corp",
                "email": "juan@techcorp.com",
                "estado": "CONFIRMADO",
                "creadoEn": "2025-08-30T10:30:00"
            }
        }


class GetInscritosOutput(BaseModel):
    """Output schema for getInscritos tool"""
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página actual")
    pageSize: int = Field(..., description="Tamaño de página")
    lista: List[InscritoInfo] = Field(..., description="Lista de inscritos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "page": 1,
                "pageSize": 20,
                "lista": [
                    {
                        "registroId": 1037,
                        "nombre": "Juan Pérez",
                        "empresa": "Tech Corp",
                        "email": "juan@techcorp.com",
                        "estado": "CONFIRMADO",
                        "creadoEn": "2025-08-30T10:30:00"
                    }
                ]
            }
        }


class GetAforoOutput(BaseModel):
    """Output schema for getAforo tool"""
    cupoTotal: int = Field(..., description="Capacidad total del evento")
    inscritos: int = Field(..., description="Total de inscritos")
    confirmados: int = Field(..., description="Total de confirmados")
    asistenciaEnPuerta: int = Field(..., description="Asistencia registrada en puerta")
    noShowEstimado: int = Field(..., description="Estimación de no shows")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cupoTotal": 60,
                "inscritos": 75,
                "confirmados": 45,
                "asistenciaEnPuerta": 38,
                "noShowEstimado": 7
            }
        }


class ConfirmarAsistenciaOutput(BaseModel):
    """Output schema for confirmarAsistencia tool"""
    ok: bool = Field(..., description="Confirmación de éxito")
    timestamp: datetime = Field(..., description="Timestamp de la confirmación")
    registroId: int = Field(..., description="ID del registro procesado")
    eventoId: int = Field(..., description="ID del evento procesado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "timestamp": "2025-08-30T14:30:00",
                "registroId": 1037,
                "eventoId": 123
            }
        }


class KpiInfo(BaseModel):
    """KPI information schema"""
    nombre: str = Field(..., description="Nombre del KPI")
    valor: Any = Field(..., description="Valor del KPI")
    detalle: Optional[Dict[str, Any]] = Field(None, description="Detalle adicional del KPI")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "tasaAsistencia",
                "valor": 84.5,
                "detalle": {
                    "confirmados": 45,
                    "asistieron": 38,
                    "porcentaje": 84.5
                }
            }
        }


class GetEstadisticasOutput(BaseModel):
    """Output schema for getEstadisticas tool"""
    kpis: List[KpiInfo] = Field(..., description="Lista de KPIs calculados")
    granularidad: str = Field(..., description="Granularidad usada")
    periodo: Dict[str, str] = Field(..., description="Período analizado")
    
    class Config:
        json_schema_extra = {
            "example": {
                "kpis": [
                    {
                        "nombre": "inscritos",
                        "valor": 150
                    },
                    {
                        "nombre": "tasaAsistencia",
                        "valor": 84.5,
                        "detalle": {
                            "confirmados": 45,
                            "asistieron": 38
                        }
                    }
                ],
                "granularidad": "DIA",
                "periodo": {
                    "inicio": "2025-08-01",
                    "fin": "2025-08-31"
                }
            }
        }


class EventoAsociado(BaseModel):
    """Associated event schema"""
    eventoId: int
    titulo: Optional[str] = None
    estado: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "eventoId": 123,
                "titulo": "Innovaciones en Salud Digital",
                "estado": "CONFIRMADO"
            }
        }


class CoincidenciaRegistro(BaseModel):
    """Registry match schema"""
    registroId: int
    nombre: str
    empresa: Optional[str] = None
    email: str
    eventosAsociados: List[EventoAsociado] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "registroId": 1037,
                "nombre": "Juan Pérez",
                "empresa": "Tech Corp",
                "email": "juan@techcorp.com",
                "eventosAsociados": [
                    {
                        "eventoId": 123,
                        "estado": "CONFIRMADO"
                    }
                ]
            }
        }


class BuscarRegistroOutput(BaseModel):
    """Output schema for buscarRegistro tool"""
    coincidencias: List[CoincidenciaRegistro] = Field(..., description="Registros encontrados")
    total: int = Field(..., description="Total de coincidencias")
    
    class Config:
        json_schema_extra = {
            "example": {
                "coincidencias": [
                    {
                        "registroId": 1037,
                        "nombre": "Juan Pérez",
                        "empresa": "Tech Corp",
                        "email": "juan@techcorp.com",
                        "eventosAsociados": []
                    }
                ],
                "total": 1
            }
        }


class SalaEventoItem(BaseModel):
    """Room-event mapping item schema"""
    sala: str
    eventoId: int
    titulo: str
    horario: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "sala": "Auditorio A",
                "eventoId": 123,
                "titulo": "Innovaciones en Salud Digital",
                "horario": "10:00-11:30"
            }
        }


class MapaSalaEventoOutput(BaseModel):
    """Output schema for mapaSalaEvento tool"""
    items: List[SalaEventoItem] = Field(..., description="Mapeo sala-evento")
    dia: date = Field(..., description="Día consultado")
    total: int = Field(..., description="Total de eventos del día")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "sala": "Auditorio A",
                        "eventoId": 123,
                        "titulo": "Innovaciones en Salud Digital",
                        "horario": "10:00-11:30"
                    }
                ],
                "dia": "2025-08-30",
                "total": 1
            }
        }


# Error schemas
class MCPError(BaseModel):
    """Standard MCP error schema"""
    error: str = Field(..., description="Código de error")
    message: str = Field(..., description="Mensaje de error")
    trace_id: Optional[str] = Field(None, description="ID de trazabilidad")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "NOT_FOUND",
                "message": "Evento no encontrado",
                "trace_id": "abc123-def456",
                "details": {
                    "eventoId": 999
                }
            }
        }