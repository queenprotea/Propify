"""Lógica de negocio de pagos vía Stripe (inicio de sesión y webhook)."""
import os

from fastapi import HTTPException
import stripe

import schemas
import gateway
from repositories import pago_repository

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def iniciar_pago(db, payload: schemas.IniciarPago) -> schemas.RespuestaSesion:
    contrato = pago_repository.obtener_contrato(db, payload.contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail=f"No existe un contrato con id={payload.contrato_id}")

    if contrato.estado != "activo":
        raise HTTPException(status_code=422, detail=f"El contrato está '{contrato.estado}' y no acepta pagos")

    # En venta el monto no puede superar la deuda pendiente.
    if contrato.tipo == "Venta":
        pagado = sum(p.monto for p in contrato.pagos if p.estado == "completado")
        deuda = float(contrato.monto) - float(pagado)
        if float(payload.monto) > deuda + 0.01:
            raise HTTPException(status_code=422,
                detail=(f"El monto ${payload.monto} supera la deuda pendiente "
                        f"(${deuda:.2f}). Ajuste el importe."))

    try:
        sesion = gateway.crear_sesion(
            tipo_contrato=contrato.tipo,
            monto=float(payload.monto),
            contrato_id=payload.contrato_id,
            moneda=payload.moneda,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error en Stripe: {str(e)}")

    pago = pago_repository.crear_pago(db, payload.monto, payload.contrato_id, sesion.id)

    return schemas.RespuestaSesion(
        checkout_url=sesion.url,
        stripe_session_id=sesion.id,
        tipo_contrato=contrato.tipo,
        pago_id=pago.id,
    )


def procesar_webhook(db, payload: bytes, sig_header: str) -> dict:
    try:
        evento = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma Stripe inválida")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if evento["type"] == "checkout.session.completed":
        _pago_completado(db, evento["data"]["object"])
    elif evento["type"] == "checkout.session.expired":
        _pago_expirado(db, evento["data"]["object"])

    return {"status": "ok"}


def _pago_completado(db, sesion) -> None:
    pago = pago_repository.obtener_pago_por_sesion(db, sesion["id"])
    if not pago:
        return
    pago_repository.actualizar_estado_pago(db, pago, "completado")

    if sesion["metadata"].get("tipo_contrato", "") == "Venta":
        contrato_id = int(sesion["metadata"].get("contrato_id", 0))
        contrato = pago_repository.obtener_contrato(db, contrato_id)
        if contrato:
            total_pagado = sum(float(p.monto) for p in contrato.pagos if p.estado == "completado")
            if total_pagado >= float(contrato.monto):
                pago_repository.actualizar_estado_contrato(db, contrato, "finalizado")


def _pago_expirado(db, sesion) -> None:
    pago = pago_repository.obtener_pago_por_sesion(db, sesion["id"])
    if pago:
        pago_repository.actualizar_estado_pago(db, pago, "fallido")


def estado_pago(db, pago_id: int) -> schemas.EstadoPago:
    pago = pago_repository.obtener_pago(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return schemas.EstadoPago(pago_id=pago.id, estado=pago.estado, contrato_id=pago.contrato_id)
