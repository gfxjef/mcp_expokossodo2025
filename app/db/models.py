"""
SQLAlchemy models for Expokossodo database
Based on the REAL discovered table structure from database inventory
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ExpoEventos(Base):
    """expokossodo_eventos table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_eventos"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(String(20), nullable=False)
    sala = Column(String(50), nullable=False, index=True)
    titulo_charla = Column(String(200), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=True)
    expositor = Column(String(100), nullable=False)
    pais = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=True)
    imagen_url = Column(String(500), nullable=True)
    post = Column(String(500), nullable=True)
    marca_id = Column(Integer, ForeignKey("expokossodo_marcas.id"), nullable=True, index=True)
    slots_disponibles = Column(Integer, default=60, nullable=True)
    slots_ocupados = Column(Integer, default=0, nullable=True)
    disponible = Column(Boolean, default=True, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    rubro = Column(JSON, nullable=True)
    
    # Relationships
    marca = relationship("ExpoMarcas", back_populates="eventos")
    registros_eventos = relationship("ExpoRegistroEventos", back_populates="evento")
    asistencias_sala = relationship("ExpoAsistenciasPorSala", back_populates="evento")


class ExpoRegistros(Base):
    """expokossodo_registros table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_registros"
    
    id = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)  # Real field name
    correo = Column(String(100), nullable=False, index=True)  # Real field name
    empresa = Column(String(100), nullable=False)
    cargo = Column(String(100), nullable=False)
    numero = Column(String(20), nullable=False)  # Real field name
    expectativas = Column(Text, nullable=True)
    eventos_seleccionados = Column(JSON, nullable=True)
    qr_code = Column(String(500), nullable=True)
    qr_generado_at = Column(TIMESTAMP, nullable=True)
    asistencia_general_confirmada = Column(Boolean, default=False, nullable=True)
    fecha_asistencia_general = Column(TIMESTAMP, nullable=True)
    fecha_registro = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    confirmado = Column(Boolean, default=False, nullable=True)
    
    # Relationships
    registros_eventos = relationship("ExpoRegistroEventos", back_populates="registro")
    asistencias_generales = relationship("ExpoAsistenciasGenerales", back_populates="registro")
    asistencias_sala = relationship("ExpoAsistenciasPorSala", back_populates="registro")
    consultas = relationship("ExpoConsultas", back_populates="registro")


class ExpoRegistroEventos(Base):
    """expokossodo_registro_eventos table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_registro_eventos"
    
    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("expokossodo_registros.id"), nullable=False, index=True)
    evento_id = Column(Integer, ForeignKey("expokossodo_eventos.id"), nullable=False, index=True)
    fecha_seleccion = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    
    # Relationships
    registro = relationship("ExpoRegistros", back_populates="registros_eventos")
    evento = relationship("ExpoEventos", back_populates="registros_eventos")


class ExpoAsistenciasGenerales(Base):
    """expokossodo_asistencias_generales table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_asistencias_generales"
    
    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("expokossodo_registros.id"), nullable=False, index=True)
    qr_escaneado = Column(String(500), nullable=False, index=True)
    fecha_escaneo = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    verificado_por = Column(String(100), default="Sistema", nullable=True)
    ip_verificacion = Column(String(45), nullable=True)
    
    # Relationships
    registro = relationship("ExpoRegistros", back_populates="asistencias_generales")


class ExpoAsistenciasPorSala(Base):
    """expokossodo_asistencias_por_sala table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_asistencias_por_sala"
    
    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("expokossodo_registros.id"), nullable=False, index=True)
    evento_id = Column(Integer, ForeignKey("expokossodo_eventos.id"), nullable=False, index=True)
    qr_escaneado = Column(String(500), nullable=False, index=True)
    fecha_ingreso = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    asesor_verificador = Column(String(100), nullable=False)
    ip_verificacion = Column(String(45), nullable=True)
    notas = Column(Text, nullable=True)
    
    # Relationships
    registro = relationship("ExpoRegistros", back_populates="asistencias_sala")
    evento = relationship("ExpoEventos", back_populates="asistencias_sala")


class ExpoMarcas(Base):
    """expokossodo_marcas table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_marcas"
    
    id = Column(Integer, primary_key=True, index=True)
    marca = Column(String(100), nullable=False, unique=True)  # Real field name
    expositor = Column(String(100), nullable=True)
    logo = Column(String(500), nullable=True)  # Real field name
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)
    
    # Relationships
    eventos = relationship("ExpoEventos", back_populates="marca")


class ExpoConsultas(Base):
    """expokossodo_consultas table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_consultas"
    
    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("expokossodo_registros.id"), nullable=False, index=True)
    asesor_nombre = Column(String(100), nullable=False, index=True)
    consulta = Column(Text, nullable=False)
    fecha_consulta = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    uso_transcripcion = Column(Boolean, default=False, nullable=True)
    resumen = Column(Text, nullable=False)
    
    # Relationships
    registro = relationship("ExpoRegistros", back_populates="consultas")


class ExpoHorarios(Base):
    """expokossodo_horarios table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_horarios"
    
    id = Column(Integer, primary_key=True, index=True)
    horario = Column(String(20), nullable=False, unique=True)
    activo = Column(Boolean, default=True, nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)


class ExpoFechaInfo(Base):
    """expokossodo_fecha_info table model - REAL STRUCTURE"""
    __tablename__ = "expokossodo_fecha_info"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True, index=True)
    rubro = Column(String(100), nullable=False, index=True)
    titulo_dia = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    ponentes_destacados = Column(JSON, nullable=True)
    marcas_patrocinadoras = Column(JSON, nullable=True)
    paises_participantes = Column(JSON, nullable=True)
    imagen_url = Column(String(500), nullable=True)
    activo = Column(Boolean, default=True, nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)