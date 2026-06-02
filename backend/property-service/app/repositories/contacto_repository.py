from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import or_

#--------------------------
#        contacto 
#--------------------------

def get_contacto_by_id(db: Session, contacto_id: int):
    return db.query(models.Contacto).filter(models.Contacto.id == contacto_id).first()

def get_contactos_by_inmueble(db: Session, inmueble_id: int):
    return db.query(models.Contacto).filter(models.Contacto.inmueble_id == inmueble_id).order_by(models.Contacto.fecha.desc()).all()

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
    

def delete_contacto(
    db: Session,
    contacto_id: int
):
    contacto = get_contacto_by_id(db, contacto_id)

    if not contacto:
        return False

    db.delete(contacto)
    db.commit()

    return True
    
def get_all_contactos(db: Session, limit: int = 100, offset: int = 0):
    safe_limit = min(limit, 1000)

    return (
    db.query(models.Contacto)
    .order_by(models.Contacto.fecha.desc())
    .offset(offset)
    .limit(safe_limit)
    .all()
)

def get_contactos_by_correo(
    db: Session,
    correo: str
):
    return (
        db.query(models.Contacto)
        .filter(models.Contacto.correo.ilike(f"%{correo}%"))
        .order_by(models.Contacto.fecha.desc())
        .all()
    )

def search_contactos(
    db: Session,
    query: str
):
    
    if not query.strip():
        return []

    return (
        db.query(models.Contacto)
        .filter(
            or_(
                models.Contacto.correo.ilike(f"%{query}%"),
                models.Contacto.nombre.ilike(f"%{query}%"),
                models.Contacto.mensaje.ilike(f"%{query}%")
            )
        )
        .order_by(models.Contacto.fecha.desc())
        .all()
    )
