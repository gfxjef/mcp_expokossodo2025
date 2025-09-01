"""
Events service - Business logic for event-related operations
"""
from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.queries import EventosQueries
from app.schemas.tools_in import GetEventosInput, MapaSalaEventoInput
from app.schemas.tools_out import GetEventosOutput, EventoInfo, MapaSalaEventoOutput, SalaEventoItem

logger = structlog.get_logger()


class EventosService:
    """Service for events operations"""
    
    @staticmethod
    async def get_eventos(
        db: AsyncSession,
        input_data: GetEventosInput,
        trace_id: str = None
    ) -> GetEventosOutput:
        """Get events with filters"""
        
        logger.info(
            "get_eventos_started",
            filters=input_data.dict(exclude_none=True),
            trace_id=trace_id
        )
        
        try:
            eventos = await EventosQueries.get_eventos_filtered(
                db=db,
                fecha_inicio=input_data.fechaInicio,
                fecha_fin=input_data.fechaFin,
                sede=input_data.sede,
                sala=input_data.sala,
                query=input_data.query,
                limit=50,  # Default limit
                offset=0
            )
            
            # Transform to output format
            eventos_info = []
            for evento in eventos:
                evento_info = EventoInfo(
                    id=evento.id,
                    titulo=evento.titulo_charla,
                    sede=None,  # Not available in current schema
                    sala=evento.sala,
                    fechaInicio=evento.fecha,
                    fechaFin=None,  # Single date events
                    cupoTotal=evento.slots_disponibles or 60,
                    estado="ACTIVO" if evento.disponible else "INACTIVO",
                    expositor=evento.expositor
                )
                eventos_info.append(evento_info)
            
            result = GetEventosOutput(
                eventos=eventos_info,
                total=len(eventos_info)
            )
            
            logger.info(
                "get_eventos_completed",
                total_found=len(eventos_info),
                trace_id=trace_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "get_eventos_error",
                error=str(e),
                filters=input_data.dict(exclude_none=True),
                trace_id=trace_id
            )
            raise
    
    @staticmethod
    async def get_mapa_sala_evento(
        db: AsyncSession,
        input_data: MapaSalaEventoInput,
        trace_id: str = None
    ) -> MapaSalaEventoOutput:
        """Get room-event mapping for a specific day"""
        
        logger.info(
            "get_mapa_sala_evento_started",
            dia=input_data.dia.isoformat(),
            trace_id=trace_id
        )
        
        try:
            items_data = await EventosQueries.get_mapa_sala_evento(
                db=db,
                dia=input_data.dia
            )
            
            # Transform to output format
            items = [
                SalaEventoItem(
                    sala=item["sala"],
                    eventoId=item["eventoId"],
                    titulo=item["titulo"],
                    horario=item["horario"]
                )
                for item in items_data
            ]
            
            result = MapaSalaEventoOutput(
                items=items,
                dia=input_data.dia,
                total=len(items)
            )
            
            logger.info(
                "get_mapa_sala_evento_completed",
                total_events=len(items),
                dia=input_data.dia.isoformat(),
                trace_id=trace_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "get_mapa_sala_evento_error",
                error=str(e),
                dia=input_data.dia.isoformat(),
                trace_id=trace_id
            )
            raise