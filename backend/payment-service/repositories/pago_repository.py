# Acceso a datos del payment-service (pagos y contratos)
from datetime import datetime

from sqlalchemy.orm import Session

import models


def obtener_contrato(db: Session, contrato_id: int):
    return db.query(models.Contrato).filter(models.Contrato.id == contrato_id).first()


def obtener_pago(db: Session, pago_id: int):
    return db.query(models.Pago).filter(models.Pago.id == pago_id).first()


def obtener_pago_por_sesion(db: Session, session_id: str):
    return db.query(models.Pago).filter(models.Pago.stripe_session_id == session_id).first()


def crear_pago(db: Session, monto, contrato_id: int, stripe_session_id: str):
    pago = models.Pago(
        monto=monto,
        metodo="stripe",
        estado="pendiente",
        stripe_session_id=stripe_session_id,
        contrato_id=contrato_id,
        fecha=datetime.utcnow(),
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago


def actualizar_estado_pago(db: Session, pago, estado: str):
    pago.estado = estado
    db.commit()
    return pago


def actualizar_estado_contrato(db: Session, contrato, estado: str):
    contrato.estado = estado
    db.commit()
    return contrato
