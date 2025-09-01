"""
Asistencia service - Business logic for attendance operations
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.queries import AsistenciaQueries
from app.schemas.tools_in import ConfirmarAsistenciaInput
from app.schemas.tools_out import ConfirmarAsistenciaOutput

logger = structlog.get_logger()


class AsistenciaService:
    """Service for attendance operations"""
    
    @staticmethod
    async def confirmar_asistencia(
        db: AsyncSession,
        input_data: ConfirmarAsistenciaInput,
        asesor_verificador: str,
        ip_verificacion: Optional[str] = None,
        trace_id: str = None
    ) -> Optional[ConfirmarAsistenciaOutput]:
        """Confirm attendance (idempotent operation)"""
        
        logger.info(
            "confirmar_asistencia_started",
            registro_id=input_data.registroId,
            evento_id=input_data.eventoId,
            estado=input_data.estado,
            asesor=asesor_verificador,
            trace_id=trace_id
        )
        
        try:
            # Perform idempotent attendance confirmation
            success = await AsistenciaQueries.confirmar_asistencia(
                db=db,
                registro_id=input_data.registroId,
                evento_id=input_data.eventoId,
                estado=input_data.estado,
                asesor_verificador=asesor_verificador,
                observacion=input_data.observacion,
                ip_verificacion=ip_verificacion
            )
            
            if not success:
                logger.warning(
                    "confirmar_asistencia_not_found",
                    registro_id=input_data.registroId,
                    evento_id=input_data.eventoId,
                    trace_id=trace_id
                )
                return None
            
            result = ConfirmarAsistenciaOutput(
                ok=True,
                timestamp=datetime.utcnow(),
                registroId=input_data.registroId,
                eventoId=input_data.eventoId
            )
            
            logger.info(
                "confirmar_asistencia_completed",
                registro_id=input_data.registroId,
                evento_id=input_data.eventoId,
                estado=input_data.estado,
                asesor=asesor_verificador,
                trace_id=trace_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "confirmar_asistencia_error",
                error=str(e),
                registro_id=input_data.registroId,
                evento_id=input_data.eventoId,
                trace_id=trace_id
            )
            raise