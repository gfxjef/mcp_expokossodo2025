"""
Inscritos service - Business logic for inscribed users operations
"""
from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.queries import InscritosQueries, AforoQueries, BusquedaQueries
from app.schemas.tools_in import GetInscritosInput, GetAforoInput, BuscarRegistroInput
from app.schemas.tools_out import (
    GetInscritosOutput, InscritoInfo, GetAforoOutput, 
    BuscarRegistroOutput, CoincidenciaRegistro
)

logger = structlog.get_logger()


class InscritosService:
    """Service for inscribed users operations"""
    
    @staticmethod
    async def get_inscritos(
        db: AsyncSession,
        input_data: GetInscritosInput,
        trace_id: str = None
    ) -> GetInscritosOutput:
        """Get inscribed users with pagination"""
        
        logger.info(
            "get_inscritos_started",
            filters=input_data.dict(exclude_none=True),
            trace_id=trace_id
        )
        
        try:
            # Route to appropriate query based on input
            if input_data.eventoId:
                # Query by specific event
                total, lista_data = await InscritosQueries.get_inscritos_by_evento(
                    db=db,
                    evento_id=input_data.eventoId,
                    estado_inscripcion=input_data.estadoInscripcion,
                    page=input_data.page,
                    page_size=input_data.pageSize
                )
            else:
                # Query by day/sala filters
                total, lista_data = await InscritosQueries.get_inscritos_by_filters(
                    db=db,
                    dia=input_data.dia,
                    sala=input_data.sala,
                    estado_inscripcion=input_data.estadoInscripcion,
                    page=input_data.page,
                    page_size=input_data.pageSize
                )
            
            # Transform to output format
            lista = [
                InscritoInfo(
                    registroId=item["registroId"],
                    nombre=item["nombre"],
                    empresa=item["empresa"],
                    email=item["email"],
                    estado=item["estado"],
                    creadoEn=item["creadoEn"]
                )
                for item in lista_data
            ]
            
            result = GetInscritosOutput(
                total=total,
                page=input_data.page,
                pageSize=input_data.pageSize,
                lista=lista
            )
            
            logger.info(
                "get_inscritos_completed",
                total_found=total,
                page=input_data.page,
                trace_id=trace_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "get_inscritos_error",
                error=str(e),
                filters=input_data.dict(exclude_none=True),
                trace_id=trace_id
            )
            raise
    
    @staticmethod
    async def get_aforo(
        db: AsyncSession,
        input_data: GetAforoInput,
        trace_id: str = None
    ) -> Optional[GetAforoOutput]:
        """Get event capacity information"""
        
        logger.info(
            "get_aforo_started",
            evento_id=input_data.eventoId,
            trace_id=trace_id
        )
        
        try:
            aforo_data = await AforoQueries.get_aforo_evento(
                db=db,
                evento_id=input_data.eventoId
            )
            
            if aforo_data is None:
                logger.warning(
                    "get_aforo_not_found",
                    evento_id=input_data.eventoId,
                    trace_id=trace_id
                )
                return None
            
            result = GetAforoOutput(
                cupoTotal=aforo_data["cupoTotal"],
                inscritos=aforo_data["inscritos"],
                confirmados=aforo_data["confirmados"],
                asistenciaEnPuerta=aforo_data["asistenciaEnPuerta"],
                noShowEstimado=aforo_data["noShowEstimado"]
            )
            
            logger.info(
                "get_aforo_completed",
                evento_id=input_data.eventoId,
                cupo_total=result.cupoTotal,
                inscritos=result.inscritos,
                trace_id=trace_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "get_aforo_error",
                error=str(e),
                evento_id=input_data.eventoId,
                trace_id=trace_id
            )
            raise
    
    @staticmethod
    async def buscar_registro(
        db: AsyncSession,
        input_data: BuscarRegistroInput,
        trace_id: str = None
    ) -> BuscarRegistroOutput:
        """Search user registrations"""
        
        logger.info(
            "buscar_registro_started",
            query=input_data.query,
            campos=input_data.campos,
            trace_id=trace_id
        )
        
        try:
            coincidencias_data = await BusquedaQueries.buscar_registro(
                db=db,
                query=input_data.query,
                campos=input_data.campos
            )
            
            # Transform to output format
            coincidencias = [
                CoincidenciaRegistro(
                    registroId=item["registroId"],
                    nombre=item["nombre"],
                    empresa=item["empresa"],
                    email=item["email"],
                    eventosAsociados=item["eventosAsociados"]
                )
                for item in coincidencias_data
            ]
            
            result = BuscarRegistroOutput(
                coincidencias=coincidencias,
                total=len(coincidencias)
            )
            
            logger.info(
                "buscar_registro_completed",
                query=input_data.query,
                total_found=len(coincidencias),
                trace_id=trace_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "buscar_registro_error",
                error=str(e),
                query=input_data.query,
                trace_id=trace_id
            )
            raise