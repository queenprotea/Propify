from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, func, Text, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Inmueble(Base):
    __tablename__ = "Inmueble"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(12, 2), nullable=False)
    # Taxonomía como columnas planas validadas por enums en la capa de aplicación
    tipo = Column(String(50), nullable=False)            # casa, departamento, ...
    operacion = Column(String(20), nullable=False)       # venta | renta
    uso = Column(String(20), nullable=False)             # residencial | comercial
    estado = Column(String(20), nullable=False, default="disponible")  # disponible|reservado|vendido|rentado
    propietario_id = Column(Integer, nullable=True)
    area_construccion = Column(Numeric(12, 2))
    area_terreno = Column(Numeric(12, 2))
    num_recamaras = Column(Integer)
    num_banos = Column(Integer)
    num_estacionamientos = Column(Integer)
    niveles = Column(Integer)
    amueblado = Column(Boolean, default=False)
    ubicacion_id = Column(Integer, ForeignKey("Ubicacion.id"), nullable=False)

    # Relaciones
    ubicacion = relationship("Ubicacion", back_populates="inmueble", uselist=False)
    imagenes = relationship("Imagen", back_populates="inmueble", cascade="all, delete-orphan")
    contactos = relationship("Contacto", back_populates="inmueble", cascade="all, delete-orphan")
    historial_estado = relationship("HistorialEstado", back_populates="inmueble", cascade="all, delete-orphan")
    historial_propietarios = relationship("HistorialPropietario", back_populates="inmueble", cascade="all, delete-orphan")


# Catálogo de estados de la república (para selector en el frontend; sin FK directa).
class EstadoRepublica(Base):
    __tablename__ = "EstadoRepublica"

    id = Column(Integer, primary_key=True)
    valor = Column(String(50), nullable=False, unique=True)


class Ubicacion(Base):
    __tablename__ = "Ubicacion"

    id = Column(Integer, primary_key=True, nullable=False)
    direccion_completa = Column(Text)          # autogenerada a partir de las partes
    latitud = Column(Numeric(10, 6))
    longitud = Column(Numeric(10, 6))
    estado = Column(String(50), nullable=False)   # nombre del estado de la república
    ciudad = Column(String(100), nullable=False)
    colonia = Column(String(100), nullable=False)
    calle = Column(String(100), nullable=False)
    numero_exterior = Column(String(20), nullable=False)
    numero_interior = Column(String(20), nullable=True)
    codigo_postal = Column(String(20), nullable=False)

    inmueble = relationship("Inmueble", back_populates="ubicacion")


class HistorialEstado(Base):
    __tablename__ = "HistorialEstado"

    id = Column(Integer, primary_key=True, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    estado = Column(String(20), nullable=False)
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    inmueble = relationship("Inmueble", back_populates="historial_estado")


class HistorialPropietario(Base):
    __tablename__ = "HistorialPropietario"

    id = Column(Integer, primary_key=True, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    propietario_id = Column(Integer, nullable=False)
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    inmueble = relationship("Inmueble", back_populates="historial_propietarios")


class Imagen(Base):
    __tablename__ = "Imagen"

    id = Column(Integer, primary_key=True, nullable=False)
    url_archivo = Column(Text, nullable=False)
    # WCAG 1.1.1: texto alternativo descriptivo obligatorio para cada imagen
    texto_alternativo = Column(String(255), nullable=False)
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    inmueble = relationship("Inmueble", back_populates="imagenes")


class Contacto(Base):
    __tablename__ = "Contacto"

    id = Column(Integer, primary_key=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    inmueble_id = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    inmueble = relationship("Inmueble", back_populates="contactos")
