"""
Estadisticas service - Business logic for statistics and KPIs
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
import structlog

from app.auth import MCPUser
from app.db.models import ExpoEventos, ExpoRegistros, ExpoRegistroEventos, ExpoAsistenciasPorSala
from app.schemas.tools_in import GetEstadisticasInput
from app.schemas.tools_out import GetEstadisticasOutput, KpiInfo

logger = structlog.get_logger()


class EstadisticasService:
    """Service for statistics and KPIs operations"""
    
    @staticmethod
    async def get_estadisticas(
        db: AsyncSession,
        input_data: GetEstadisticasInput,
        user: MCPUser,
        trace_id: str = None
    ) -> GetEstadisticasOutput:
        """Get statistics and KPIs"""
        
        logger.info(
            "get_estadisticas_started",
            granularidad=input_data.granularidad,
            kpis=input_data.kpis,
            rango=input_data.rango,
            trace_id=trace_id
        )
        
        try:
            # Parse date range
            fecha_inicio = datetime.strptime(input_data.rango["inicio"], "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(input_data.rango["fin"], "%Y-%m-%d").date()
            
            # Calculate requested KPIs
            kpis = []
            for kpi_name in input_data.kpis:
                kpi_result = await EstadisticasService._calculate_kpi(
                    db=db,
                    kpi_name=kpi_name,
                    granularidad=input_data.granularidad,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    user=user,
                    trace_id=trace_id
                )
                if kpi_result:
                    kpis.append(kpi_result)
            
            result = GetEstadisticasOutput(
                kpis=kpis,
                granularidad=input_data.granularidad,
                periodo={
                    "inicio": input_data.rango["inicio"],
                    "fin": input_data.rango["fin"]
                }
            )
            
            logger.info(
                "get_estadisticas_completed",
                granularidad=input_data.granularidad,
                kpis_calculated=len(kpis),
                trace_id=trace_id
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "get_estadisticas_error",
                error=str(e),
                granularidad=input_data.granularidad,
                kpis=input_data.kpis,
                trace_id=trace_id
            )
            raise
    
    @staticmethod
    async def _calculate_kpi(
        db: AsyncSession,
        kpi_name: str,
        granularidad: str,
        fecha_inicio: date,
        fecha_fin: date,
        user: MCPUser,
        trace_id: str = None
    ) -> Optional[KpiInfo]:
        """Calculate individual KPI"""
        
        try:
            if kpi_name == "inscritos":
                return await EstadisticasService._kpi_inscritos(
                    db, granularidad, fecha_inicio, fecha_fin, trace_id
                )
            elif kpi_name == "confirmados":
                # For simplicity, confirmados = inscritos (no real estado field)
                return await EstadisticasService._kpi_inscritos(
                    db, granularidad, fecha_inicio, fecha_fin, trace_id, alias="confirmados"
                )
            elif kpi_name == "tasaAsistencia":
                return await EstadisticasService._kpi_tasa_asistencia(
                    db, granularidad, fecha_inicio, fecha_fin, trace_id
                )
            elif kpi_name == "noShow":
                return await EstadisticasService._kpi_no_show(
                    db, granularidad, fecha_inicio, fecha_fin, trace_id
                )
            elif kpi_name == "leadsPorFuente":
                return await EstadisticasService._kpi_leads_por_fuente(
                    db, granularidad, fecha_inicio, fecha_fin, trace_id
                )
            elif kpi_name == "eventosMasPopulares":
                return await EstadisticasService._kpi_eventos_populares(
                    db, granularidad, fecha_inicio, fecha_fin, trace_id
                )
            else:
                logger.warning(f"Unknown KPI: {kpi_name}", trace_id=trace_id)
                return None
                
        except Exception as e:
            logger.error(
                "calculate_kpi_error",
                kpi_name=kpi_name,
                error=str(e),
                trace_id=trace_id
            )
            return None
    
    @staticmethod
    async def _kpi_inscritos(
        db: AsyncSession,
        granularidad: str,
        fecha_inicio: date,
        fecha_fin: date,
        trace_id: str = None,
        alias: str = "inscritos"
    ) -> KpiInfo:
        """Calculate inscribed users KPI"""
        
        stmt = select(func.count(ExpoRegistroEventos.id)).select_from(
            ExpoRegistroEventos.join(ExpoEventos)
        ).where(
            and_(
                ExpoEventos.fecha >= fecha_inicio,
                ExpoEventos.fecha <= fecha_fin
            )
        )
        
        result = await db.execute(stmt)
        total = result.scalar() or 0
        
        return KpiInfo(
            nombre=alias,
            valor=total,
            detalle={
                "granularidad": granularidad,
                "periodo": f"{fecha_inicio} a {fecha_fin}"
            }
        )
    
    @staticmethod
    async def _kpi_tasa_asistencia(
        db: AsyncSession,
        granularidad: str,
        fecha_inicio: date,
        fecha_fin: date,
        trace_id: str = None
    ) -> KpiInfo:
        """Calculate attendance rate KPI"""
        
        # Count inscribed
        inscritos_stmt = select(func.count(ExpoRegistroEventos.id)).select_from(
            ExpoRegistroEventos.join(ExpoEventos)
        ).where(
            and_(
                ExpoEventos.fecha >= fecha_inicio,
                ExpoEventos.fecha <= fecha_fin
            )
        )
        
        inscritos_result = await db.execute(inscritos_stmt)
        total_inscritos = inscritos_result.scalar() or 0
        
        # Count attended
        asistieron_stmt = select(func.count(ExpoAsistenciasPorSala.id)).select_from(
            ExpoAsistenciasPorSala.join(ExpoEventos)
        ).where(
            and_(
                ExpoEventos.fecha >= fecha_inicio,
                ExpoEventos.fecha <= fecha_fin
            )
        )
        
        asistieron_result = await db.execute(asistieron_stmt)
        total_asistieron = asistieron_result.scalar() or 0
        
        # Calculate rate
        tasa = (total_asistieron * 100.0 / total_inscritos) if total_inscritos > 0 else 0
        
        return KpiInfo(
            nombre="tasaAsistencia",
            valor=round(tasa, 2),
            detalle={
                "inscritos": total_inscritos,
                "asistieron": total_asistieron,
                "porcentaje": round(tasa, 2)
            }
        )
    
    @staticmethod
    async def _kpi_no_show(
        db: AsyncSession,
        granularidad: str,
        fecha_inicio: date,
        fecha_fin: date,
        trace_id: str = None
    ) -> KpiInfo:
        """Calculate no-show KPI"""
        
        # Get inscritos and asistieron counts
        tasa_kpi = await EstadisticasService._kpi_tasa_asistencia(
            db, granularidad, fecha_inicio, fecha_fin, trace_id
        )
        
        total_inscritos = tasa_kpi.detalle["inscritos"]
        total_asistieron = tasa_kpi.detalle["asistieron"]
        no_shows = total_inscritos - total_asistieron
        
        return KpiInfo(
            nombre="noShow",
            valor=no_shows,
            detalle={
                "inscritos": total_inscritos,
                "asistieron": total_asistieron,
                "noShows": no_shows
            }
        )
    
    @staticmethod
    async def _kpi_leads_por_fuente(
        db: AsyncSession,
        granularidad: str,
        fecha_inicio: date,
        fecha_fin: date,
        trace_id: str = None
    ) -> KpiInfo:
        """Calculate leads by source KPI"""
        
        stmt = select(
            func.coalesce(ExpoRegistros.empresa, "Sin empresa").label("fuente"),
            func.count().label("total")
        ).select_from(
            ExpoRegistros.join(ExpoRegistroEventos).join(ExpoEventos)
        ).where(
            and_(
                ExpoEventos.fecha >= fecha_inicio,
                ExpoEventos.fecha <= fecha_fin
            )
        ).group_by(ExpoRegistros.empresa).order_by(func.count().desc()).limit(10)
        
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        fuentes = [
            {"fuente": row.fuente, "total": row.total}
            for row in rows
        ]
        
        total_leads = sum(item["total"] for item in fuentes)
        
        return KpiInfo(
            nombre="leadsPorFuente",
            valor=total_leads,
            detalle={
                "totalLeads": total_leads,
                "topFuentes": fuentes
            }
        )
    
    @staticmethod
    async def _kpi_eventos_populares(
        db: AsyncSession,
        granularidad: str,
        fecha_inicio: date,
        fecha_fin: date,
        trace_id: str = None
    ) -> KpiInfo:
        """Calculate most popular events KPI"""
        
        stmt = select(
            ExpoEventos.id,
            ExpoEventos.titulo_charla,
            ExpoEventos.sala,
            func.count(ExpoRegistroEventos.id).label("inscritos")
        ).select_from(
            ExpoEventos.join(ExpoRegistroEventos)
        ).where(
            and_(
                ExpoEventos.fecha >= fecha_inicio,
                ExpoEventos.fecha <= fecha_fin
            )
        ).group_by(
            ExpoEventos.id, ExpoEventos.titulo_charla, ExpoEventos.sala
        ).order_by(func.count(ExpoRegistroEventos.id).desc()).limit(10)
        
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        eventos = [
            {
                "eventoId": row.id,
                "titulo": row.titulo_charla,
                "sala": row.sala,
                "inscritos": row.inscritos
            }
            for row in rows
        ]
        
        return KpiInfo(
            nombre="eventosMasPopulares",
            valor=len(eventos),
            detalle={
                "totalEventos": len(eventos),
                "topEventos": eventos
            }
        )