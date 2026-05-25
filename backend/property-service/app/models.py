from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, func, Text, Float,  Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Inmueble(Base):
    __tablename__ = "Inmueble"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(12,2), nullable=False)
    tipo_id = Column(Integer, ForeignKey("TipoInmueble.id"), nullable=False)
    estado_id = Column(Integer, ForeignKey("EstadoInmueble.id"), nullable=False)
    propietario_id = Column(Integer, nullable=True)
    area_construccion = Column(Numeric(12,2))
    area_terreno = Column(Numeric(12,2))
    num_recamaras = Column(Integer)
    num_banos = Column(Integer)
    num_estacionamientos = Column(Integer)
    niveles = Column(Integer)
    amueblado = Column(Boolean, default=False)
    ubicacion_id = Column(Integer, ForeignKey("Ubicacion.id"), nullable=False)
    
    # Relaciones
    ubicacion = relationship("Ubicacion", back_populates="inmueble", cascade="all, delete-orphan", uselist=False, single_parent=True)
    imagenes = relationship("Imagen", back_populates="inmueble", cascade="all, delete-orphan")
    contactos = relationship("Contacto", back_populates="inmueble", cascade="all, delete-orphan")
    historial_estado = relationship("HistorialEstado", back_populates="inmueble", cascade="all, delete-orphan")
    estado_inmueble = relationship("EstadoInmueble", back_populates="inmuebles")
    tipo_inmueble = relationship("TipoInmueble", back_populates="inmuebles")
    historial_propietarios = relationship("HistorialPropietario", back_populates="inmueble", cascade="all, delete-orphan")


class EstadoInmueble(Base):
    __tablename__ = "EstadoInmueble"

    id = Column(Integer, primary_key=True)
    valor = Column(String(50), nullable=False, default='en venta')

    # Relación inversa
    inmuebles = relationship("Inmueble", back_populates="estado_inmueble") 
    historiales = relationship("HistorialEstado", back_populates="estado_inmueble")

class TipoInmueble(Base):
    __tablename__ = "TipoInmueble"

    id = Column(Integer, primary_key=True)
    valor = Column(String(50), nullable=False)

    # Relación inversa
    inmuebles = relationship("Inmueble", back_populates="tipo_inmueble") 
    

class EstadoRepublica(Base):
    __tablename__ = "EstadoRepublica"

    id = Column(Integer, primary_key=True)
    valor = Column(String(50), nullable=False)

    # Relación inversa
    ubicaciones = relationship("Ubicacion", back_populates="estado_republica")


class Ubicacion(Base):
    __tablename__ = "Ubicacion"

    id = Column(Integer, primary_key=True, nullable=False)
    direccion_completa = Column(Text)
    latitud = Column(Numeric(10,6))
    longitud = Column(Numeric(10,6))
    estado_id = Column(Integer, ForeignKey("EstadoRepublica.id"), nullable=False)
    ciudad = Column(String(100), nullable=False)
    colonia = Column(String(100), nullable=False)
    calle = Column(String(100), nullable=False)
    numero_exterior = Column(String(20), nullable=False)
    numero_interior = Column(String(20), nullable=True)
    codigo_postal = Column(String(100), nullable=False)
    
    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="ubicacion")
    estado_republica = relationship("EstadoRepublica", back_populates="ubicaciones")


class HistorialEstado(Base):
    __tablename__ = "HistorialEstado"

    id = Column(Integer, primary_key=True, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable = True)
    estado_id = Column(Integer, ForeignKey("EstadoInmueble.id"), nullable=False)
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="historial_estado")
    estado_inmueble = relationship("EstadoInmueble", back_populates="historiales")

class HistorialPropietario(Base):
    __tablename__ = "HistorialPropietario"

    id = Column(Integer, primary_key=True, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable = True)
    propietario_id = Column(Integer, nullable=False)
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="historial_propietarios")


class Imagen(Base):
    __tablename__ = "Imagen"

    id = Column(Integer, primary_key=True, nullable=False)
    url_archivo = Column(Text, nullable=False)
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="imagenes")


class Contacto(Base):
    __tablename__ = "Contacto"

    id = Column(Integer, primary_key=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="contactos")

