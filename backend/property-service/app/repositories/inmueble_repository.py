from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import or_

INMUEBLE_RELATIONS = [
    joinedload(models.Inmueble.estado_inmueble),
    joinedload(models.Inmueble.tipo_inmueble),
    joinedload(models.Inmueble.ubicacion),
    joinedload(models.Inmueble.imagenes)
]

PUBLIC_STATES = ["en venta", "en renta", "reservado"]

def get_inmueble_by_id(db: Session, inmueble_id: int):
    return (
        db.query(models.Inmueble)
        .filter(models.Inmueble.id == inmueble_id)
        .options(*INMUEBLE_RELATIONS)
        .first()
    )

def create_inmueble(db: Session, inmueble: schemas.InmuebleCreate):
    try:
        db_inmueble = models.Inmueble(
            titulo=inmueble.titulo,
            descripcion = inmueble.descripcion,
            precio = inmueble.precio,
            tipo_id=inmueble.tipo_id,
            estado_id=inmueble.estado_id,
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

        if inmueble_update.tipo_id is not None:
            db_inmueble.tipo_id = inmueble_update.tipo_id

        if inmueble_update.estado_id is not None:
            db_inmueble.estado_id = inmueble_update.estado_id

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

        if inmueble_update.propietario_id is not None:
            db_inmueble.propietario_id = inmueble_update.propietario_id
    

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
    new_status_id: int
):
    try:

        property_db = (
            db.query(models.Inmueble)
            .filter(models.Inmueble.id == inmueble_id)
            .first()
        )

        if not property_db:
            return None

        property_db.estado_id = new_status_id

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
    

def update_inmueble_propietario(
    db: Session,
    inmueble_id: int,
    new_propietario_id: int
):
    try:

        property_db = (
            db.query(models.Inmueble)
            .filter(models.Inmueble.id == inmueble_id)
            .first()
        )

        if not property_db:
            return None

        property_db.propietario_id = new_propietario_id

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


def clear_propietario_inmueble(
    db: Session,
    inmueble_id: int,
):
    try:

        property_db = (
            db.query(models.Inmueble)
            .filter(models.Inmueble.id == inmueble_id)
            .first()
        )

        if not property_db:
            return None

        property_db.propietario_id = None

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


def get_disponible_inmuebles(db: Session):
    return (
        db.query(models.Inmueble)
        .join(models.EstadoInmueble)
        .filter(
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()
    )

def get_inmuebles_by_tipo_admin(
    db: Session,
    tipo_id: int
):
    return (
        db.query(models.Inmueble)
        .filter(
            models.Inmueble.tipo_id == tipo_id
        )
        .options(*INMUEBLE_RELATIONS)
        .all()
    )

def get_inmuebles_by_tipo(
    db: Session,
    tipo_id: int
):
    return (
        db.query(models.Inmueble)
        .join(models.EstadoInmueble)
        .filter(
            models.Inmueble.tipo_id == tipo_id,
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()
    )


# para admin o para que el cliente consulte sus propios inmuebles
def get_inmuebles_by_propietario(db: Session, pro_id: int):
    return(
        db.query(models.Inmueble)
        .filter(models.Inmueble.propietario_id == pro_id)
        .options(*INMUEBLE_RELATIONS)
        .all()
    )

def get_inmuebles_by_titulo_admin(db: Session, titulo: str):
    return( 
        db.query(models.Inmueble)
        .filter(
            models.Inmueble.titulo.ilike(f"%{titulo}%"),
        )
        .options(*INMUEBLE_RELATIONS)
        .all()
    )

def get_inmuebles_by_titulo(db: Session, titulo: str):
    return( 
        db.query(models.Inmueble)
        .join(models.EstadoInmueble)
        .filter(
            models.Inmueble.titulo.ilike(f"%{titulo}%"),
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()
    )

def get_inmuebles_by_descripcion_admin(db: Session, des: str):
    return(
        db.query(models.Inmueble)
        .filter(models.Inmueble.descripcion.ilike(f"%{des}%"))
        .options(*INMUEBLE_RELATIONS)
        .all()
    )

def get_inmuebles_by_descripcion(db: Session, des: str):
    return(
        db.query(models.Inmueble)
        .join(models.EstadoInmueble)
        .filter(
            models.Inmueble.descripcion.ilike(f"%{des}%"),
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()
    )

def get_inmuebles_by_estado(db: Session, sta: int):
    return ( 
        db.query(models.Inmueble)
        .filter(models.Inmueble.estado_id == sta)
        .options(*INMUEBLE_RELATIONS)
        .all()
    )


# exclusivo admin
def get_all_inmuebles(db: Session, limit: int = 100, offset: int = 0):
    safe_limit = min(limit, 1000)

    return (
        db.query(models.Inmueble)
        .options(*INMUEBLE_RELATIONS)
        .offset(offset)
        .limit(safe_limit)
        
        .all()
    )


#bucar desde valores de inmueble, su ubicacion, tipo y estado
def search_inmuebles_admin(db: Session, query: str):

    if not query.strip():
        return []

    return (
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .join(models.TipoInmueble)
        .join(models.EstadoInmueble)
        .filter(
            or_(
                models.Inmueble.descripcion.ilike(f"%{query}%"),
                models.Inmueble.titulo.ilike(f"%{query}%"),
                models.Ubicacion.ciudad.ilike(f"%{query}%"),
                models.Ubicacion.colonia.ilike(f"%{query}%"),
                models.Ubicacion.calle.ilike(f"%{query}%"),
                models.TipoInmueble.valor.ilike(f"%{query}%"),
                models.EstadoInmueble.valor.ilike(f"%{query}%"),
            )
        )
        .options(*INMUEBLE_RELATIONS)
        .distinct()
        .all()
    )

def search_inmuebles(db: Session, query: str):

    if not query.strip():
        return []

    return (
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .join(models.TipoInmueble)
        .join(models.EstadoInmueble)
        .filter(
            or_(
                models.Inmueble.descripcion.ilike(f"%{query}%"),
                models.Inmueble.titulo.ilike(f"%{query}%"),
                models.Ubicacion.ciudad.ilike(f"%{query}%"),
                models.Ubicacion.colonia.ilike(f"%{query}%"),
                models.Ubicacion.calle.ilike(f"%{query}%"),
                models.TipoInmueble.valor.ilike(f"%{query}%"),
                models.EstadoInmueble.valor.ilike(f"%{query}%"),
            ),

            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .distinct()
        .all()
    )

def get_inmuebles_by_estado_republica_admin(db: Session, estado_id: int):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .filter(models.Ubicacion.estado_id == estado_id)
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_estado_republica(db: Session, estado_id: int):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .join(models.EstadoInmueble)
        .filter(
            models.Ubicacion.estado_id == estado_id,
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_ciudad_admin(db: Session, ciudad: str):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .filter(models.Ubicacion.ciudad.ilike(f"%{ciudad}%"))
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_ciudad(db: Session, ciudad: str):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .join(models.EstadoInmueble)
        .filter(
            models.Ubicacion.ciudad.ilike(f"%{ciudad}%"),
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_colonia_admin(db: Session, colonia: str):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .filter(models.Ubicacion.colonia.ilike(f"%{colonia}%"))
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_colonia(db: Session, colonia: str):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .join(models.EstadoInmueble)
        .filter(
            models.Ubicacion.colonia.ilike(f"%{colonia}%"),
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_calle_admin(db: Session, calle: str):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .filter(models.Ubicacion.calle.ilike(f"%{calle}%"))
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_calle(db: Session, calle: str):
    return( 
        db.query(models.Inmueble)
        .join(models.Ubicacion)
        .join(models.EstadoInmueble)
        .filter(
            models.Ubicacion.calle.ilike(f"%{calle}%"),
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .all()       
    )

def get_inmuebles_by_precio_admin(db: Session, precio: Decimal):
    return( 
        db.query(models.Inmueble)
        .filter(models.Inmueble.precio <= precio)
        .options(*INMUEBLE_RELATIONS)
        .order_by(models.Inmueble.precio.asc())    
        .all()
    )

def get_inmuebles_by_precio(db: Session, precio: Decimal):
    return( 
        db.query(models.Inmueble)
        .join(models.EstadoInmueble)
        .filter(
            models.Inmueble.precio <= precio,
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .order_by(models.Inmueble.precio.asc())    
        .all()
    )


def get_inmuebles_by_num_recamaras_admin(db: Session, num: int):
    return( 
        db.query(models.Inmueble)
        .filter(models.Inmueble.num_recamaras >= num)
        .options(*INMUEBLE_RELATIONS)
        .order_by(models.Inmueble.num_recamaras.asc())
        .all()  

    )

def get_inmuebles_by_num_recamaras(db: Session, num: int):
    return( 
        db.query(models.Inmueble)
        .join(models.EstadoInmueble)
        .filter(
            models.Inmueble.num_recamaras >= num,
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .order_by(models.Inmueble.num_recamaras.asc())
        .all()  

    )

def get_inmuebles_by_num_banos_admin(db: Session, num: int):
    return( 
        db.query(models.Inmueble)
        .filter(models.Inmueble.num_banos >= num)
        .options(*INMUEBLE_RELATIONS)
        .order_by(models.Inmueble.num_banos.asc())
        .all()       
    )

def get_inmuebles_by_num_banos(db: Session, num: int):
    return( 
        db.query(models.Inmueble)
        .join(models.EstadoInmueble)
        .filter(
            models.Inmueble.num_banos >= num,
            models.EstadoInmueble.valor.in_(PUBLIC_STATES)
        )
        .options(*INMUEBLE_RELATIONS)
        .order_by(models.Inmueble.num_banos.asc())
        .all()       
    )


#--------------------------
#       Estado inmueble 
#--------------------------

def get_all_estado_inmueble(db: Session):
    return( 
        db.query(models.EstadoInmueble).
        all()       
    )

def get_estado_inmueble_by_id(db: Session, estado_id: int):
    return( 
        db.query(models.EstadoInmueble).
        filter(models.EstadoInmueble.id == estado_id).
        first()      
    )

def get_estado_inmueble_by_valor(
    db: Session,
    valor: str
):
    return (
        db.query(models.EstadoInmueble)
        .filter(models.EstadoInmueble.valor.ilike(valor))
        .first()
    )

#--------------------------
#       Tipo inmueble 
#--------------------------

def get_all_tipo_inmueble(db: Session):
    return( 
        db.query(models.TipoInmueble).
        all()       
    )

def get_tipo_inmueble_by_id(db: Session, tipo_id: int):
    return( 
        db.query(models.TipoInmueble).
        filter(models.TipoInmueble.id == tipo_id).
        first()      
    )

def get_tipo_inmueble_by_valor(
    db: Session,
    valor: str
):
    return (
        db.query(models.TipoInmueble)
        .filter(models.TipoInmueble.valor.ilike(valor))
        .first()
    )


