from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import or_


#--------------------------
#       ubicacion 
#--------------------------

def get_ubicacion_by_id(db: Session, ubicacion_id: int):
    return (
        db.query(models.Ubicacion)
        .filter(models.Ubicacion.id == ubicacion_id)
        .options(
            joinedload(models.Ubicacion.estado_republica)
        )
        .first()
    )


def create_ubicacion(db: Session, ubicacion: schemas.UbicacionCreate):
    try:  

        estado = get_estado_republica_by_id(
            db,
            ubicacion.estado_id
        )

        if not estado:
            raise ValueError("State not found")

        db_ubicacion = models.Ubicacion(
            latitud = ubicacion.latitud,
            longitud = ubicacion.longitud,
            estado_id=ubicacion.estado_id,
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
        
        if ubicacion_update.estado_id is not None:
            estado = get_estado_republica_by_id(
                db,
                ubicacion_update.estado_id
            )

            if not estado:
                raise ValueError("State not found")

        updates = ubicacion_update.model_dump(
            exclude_none=True
        )

        for key, value in updates.items():
            setattr(db_ubicacion, key, value)

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
    

def search_ubicaciones(
    db: Session,
    query: str
):

    if not query.strip():
        return []

    return (
        db.query(models.Ubicacion)
        .join(models.EstadoRepublica)
        .filter(
            or_(
                models.Ubicacion.calle.ilike(f"%{query}%"),
                models.Ubicacion.ciudad.ilike(f"%{query}%"),
                models.Ubicacion.codigo_postal.ilike(f"%{query}%"),
                models.Ubicacion.colonia.ilike(f"%{query}%"),
                models.Ubicacion.numero_exterior.ilike(f"%{query}%"),
                models.Ubicacion.numero_interior.ilike(f"%{query}%"),
                models.EstadoRepublica.valor.ilike(f"%{query}%")
            )
        )
        .options(
            joinedload(models.Ubicacion.estado_republica)
        )
        .all()
    )


#--------------------------
#       Estado Republica 
#--------------------------

def get_all_estado_republica(db: Session):
    return( 
        db.query(models.EstadoRepublica).
        all()       
    )

def get_estado_republica_by_id(db: Session, estado_id: int):
    return( 
        db.query(models.EstadoRepublica).
        filter(models.EstadoRepublica.id == estado_id).
        first()      
    )

def get_estado_republica_by_valor(
    db: Session,
    valor: str
):
    return (
        db.query(models.EstadoRepublica)
        .filter(models.EstadoRepublica.valor.ilike(valor))
        .first()
    )