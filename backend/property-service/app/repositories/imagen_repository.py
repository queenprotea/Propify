from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import or_

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
            inmueble_id = imagen.inmueble_id,
            descripcion = imagen.descripcion
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
    
