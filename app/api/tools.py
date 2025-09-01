"""
MCP Tools API endpoints
All 7 MCP tools for Expokossodo events management
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.session import get_db_session
from app.auth import MCPUser, get_current_user, require_permission, check_rate_limit
from app.schemas.tools_in import (
    GetEventosInput, GetInscritosInput, GetAforoInput, 
    ConfirmarAsistenciaInput, GetEstadisticasInput, 
    BuscarRegistroInput, MapaSalaEventoInput
)
from app.schemas.tools_out import (
    GetEventosOutput, GetInscritosOutput, GetAforoOutput,
    ConfirmarAsistenciaOutput, GetEstadisticasOutput,
    BuscarRegistroOutput, MapaSalaEventoOutput, MCPError
)
from app.services.eventos import EventosService
from app.services.inscritos import InscritosService
from app.services.asistencia import AsistenciaService
from app.services.estadisticas import EstadisticasService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/getEventos", response_model=GetEventosOutput)
async def get_eventos(
    request: Request,
    input_data: GetEventosInput,
    db: AsyncSession = Depends(get_db_session),
    user: MCPUser = Depends(require_permission("getEventos"))
):
    """
    Get events with optional filters
    Permissions: LECTOR, STAFF_PUERTA, COORDINADOR
    """
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Rate limiting
    check_rate_limit(request, user, "getEventos")
    
    logger.info(
        "get_eventos_request",
        user_id=user.user_id,
        filters=input_data.dict(exclude_none=True),
        trace_id=trace_id
    )
    
    try:
        result = await EventosService.get_eventos(db, input_data, trace_id)
        
        logger.info(
            "get_eventos_success",
            user_id=user.user_id,
            total_found=result.total,
            trace_id=trace_id
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "get_eventos_error",
            user_id=user.user_id,
            error=str(e),
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPError(
                error="INTERNAL_ERROR",
                message="Error retrieving events",
                trace_id=trace_id
            ).dict()
        )


@router.post("/getInscritos", response_model=GetInscritosOutput)
async def get_inscritos(
    request: Request,
    input_data: GetInscritosInput,
    db: AsyncSession = Depends(get_db_session),
    user: MCPUser = Depends(require_permission("getInscritos"))
):
    """
    Get inscribed users with pagination
    Permissions: LECTOR, STAFF_PUERTA, COORDINADOR
    """
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Rate limiting
    check_rate_limit(request, user, "getInscritos")
    
    logger.info(
        "get_inscritos_request",
        user_id=user.user_id,
        filters=input_data.dict(exclude_none=True),
        trace_id=trace_id
    )
    
    try:
        result = await InscritosService.get_inscritos(db, input_data, trace_id)
        
        logger.info(
            "get_inscritos_success",
            user_id=user.user_id,
            total_found=result.total,
            page=result.page,
            trace_id=trace_id
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "get_inscritos_error",
            user_id=user.user_id,
            error=str(e),
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPError(
                error="INTERNAL_ERROR",
                message="Error retrieving inscribed users",
                trace_id=trace_id
            ).dict()
        )


@router.post("/getAforo", response_model=GetAforoOutput)
async def get_aforo(
    request: Request,
    input_data: GetAforoInput,
    db: AsyncSession = Depends(get_db_session),
    user: MCPUser = Depends(require_permission("getAforo"))
):
    """
    Get event capacity information
    Permissions: LECTOR, STAFF_PUERTA, COORDINADOR
    """
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Rate limiting
    check_rate_limit(request, user, "getAforo")
    
    logger.info(
        "get_aforo_request",
        user_id=user.user_id,
        evento_id=input_data.eventoId,
        trace_id=trace_id
    )
    
    try:
        result = await InscritosService.get_aforo(db, input_data, trace_id)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MCPError(
                    error="NOT_FOUND",
                    message="Event not found",
                    trace_id=trace_id,
                    details={"eventoId": input_data.eventoId}
                ).dict()
            )
        
        logger.info(
            "get_aforo_success",
            user_id=user.user_id,
            evento_id=input_data.eventoId,
            cupo_total=result.cupoTotal,
            inscritos=result.inscritos,
            trace_id=trace_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_aforo_error",
            user_id=user.user_id,
            evento_id=input_data.eventoId,
            error=str(e),
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPError(
                error="INTERNAL_ERROR",
                message="Error retrieving event capacity",
                trace_id=trace_id
            ).dict()
        )


@router.post("/confirmarAsistencia", response_model=ConfirmarAsistenciaOutput)
async def confirmar_asistencia(
    request: Request,
    input_data: ConfirmarAsistenciaInput,
    db: AsyncSession = Depends(get_db_session),
    user: MCPUser = Depends(require_permission("confirmarAsistencia"))
):
    """
    Confirm attendance (idempotent operation)
    Permissions: STAFF_PUERTA, COORDINADOR
    """
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Rate limiting (stricter for write operations)
    check_rate_limit(request, user, "confirmarAsistencia")
    
    logger.info(
        "confirmar_asistencia_request",
        user_id=user.user_id,
        registro_id=input_data.registroId,
        evento_id=input_data.eventoId,
        estado=input_data.estado,
        trace_id=trace_id
    )
    
    try:
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        result = await AsistenciaService.confirmar_asistencia(
            db=db,
            input_data=input_data,
            asesor_verificador=user.username,
            ip_verificacion=client_ip,
            trace_id=trace_id
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=MCPError(
                    error="NOT_FOUND",
                    message="Registration or event not found",
                    trace_id=trace_id,
                    details={
                        "registroId": input_data.registroId,
                        "eventoId": input_data.eventoId
                    }
                ).dict()
            )
        
        logger.info(
            "confirmar_asistencia_success",
            user_id=user.user_id,
            registro_id=input_data.registroId,
            evento_id=input_data.eventoId,
            verified_by=user.username,
            trace_id=trace_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "confirmar_asistencia_error",
            user_id=user.user_id,
            registro_id=input_data.registroId,
            evento_id=input_data.eventoId,
            error=str(e),
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPError(
                error="INTERNAL_ERROR",
                message="Error confirming attendance",
                trace_id=trace_id
            ).dict()
        )


@router.post("/getEstadisticas", response_model=GetEstadisticasOutput)
async def get_estadisticas(
    request: Request,
    input_data: GetEstadisticasInput,
    db: AsyncSession = Depends(get_db_session),
    user: MCPUser = Depends(require_permission("getEstadisticas"))
):
    """
    Get statistics and KPIs
    Permissions: LECTOR, STAFF_PUERTA, COORDINADOR
    """
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Rate limiting
    check_rate_limit(request, user, "getEstadisticas")
    
    logger.info(
        "get_estadisticas_request",
        user_id=user.user_id,
        granularidad=input_data.granularidad,
        kpis=input_data.kpis,
        trace_id=trace_id
    )
    
    try:
        result = await EstadisticasService.get_estadisticas(db, input_data, user, trace_id)
        
        logger.info(
            "get_estadisticas_success",
            user_id=user.user_id,
            granularidad=input_data.granularidad,
            kpis_calculated=len(result.kpis),
            trace_id=trace_id
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "get_estadisticas_error",
            user_id=user.user_id,
            granularidad=input_data.granularidad,
            error=str(e),
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPError(
                error="INTERNAL_ERROR",
                message="Error calculating statistics",
                trace_id=trace_id
            ).dict()
        )


@router.post("/buscarRegistro", response_model=BuscarRegistroOutput)
async def buscar_registro(
    request: Request,
    input_data: BuscarRegistroInput,
    db: AsyncSession = Depends(get_db_session),
    user: MCPUser = Depends(require_permission("buscarRegistro"))
):
    """
    Search user registrations
    Permissions: LECTOR, STAFF_PUERTA, COORDINADOR
    """
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Rate limiting
    check_rate_limit(request, user, "buscarRegistro")
    
    logger.info(
        "buscar_registro_request",
        user_id=user.user_id,
        query=input_data.query,
        campos=input_data.campos,
        trace_id=trace_id
    )
    
    try:
        result = await InscritosService.buscar_registro(db, input_data, trace_id)
        
        logger.info(
            "buscar_registro_success",
            user_id=user.user_id,
            query=input_data.query,
            total_found=result.total,
            trace_id=trace_id
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "buscar_registro_error",
            user_id=user.user_id,
            query=input_data.query,
            error=str(e),
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPError(
                error="INTERNAL_ERROR",
                message="Error searching registrations",
                trace_id=trace_id
            ).dict()
        )


@router.post("/mapaSalaEvento", response_model=MapaSalaEventoOutput)
async def mapa_sala_evento(
    request: Request,
    input_data: MapaSalaEventoInput,
    db: AsyncSession = Depends(get_db_session),
    user: MCPUser = Depends(require_permission("mapaSalaEvento"))
):
    """
    Get quick room-event mapping for a day (hot resource)
    Permissions: LECTOR, STAFF_PUERTA, COORDINADOR
    """
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    # Rate limiting
    check_rate_limit(request, user, "mapaSalaEvento")
    
    logger.info(
        "mapa_sala_evento_request",
        user_id=user.user_id,
        dia=input_data.dia.isoformat(),
        trace_id=trace_id
    )
    
    try:
        result = await EventosService.get_mapa_sala_evento(db, input_data, trace_id)
        
        logger.info(
            "mapa_sala_evento_success",
            user_id=user.user_id,
            dia=input_data.dia.isoformat(),
            total_events=result.total,
            trace_id=trace_id
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "mapa_sala_evento_error",
            user_id=user.user_id,
            dia=input_data.dia.isoformat(),
            error=str(e),
            trace_id=trace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MCPError(
                error="INTERNAL_ERROR",
                message="Error retrieving room-event mapping",
                trace_id=trace_id
            ).dict()
        )


# Health check for tools
@router.get("/health")
async def tools_health():
    """Tools health check"""
    return {
        "status": "healthy",
        "tools": [
            "getEventos",
            "getInscritos", 
            "getAforo",
            "confirmarAsistencia",
            "getEstadisticas",
            "buscarRegistro",
            "mapaSalaEvento"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }