from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import or_
from app.repositories.inmueble_repository import get_inmueble_by_id, get_estado_inmueble_by_id

#--------------------------
#     historialEstado 
#--------------------------



def get_historial_estado_by_id(db: Session, historialEstado_id: int):
    return(
        db.query(models.HistorialEstado)
        .filter(models.HistorialEstado.id == historialEstado_id)
        .options(
            joinedload(models.HistorialEstado.estado_inmueble),
            joinedload(models.HistorialEstado.inmueble),
        )
        .first()
    )

def get_historial_estado_by_inmueble(db: Session, inmueble_id: int):
    return(
        db.query(models.HistorialEstado)
        .filter(models.HistorialEstado.inmueble_id  == inmueble_id)
        .options(
            joinedload(models.HistorialEstado.estado_inmueble),
            joinedload(models.HistorialEstado.inmueble),
        )
        .order_by(models.HistorialEstado.fecha_inicio.desc())
        .all()
    )

def create_historial_estado(
    db: Session,
    historialEstado: schemas.HistorialCreate
):
    try:

        estado = get_estado_inmueble_by_id(
            db,
            historialEstado.estado_id
        )

        if not estado:
            raise ValueError("State not found")

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
            id_inmueble=historialEstado.inmueble_id,
            estado_id=historialEstado.estado_id,
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
        .options(
            joinedload(models.HistorialEstado.estado_inmueble),
            joinedload(models.HistorialEstado.inmueble),
        )
        .order_by(models.HistorialEstado.fecha_inicio.desc())
        .first()
    )



#--------------------------
#   historialPropietario 
#--------------------------

def get_historial_propietario_by_id(db: Session, historialPropietario_id: int):
    return (
        db.query(models.HistorialPropietario)
        .filter(models.HistorialPropietario.id == historialPropietario_id)
        .options(
            joinedload(models.HistorialEstado.inmueble),
        )
        .first()
    )

def get_historial_propietario_by_inmueble(db: Session, inmueble_id: int):
    return (
        db.query(models.HistorialPropietario)
        .filter(models.HistorialPropietario.inmueble_id == inmueble_id)
        .options(
            joinedload(models.HistorialEstado.inmueble),
        )
        .order_by(models.HistorialPropietario.fecha_inicio.desc())
        .all()
    )

def create_historial_propietario(
    db: Session,
    historialPropietario: schemas.HistorialPropietarioCreate
):
    try:

        inmueble = get_inmueble_by_id(
            db,
            historialPropietario.inmueble_id
        )

        if not inmueble:
            raise ValueError("Property not found")

        now = datetime.now(timezone.utc)

        # Buscar historial actual activo
        current_historial = (
            db.query(models.HistorialPropietario)
            .filter(
                models.HistorialPropietario.inmueble_id == historialPropietario.inmueble_id,
                models.HistorialPropietario.fecha_fin.is_(None)
            )
            .first()
        )

        # Cerrar historial anterior
        if current_historial:
            current_historial.fecha_fin = now

        # Crear nuevo historial
        db_historial_propietario = models.HistorialPropietario(
            inmueble_id=historialPropietario.inmueble_id,
            propietario_id=historialPropietario.propietario_id,
            fecha_inicio=now
        )

        db.add(db_historial_propietario)

        db.commit()

        db.refresh(db_historial_propietario)

        return db_historial_propietario

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
    

def update_historial_propietario(
    db: Session,
    historial_id: int,
    historial_update: schemas.HistorialPropietarioUpdate
):
    try:

        db_historial = get_historial_propietario_by_id(
            db,
            historial_id
        )

        if not db_historial:
            return None

        updates = historial_update.model_dump(
            exclude_none=True
        )

        for key, value in updates.items():

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
    

#para cuando el inmueble cambie a un estado donde no tenga propietario (en renta, en venta, no disponible)
def close_current_propietario(
    db: Session,
    inmueble_id: int,
):
    try:

        db_historial = get_current_propietario_by_inmueble(
            db,
            inmueble_id
        )

        if not db_historial:
            return None
        
        #en caso de que ya estuviera cerrado el historial propietario
        if db_historial.fecha_fin is not None:
            return None

        now = datetime.now(timezone.utc)

        db_historial.fecha_fin = now

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
    

def get_current_propietario_by_inmueble(
    db: Session,
    inmueble_id: int
):
    return (
        db.query(models.HistorialPropietario)
        .filter(
            models.HistorialPropietario.inmueble_id == inmueble_id,
            models.HistorialPropietario.fecha_fin.is_(None)
        )
        .options(
            joinedload(models.HistorialEstado.inmueble),
        )
        .first()
    )

