"""
Optimized database queries for MCP tools
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload

from app.db.models import (
    ExpoEventos, ExpoRegistros, ExpoRegistroEventos, 
    ExpoAsistenciasGenerales, ExpoAsistenciasPorSala,
    ExpoMarcas, ExpoConsultas
)


class EventosQueries:
    """Queries for eventos (events)"""
    
    @staticmethod
    async def get_eventos_filtered(
        db: AsyncSession,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        sede: Optional[str] = None,
        sala: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ExpoEventos]:
        """Get events with filters"""
        
        stmt = select(ExpoEventos).options(selectinload(ExpoEventos.marca))
        
        # Apply filters
        conditions = []
        
        if fecha_inicio:
            conditions.append(ExpoEventos.fecha >= fecha_inicio)
        if fecha_fin:
            conditions.append(ExpoEventos.fecha <= fecha_fin)
        if sala:
            conditions.append(ExpoEventos.sala.ilike(f"%{sala}%"))
        if query:
            conditions.append(
                or_(
                    ExpoEventos.titulo_charla.ilike(f"%{query}%"),
                    ExpoEventos.descripcion.ilike(f"%{query}%"),
                    ExpoEventos.expositor.ilike(f"%{query}%")
                )
            )
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(ExpoEventos.fecha, ExpoEventos.hora).limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_mapa_sala_evento(
        db: AsyncSession,
        dia: date
    ) -> List[Dict[str, Any]]:
        """Get quick room-event mapping for a specific day"""
        
        stmt = select(
            ExpoEventos.sala,
            ExpoEventos.id.label("evento_id"),
            ExpoEventos.titulo_charla.label("titulo"),
            ExpoEventos.hora.label("horario")
        ).where(
            ExpoEventos.fecha == dia
        ).order_by(ExpoEventos.sala, ExpoEventos.hora)
        
        result = await db.execute(stmt)
        return [
            {
                "sala": row.sala,
                "eventoId": row.evento_id,
                "titulo": row.titulo,
                "horario": row.horario
            }
            for row in result.fetchall()
        ]


class InscritosQueries:
    """Queries for inscribed users"""
    
    @staticmethod
    async def get_inscritos_by_evento(
        db: AsyncSession,
        evento_id: int,
        estado_inscripcion: Optional[str] = None,  # Ignored - no real estado field
        page: int = 1,
        page_size: int = 20
    ) -> tuple[int, List[Dict[str, Any]]]:
        """Get inscribed users by event with pagination"""
        
        # Count query - fixed join syntax
        count_stmt = select(func.count(ExpoRegistroEventos.id)).select_from(
            ExpoRegistroEventos.__table__.join(ExpoRegistros.__table__)
        ).where(ExpoRegistroEventos.evento_id == evento_id)
        
        # Data query - using REAL column names
        stmt = select(
            ExpoRegistros.id.label("registro_id"),
            ExpoRegistros.nombres,  # Real column name
            ExpoRegistros.empresa,
            ExpoRegistros.correo,   # Real column name
            ExpoRegistroEventos.fecha_seleccion.label("creado_en")  # Real column name
        ).select_from(
            ExpoRegistroEventos.__table__.join(ExpoRegistros.__table__)
        ).where(
            ExpoRegistroEventos.evento_id == evento_id
        )
        
        # Note: estado_inscripcion filter ignored as table has no estado field
        
        # Get total count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(ExpoRegistroEventos.fecha_seleccion)).limit(page_size).offset(offset)
        
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        lista = [
            {
                "registroId": row.registro_id,
                "nombre": row.nombres,  # Use real column name
                "empresa": row.empresa,
                "email": row.correo,    # Use real column name
                "estado": "INSCRITO",   # Default since no real estado field
                "creadoEn": row.creado_en
            }
            for row in rows
        ]
        
        return total, lista
    
    @staticmethod
    async def get_inscritos_by_filters(
        db: AsyncSession,
        dia: Optional[date] = None,
        sala: Optional[str] = None,
        estado_inscripcion: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[int, List[Dict[str, Any]]]:
        """Get inscribed users by day/room filters"""
        
        # Base query joining tables - using REAL column names
        base_query = select(
            ExpoRegistros.id.label("registro_id"),
            ExpoRegistros.nombres,  # Real column name
            ExpoRegistros.empresa,
            ExpoRegistros.correo,   # Real column name
            ExpoRegistroEventos.fecha_seleccion.label("creado_en")  # Real column name
        ).select_from(
            ExpoRegistroEventos.__table__.join(ExpoRegistros.__table__).join(ExpoEventos.__table__)
        )
        
        # Apply filters
        conditions = []
        if dia:
            conditions.append(ExpoEventos.fecha == dia)
        if sala:
            conditions.append(ExpoEventos.sala.ilike(f"%{sala}%"))
        # Note: estado_inscripcion filter ignored as table has no estado field
        
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # Count query
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Data query with pagination
        offset = (page - 1) * page_size
        stmt = base_query.order_by(desc(ExpoRegistroEventos.fecha_seleccion)).limit(page_size).offset(offset)
        
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        lista = [
            {
                "registroId": row.registro_id,
                "nombre": row.nombres,  # Use real column name
                "empresa": row.empresa,
                "email": row.correo,    # Use real column name
                "estado": "INSCRITO",   # Default since no real estado field
                "creadoEn": row.creado_en
            }
            for row in rows
        ]
        
        return total, lista


class AforoQueries:
    """Queries for event capacity"""
    
    @staticmethod
    async def get_aforo_evento(db: AsyncSession, evento_id: int) -> Dict[str, Any]:
        """Get event capacity information"""
        
        # Get event info
        evento_stmt = select(
            ExpoEventos.slots_disponibles.label("cupo_total"),
            ExpoEventos.slots_ocupados,
            ExpoEventos.titulo_charla
        ).where(ExpoEventos.id == evento_id)
        
        evento_result = await db.execute(evento_stmt)
        evento = evento_result.first()
        
        if not evento:
            return None
        
        # Count inscribed users
        inscritos_stmt = select(func.count(ExpoRegistroEventos.id)).where(
            ExpoRegistroEventos.evento_id == evento_id
        )
        inscritos_result = await db.execute(inscritos_stmt)
        inscritos = inscritos_result.scalar()
        
        # Count confirmed users - removed estado field reference (not in real table)
        # Using inscritos count as confirmados since no real estado field exists
        confirmados = inscritos
        
        # Count attendance at door
        asistencia_stmt = select(func.count(ExpoAsistenciasPorSala.id)).where(
            ExpoAsistenciasPorSala.evento_id == evento_id
        )
        asistencia_result = await db.execute(asistencia_stmt)
        asistencia_puerta = asistencia_result.scalar()
        
        # Calculate estimated no-show
        no_show_estimado = max(0, confirmados - asistencia_puerta)
        
        return {
            "cupoTotal": evento.cupo_total,
            "inscritos": inscritos,
            "confirmados": confirmados,
            "asistenciaEnPuerta": asistencia_puerta,
            "noShowEstimado": no_show_estimado
        }


class AsistenciaQueries:
    """Queries for attendance management"""
    
    @staticmethod
    async def confirmar_asistencia(
        db: AsyncSession,
        registro_id: int,
        evento_id: int,
        estado: str,
        asesor_verificador: str,
        observacion: Optional[str] = None,
        ip_verificacion: Optional[str] = None
    ) -> bool:
        """Confirm attendance (idempotent)"""
        
        # Check if already exists
        existing_stmt = select(ExpoAsistenciasPorSala).where(
            and_(
                ExpoAsistenciasPorSala.registro_id == registro_id,
                ExpoAsistenciasPorSala.evento_id == evento_id
            )
        )
        
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # Update existing record
            existing.asesor_verificador = asesor_verificador
            existing.fecha_ingreso = func.current_timestamp()
            if observacion:
                existing.notas = observacion
            if ip_verificacion:
                existing.ip_verificacion = ip_verificacion
        else:
            # Create new record
            # Get user QR code
            qr_stmt = select(ExpoRegistros.qr_code).where(ExpoRegistros.id == registro_id)
            qr_result = await db.execute(qr_stmt)
            qr_code = qr_result.scalar()
            
            new_asistencia = ExpoAsistenciasPorSala(
                registro_id=registro_id,
                evento_id=evento_id,
                qr_escaneado=qr_code or f"manual_{registro_id}_{evento_id}",
                asesor_verificador=asesor_verificador,
                ip_verificacion=ip_verificacion,
                notas=observacion
            )
            db.add(new_asistencia)
        
        await db.commit()
        return True


class BusquedaQueries:
    """Search queries"""
    
    @staticmethod
    async def buscar_registro(
        db: AsyncSession,
        query: str,
        campos: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search user registrations"""
        
        if not campos:
            campos = ["nombre", "email", "empresa"]
        
        conditions = []
        search_term = f"%{query}%"
        
        if "nombre" in campos:
            conditions.append(ExpoRegistros.nombres.ilike(search_term))  # Use real column name
        if "email" in campos:
            conditions.append(ExpoRegistros.correo.ilike(search_term))   # Use real column name
        if "empresa" in campos:
            conditions.append(ExpoRegistros.empresa.ilike(search_term))
        if "doc" in campos:
            # Note: Real table doesn't have documento field, but keeping for completeness
            pass
        
        if not conditions:
            return []
        
        # Main query
        stmt = select(ExpoRegistros).where(or_(*conditions)).limit(20)
        result = await db.execute(stmt)
        registros = result.scalars().all()
        
        # Get associated events for each user
        coincidencias = []
        for registro in registros:
            eventos_stmt = select(
                ExpoEventos.id.label("evento_id"),
                ExpoEventos.titulo_charla
            ).select_from(
                ExpoRegistroEventos.__table__.join(ExpoEventos.__table__)
            ).where(ExpoRegistroEventos.registro_id == registro.id)
            
            eventos_result = await db.execute(eventos_stmt)
            eventos_asociados = [
                {
                    "eventoId": row.evento_id,
                    "titulo": row.titulo_charla,
                    "estado": "INSCRITO"  # Default since no real estado field
                }
                for row in eventos_result.fetchall()
            ]
            
            coincidencias.append({
                "registroId": registro.id,
                "nombre": registro.nombres,  # Use real column name
                "empresa": registro.empresa,
                "email": registro.correo,    # Use real column name
                "eventosAsociados": eventos_asociados
            })
        
        return coincidencias