import os
import stripe
from sqlalchemy.orm import Session
import models, schemas

# Llave secreta de Stripe (Debe ir en el entorno, aquí con un valor por defecto para pruebas)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_tu_llave_secreta_aqui")


class ContratoService:
    @staticmethod
    def crear_contrato(db: Session, contrato_in: schemas.ContratoCreate):
        db_contrato = models.Contrato(**contrato_in.model_dump())
        db.add(db_contrato)
        db.commit()
        db.refresh(db_contrato)
        return db_contrato

    @staticmethod
    def obtener_por_id(db: Session, contrato_id: int):
        return db.query(models.Contrato).filter(models.Contrato.id == contrato_id).first()

    @staticmethod
    def obtener_por_usuario(db: Session, usuario_id: int):
        return db.query(models.Contrato).filter(models.Contrato.usuario_id == usuario_id).all()

    @staticmethod
    def obtener_por_inmueble(db: Session, inmueble_id: int):
        return db.query(models.Contrato).filter(models.Contrato.inmueble_id == inmueble_id).all()


class PagoService:
    @staticmethod
    def crear_intento_stripe(monto: float, moneda: str, contrato_id: int):
        # Stripe maneja los montos en centavos
        intent = stripe.PaymentIntent.create(
            amount=int(monto * 100),
            currency=moneda,
            metadata={"contrato_id": contrato_id}
        )
        return intent.client_secret

    @staticmethod
    def registrar_pago(db: Session, pago_in: schemas.PagoCreate):
        # Regla de Negocio: Validar que el contrato exista
        contrato = db.query(models.Contrato).filter(models.Contrato.id == pago_in.contrato_id).first()
        if not contrato:
            return None

        db_pago = models.Pago(
            monto=pago_in.monto,
            metodo=pago_in.metodo,
            contrato_id=pago_in.contrato_id,
            estado="completado" if pago_in.metodo.lower() == "stripe" else "pendiente"
        )
        db.add(db_pago)
        db.commit()
        db.refresh(db_pago)
        return db_pago