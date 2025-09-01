"""
Pydantic schemas for MCP tool inputs
"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class GetEventosInput(BaseModel):
    """Input schema for getEventos tool"""
    fechaInicio: Optional[date] = Field(None, description="Fecha de inicio para filtrar eventos")
    fechaFin: Optional[date] = Field(None, description="Fecha de fin para filtrar eventos")
    sede: Optional[str] = Field(None, description="Sede para filtrar eventos")
    sala: Optional[str] = Field(None, description="Sala para filtrar eventos")
    query: Optional[str] = Field(None, description="Búsqueda en título/descripción")
    
    @validator('fechaFin')
    def validate_fecha_range(cls, v, values):
        if v and 'fechaInicio' in values and values['fechaInicio']:
            if v < values['fechaInicio']:
                raise ValueError('fechaFin debe ser mayor o igual a fechaInicio')
        return v


class GetInscritosInput(BaseModel):
    """Input schema for getInscritos tool"""
    eventoId: Optional[int] = Field(None, description="ID del evento específico")
    dia: Optional[date] = Field(None, description="Día para filtrar")
    sala: Optional[str] = Field(None, description="Sala para filtrar")
    estadoInscripcion: Optional[str] = Field(
        None, 
        description="Estado de inscripción",
        pattern="^(INSCRITO|CONFIRMADO|CANCELADO)$"
    )
    page: int = Field(1, ge=1, description="Número de página")
    pageSize: int = Field(20, ge=1, le=100, description="Tamaño de página")
    
    @validator('sala', 'estadoInscripcion', pre=True)
    def empty_string_to_none(cls, v):
        return None if v == "" else v
    
    class Config:
        json_schema_extra = {
            "example": {
                "eventoId": 123,
                "page": 1,
                "pageSize": 20
            }
        }


class GetAforoInput(BaseModel):
    """Input schema for getAforo tool"""
    eventoId: int = Field(..., description="ID del evento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "eventoId": 123
            }
        }


class ConfirmarAsistenciaInput(BaseModel):
    """Input schema for confirmarAsistencia tool"""
    registroId: int = Field(..., description="ID del registro")
    eventoId: int = Field(..., description="ID del evento")
    estado: str = Field(
        ..., 
        description="Estado de asistencia",
        pattern="^(PRESENTE|AUSENTE|TARDE)$"
    )
    observacion: Optional[str] = Field(None, max_length=500, description="Observación opcional")
    
    class Config:
        json_schema_extra = {
            "example": {
                "registroId": 1037,
                "eventoId": 123,
                "estado": "PRESENTE",
                "observacion": "Llegó puntual"
            }
        }


class GetEstadisticasInput(BaseModel):
    """Input schema for getEstadisticas tool"""
    granularidad: str = Field(
        ..., 
        description="Granularidad de estadísticas",
        pattern="^(DIA|EVENTO|SALA)$"
    )
    rango: dict = Field(..., description="Rango de fechas con 'inicio' y 'fin'")
    kpis: List[str] = Field(
        ..., 
        description="Lista de KPIs solicitados",
        min_items=1
    )
    
    @validator('rango')
    def validate_rango(cls, v):
        if not isinstance(v, dict):
            raise ValueError('rango debe ser un objeto con inicio y fin')
        if 'inicio' not in v or 'fin' not in v:
            raise ValueError('rango debe tener campos inicio y fin')
        return v
    
    @validator('kpis')
    def validate_kpis(cls, v):
        valid_kpis = [
            'inscritos', 'confirmados', 'tasaAsistencia', 
            'noShow', 'leadsPorFuente', 'eventosMasPopulares'
        ]
        for kpi in v:
            if kpi not in valid_kpis:
                raise ValueError(f'KPI {kpi} no válido. KPIs disponibles: {valid_kpis}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "granularidad": "DIA",
                "rango": {
                    "inicio": "2025-08-01",
                    "fin": "2025-08-31"
                },
                "kpis": ["inscritos", "confirmados", "tasaAsistencia"]
            }
        }


class BuscarRegistroInput(BaseModel):
    """Input schema for buscarRegistro tool"""
    query: str = Field(..., min_length=2, description="Término de búsqueda")
    campos: Optional[List[str]] = Field(
        ["nombre", "email", "empresa"], 
        description="Campos donde buscar"
    )
    
    @validator('campos')
    def validate_campos(cls, v):
        if v is None:
            return ["nombre", "email", "empresa"]
        valid_campos = ["nombre", "email", "empresa", "doc"]
        for campo in v:
            if campo not in valid_campos:
                raise ValueError(f'Campo {campo} no válido. Campos disponibles: {valid_campos}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "juan perez",
                "campos": ["nombre", "email"]
            }
        }


class MapaSalaEventoInput(BaseModel):
    """Input schema for mapaSalaEvento tool"""
    dia: date = Field(..., description="Día para obtener el mapa sala-evento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dia": "2025-08-30"
            }
        }