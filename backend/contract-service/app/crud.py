from __future__ import annotations

from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas

#  CONTRATOS

def crear_contrato(db: Session, datos: schemas.ContratoCreate) -> models.Contrato:
    contrato = models.Contrato(**datos.model_dump())
    db.add(contrato)
    db.commit()
    db.refresh(contrato)
    return contrato


def obtener_contrato(db: Session, contrato_id: int) -> models.Contrato | None:
    return db.query(models.Contrato).filter(
        models.Contrato.id == contrato_id
    ).first()


def obtener_contratos_por_usuario(
    db: Session, usuario_id: int, skip: int = 0, limit: int = 50
) -> list[models.Contrato]:
    return (
        db.query(models.Contrato)
        .filter(models.Contrato.usuario_id == usuario_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def obtener_contratos_por_inmueble(
    db: Session, inmueble_id: int, skip: int = 0, limit: int = 50
) -> list[models.Contrato]:
    return (
        db.query(models.Contrato)
        .filter(models.Contrato.inmueble_id == inmueble_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

#  PAGOS

def crear_pago(
    db: Session,
    contrato_id: int,
    datos: schemas.PagoCreate,
    stripe_session_id: str | None = None,
) -> models.Pago:
    pago = models.Pago(
        **datos.model_dump(),
        contrato_id=contrato_id,
        fecha=datetime.utcnow(),
        stripe_session_id=stripe_session_id,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago

#hook stripe verificacion
def actualizar_estado_pago(
    db: Session,
    stripe_session_id: str,
    nuevo_estado: str,
) -> models.Pago | None:
    pago = db.query(models.Pago).filter(
        models.Pago.stripe_session_id == stripe_session_id
    ).first()
    if pago:
        pago.estado = nuevo_estado
        db.commit()
        db.refresh(pago)
    return pago
