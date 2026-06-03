from sqlalchemy.orm import Session
from app import models, schemas
from app.enums import TipoInmueble, EstadoInmueble
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timezone


def _build_direccion_completa(calle, numero_exterior, colonia, ciudad, estado, codigo_postal) -> str:
    """Genera la dirección legible a partir de las partes (WCAG: alternativa textual al mapa)."""
    return (
        f"{calle} {numero_exterior}, {colonia}, "
        f"{ciudad}, {estado}, CP {codigo_postal}"
    )


def get_inmueble_by_id(db: Session, inmueble_id: int):
    return db.query(models.Inmueble).filter(models.Inmueble.id == inmueble_id).first()


def create_inmueble(db: Session, inmueble: schemas.InmuebleCreate):
    try:
        db_inmueble = models.Inmueble(
            titulo=inmueble.titulo,
            descripcion = inmueble.descripcion,
            precio = inmueble.precio,
            tipo=inmueble.tipo.value,
            operacion=inmueble.operacion.value,
            uso=inmueble.uso.value,
            estado=inmueble.estado.value,
            area_construccion= inmueble.area_construccion,
            area_terreno= inmueble.area_terreno,
            num_recamaras =inmueble.num_recamaras, 
            num_banos =inmueble.num_banos, 
            num_estacionamientos =inmueble.num_estacionamientos, 
            niveles =inmueble.niveles,
            amueblado =inmueble.amueblado,  
            ubicacion_id=inmueble.ubicacion_id
        )
        db.add(db_inmueble)
        db.commit()
        db.refresh(db_inmueble)
        return db_inmueble
    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )


def update_inmueble(db: Session, inmueble_id: int, inmueble_update: schemas.InmuebleUpdate):
    try:
        db_inmueble = get_inmueble_by_id(db, inmueble_id)
        if not db_inmueble:
            return None

        # Solo actualiza los campos que fueron enviados
        if inmueble_update.titulo is not None:
            db_inmueble.titulo = inmueble_update.titulo

        if inmueble_update.descripcion is not None:
            db_inmueble.descripcion = inmueble_update.descripcion

        if inmueble_update.precio is not None:
            db_inmueble.precio = inmueble_update.precio

        if inmueble_update.tipo is not None:
            db_inmueble.tipo = inmueble_update.tipo.value

        if inmueble_update.operacion is not None:
            db_inmueble.operacion = inmueble_update.operacion.value

        if inmueble_update.uso is not None:
            db_inmueble.uso = inmueble_update.uso.value

        if inmueble_update.estado is not None:
            db_inmueble.estado = inmueble_update.estado.value

        if inmueble_update.area_construccion is not None:
            db_inmueble.area_construccion = inmueble_update.area_construccion

        if inmueble_update.area_terreno is not None:
            db_inmueble.area_terreno = inmueble_update.area_terreno

        if inmueble_update.num_recamaras is not None:
            db_inmueble.num_recamaras = inmueble_update.num_recamaras

        if inmueble_update.num_banos is not None:
            db_inmueble.num_banos = inmueble_update.num_banos

        if inmueble_update.num_estacionamientos is not None:
            db_inmueble.num_estacionamientos = inmueble_update.num_estacionamientos
        
        if inmueble_update.niveles is not None:
            db_inmueble.niveles = inmueble_update.niveles
        
        if inmueble_update.amueblado is not None:
            db_inmueble.amueblado = inmueble_update.amueblado
        
        if inmueble_update.ubicacion_id is not None:
            db_inmueble.ubicacion_id = inmueble_update.ubicacion_id
    
        db.commit()
        db.refresh(db_inmueble)
        return db_inmueble
    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )


def update_inmueble_status(
    db: Session,
    inmueble_id: int,
    new_status: EstadoInmueble
):
    try:

        property_db = (
            db.query(models.Inmueble)
            .filter(models.Inmueble.id == inmueble_id)
            .first()
        )

        if not property_db:
            return None

        property_db.estado = new_status.value

        db.commit()
        db.refresh(property_db)

        return property_db

    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )


def delete_inmueble(db: Session, inmueble_id: int):
    try:
        inm = get_inmueble_by_id(db, inmueble_id)
        if not inm:
            return False
        db.delete(inm)   # cascada elimina imágenes, contactos e historial asociados
        db.commit()
        return True
    except OperationalError:
        db.rollback()
        raise ConnectionError("Database connection error, please try again later")
    except SQLAlchemyError:
        db.rollback()
        raise Exception("Database error, please try again later")


def get_disponible_inmuebles(db: Session):
    return (
        db.query(models.Inmueble)
        .filter(
            models.Inmueble.estado == EstadoInmueble.DISPONIBLE.value
        )
        .all()
    )

def get_inmuebles_by_tipo(
    db: Session,
    tipo: TipoInmueble
):
    return (
        db.query(models.Inmueble)
        .filter(
            models.Inmueble.tipo == tipo.value
        )
        .all()
    )

def get_inmuebles_by_propietario(db: Session, pro_id: int):
    return db.query(models.Inmueble).filter(models.Inmueble.propietario_id == pro_id).all()


def get_inmuebles_by_titulo(db: Session, titulo: str):
    return db.query(models.Inmueble).filter(
        models.Inmueble.titulo.ilike(f"%{titulo}%")
    ).all()

def get_inmuebles_by_descripcion(db: Session, des: str):
    return db.query(models.Inmueble).filter(
        models.Inmueble.descripcion.ilike(f"%{des}%")
    ).all()


def get_all_inmuebles(db: Session, limit: int = 100, offset: int = 0):
    return (
        db.query(models.Inmueble)
        .offset(offset)
        .limit(limit)
        .all()
    )


#--------------------------
#       ubicacion 
#--------------------------

def get_ubicacion_by_id(db: Session, ubicacion_id: int):
    return db.query(models.Ubicacion).filter(models.Ubicacion.id == ubicacion_id).first()


def create_ubicacion(db: Session, ubicacion: schemas.UbicacionCreate):
    try:
        direccion = ubicacion.direccion_completa or _build_direccion_completa(
            ubicacion.calle,
            ubicacion.numero_exterior,
            ubicacion.colonia,
            ubicacion.ciudad,
            ubicacion.estado,
            ubicacion.codigo_postal,
        )
        db_ubicacion = models.Ubicacion(
            direccion_completa=direccion,
            latitud = ubicacion.latitud,
            longitud = ubicacion.longitud,
            estado=ubicacion.estado,
            ciudad=ubicacion.ciudad,
            colonia= ubicacion.colonia,
            calle= ubicacion.calle,
            numero_exterior =ubicacion.numero_exterior,
            numero_interior =ubicacion.numero_interior,
            codigo_postal =ubicacion.codigo_postal,

        )
        db.add(db_ubicacion)
        db.commit()
        db.refresh(db_ubicacion)
        return db_ubicacion
    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )
    

def update_ubicacion(
    db: Session,
    ubicacion_id: int,
    ubicacion_update: schemas.UbicacionUpdate
):
    try:

        db_ubicacion = get_ubicacion_by_id(
            db,
            ubicacion_id
        )

        if not db_ubicacion:
            return None

        updates = ubicacion_update.model_dump(
            exclude_none=True
        )

        for key, value in updates.items():
            setattr(db_ubicacion, key, value)

        # Si cambió alguna parte de la dirección y no se envió una explícita,
        # se regenera la dirección completa (campo "autogenerado").
        partes = {"calle", "numero_exterior", "colonia", "ciudad", "estado", "codigo_postal"}
        if partes & updates.keys() and "direccion_completa" not in updates:
            db_ubicacion.direccion_completa = _build_direccion_completa(
                db_ubicacion.calle,
                db_ubicacion.numero_exterior,
                db_ubicacion.colonia,
                db_ubicacion.ciudad,
                db_ubicacion.estado,
                db_ubicacion.codigo_postal,
            )

        db.commit()
        db.refresh(db_ubicacion)

        return db_ubicacion

    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error"
        )
    

def get_ubicaciones_by_direccion_completa(db: Session, query: str):
    return db.query(models.Ubicacion).filter(
        models.Ubicacion.direccion_completa.ilike(f"%{query}%")
    ).all()



#--------------------------
#     historialEstado 
#--------------------------

def get_historial_estado_by_id(db: Session, historialEstado_id: int):
    return db.query(models.HistorialEstado).filter(models.HistorialEstado.id == historialEstado_id).first()

def get_historial_estado_by_inmueble(db: Session, inmueble_id: int):
    return db.query(models.HistorialEstado).filter(models.HistorialEstado.inmueble_id == inmueble_id).order_by(models.HistorialEstado.fecha_inicio.desc()).all()


def create_historial_estado(
    db: Session,
    historialEstado: schemas.HistorialCreate
):
    try:

        inmueble = get_inmueble_by_id(
            db,
            historialEstado.inmueble_id
        )

        if not inmueble:
            raise ValueError("Property not found")

        now = datetime.now(timezone.utc)

        # Buscar historial actual activo
        current_historial = (
            db.query(models.HistorialEstado)
            .filter(
                models.HistorialEstado.inmueble_id == historialEstado.inmueble_id,
                models.HistorialEstado.fecha_fin.is_(None)
            )
            .first()
        )

        # Cerrar historial anterior
        if current_historial:
            current_historial.fecha_fin = now

        # Crear nuevo historial
        db_historial_estado = models.HistorialEstado(
            inmueble_id=historialEstado.inmueble_id,
            estado=historialEstado.estado.value,
            fecha_inicio=now
        )

        db.add(db_historial_estado)

        db.commit()

        db.refresh(db_historial_estado)

        return db_historial_estado

    except OperationalError:

        db.rollback()

        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:

        db.rollback()

        raise Exception(
            "Database error, please try again later"
        )
    

def update_historial_estado(
    db: Session,
    historial_id: int,
    historial_update: schemas.HistorialUpdate
):
    try:

        db_historial = get_historial_estado_by_id(
            db,
            historial_id
        )

        if not db_historial:
            return None

        updates = historial_update.model_dump(
            exclude_none=True
        )

        for key, value in updates.items():

            if key == "estado":
                value = value.value

            setattr(db_historial, key, value)

        db.commit()
        db.refresh(db_historial)

        return db_historial

    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error"
        )
    

def get_current_historial_by_inmueble(
    db: Session,
    inmueble_id: int
):
    return (
        db.query(models.HistorialEstado)
        .filter(
            models.HistorialEstado.inmueble_id == inmueble_id,
            models.HistorialEstado.fecha_fin.is_(None)
        )
        .first()
    )



#--------------------------
#         imagen 
#--------------------------

def get_imagen_by_id(db: Session, imagen_id: int):
    return db.query(models.Imagen).filter(models.Imagen.id == imagen_id).first()

def get_imagenes_by_inmueble(db: Session, inmueble_id: int):
    return db.query(models.Imagen).filter(models.Imagen.inmueble_id == inmueble_id).order_by(models.Imagen.id.asc()).all()

def create_imagen(db: Session, imagen: schemas.ImagenCreate):
    try:    
        db_imagen = models.Imagen(
            url_archivo = imagen.url_archivo,
            texto_alternativo = imagen.texto_alternativo,
            inmueble_id = imagen.inmueble_id,

        )
        db.add(db_imagen)
        db.commit()
        db.refresh(db_imagen)
        return db_imagen
    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )
    

def update_imagen(
    db: Session,
    imagen_id: int,
    imagen_update: schemas.ImagenUpdate
):
    try:

        db_imagen = get_imagen_by_id(
            db,
            imagen_id
        )

        if not db_imagen:
            return None

        updates = imagen_update.model_dump(
            exclude_none=True
        )

        for key, value in updates.items():
            setattr(db_imagen, key, value)

        db.commit()
        db.refresh(db_imagen)

        return db_imagen

    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error"
        )
    

def delete_imagen(
    db: Session,
    imagen_id: int
):
    try:

        db_imagen = get_imagen_by_id(
            db,
            imagen_id
        )

        if not db_imagen:
            return None

        db.delete(db_imagen)

        db.commit()

        return True

    except OperationalError:

        db.rollback()

        raise ConnectionError(
            "Database connection error"
        )

    except SQLAlchemyError:

        db.rollback()

        raise Exception(
            "Database error"
        )
    

#--------------------------
#        contacto 
#--------------------------

def get_contacto_by_id(db: Session, contacto_id: int):
    return db.query(models.Contacto).filter(models.Contacto.id == contacto_id).first()

def get_contactos_by_inmueble(db: Session, id_inmueble: int):
    return db.query(models.Contacto).filter(models.Contacto.inmueble_id == id_inmueble).order_by(models.Contacto.fecha.desc()).all()

def create_contacto(db: Session, contacto: schemas.ContactoCreate):
    try:    
        db_contacto = models.Contacto(
            nombre = contacto.nombre,
            correo = contacto.correo,
            mensaje = contacto.mensaje,
            inmueble_id = contacto.inmueble_id

        )
        db.add(db_contacto)
        db.commit()
        db.refresh(db_contacto)
        return db_contacto
    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )
    

def update_contacto(
    db: Session,
    contacto_id: int,
    contacto_update: schemas.ContactoUpdate
):
    try:

        db_contacto = get_contacto_by_id(
            db,
            contacto_id
        )

        if not db_contacto:
            return None

        updates = contacto_update.model_dump(
            exclude_none=True
        )

        for key, value in updates.items():
            setattr(db_contacto, key, value)

        db.commit()
        db.refresh(db_contacto)

        return db_contacto

    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error"
        )
    
def get_all_contactos(db: Session, limit: int = 100, offset: int = 0):
    return (
    db.query(models.Contacto)
    .offset(offset)
    .limit(limit)
    .all()
)
