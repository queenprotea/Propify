from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, func, Text, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Inmueble(Base):
    __tablename__ = "Inmueble"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Float)
    tipo = Column(String(50), nullable=False)
    estado = Column(String(50), nullable=False) # en renta / en venta, reservado, vendido / rentado
    propietario_id = Column(Integer, nullable=True)
    area_construccion = Column(Float)
    area_terreno = Column(Float)
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
    
    
    

class Ubicacion(Base):
    __tablename__ = "Ubicacion"

    id = Column(Integer, primary_key=True, nullable=False)
    direccion_completa = Column(Text)
    latitud = Column(Float)
    longitud = Column(Float)
    estado = Column(String(100), nullable=False)
    ciudad = Column(String(100), nullable=False)
    colonia = Column(String(100), nullable=False)
    calle = Column(String(100), nullable=False)
    numero_exterior = Column(String(20), nullable=False)
    numero_interior = Column(String(20), nullable=True)
    codigo_postal = Column(String(100), nullable=False)
    
    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="ubicacion")


class HistorialEstado(Base):
    __tablename__ = "HistorialEstado"

    id = Column(Integer, primary_key=True, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable = True)
    estado = Column(String(50), nullable=False)
    id_inmueble = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="historial_estado")


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
    id_inmueble = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    # Relación inversa
    inmueble = relationship("Inmueble", back_populates="contactos")

