import os
import stripe
from fastapi import FastAPI, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime

import models, schemas, gateway
from database import get_db

stripe.api_key   = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET", "")

app = FastAPI(
    title="Payment Service",
    description="Integración con Stripe para contratos de Venta y Renta",
    version="1.0.0",
)

# Iniciar pago  →  crea sesión Stripe

@app.post(
    "/api/pagos/iniciar",
    response_model=schemas.RespuestaSesion,
    status_code=status.HTTP_201_CREATED,
    summary="Inicia el flujo de pago y devuelve la URL de Stripe",
)
def iniciar_pago(payload: schemas.IniciarPago, db: Session = Depends(get_db)):

    #contrato existe
    contrato = db.query(models.Contrato).filter(
        models.Contrato.id == payload.contrato_id
    ).first()

    if not contrato:
        raise HTTPException(
            status_code=404,
            detail=f"No existe un contrato con id={payload.contrato_id}",
        )

    #contratos activos
    if contrato.estado != "activo":
        raise HTTPException(
            status_code=422,
            detail=f"El contrato está '{contrato.estado}' y no acepta pagos",
        )

    #  monto no supera la deuda pendiente (solo Venta)
    if contrato.tipo == "Venta":
        pagado = sum(
            p.monto for p in contrato.pagos if p.estado == "completado"
        )
        deuda = float(contrato.monto) - float(pagado)
        if float(payload.monto) > deuda + 0.01:   # margen de redondeo
            raise HTTPException(
                status_code=422,
                detail=(
                    f"El monto ${payload.monto} supera la deuda pendiente "
                    f"(${deuda:.2f}). Ajuste el importe."
                ),
            )

    # Crear sesión en Stripe (flujo diferenciado por tipo)
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

    # ── Registrar el Pago como 'pendiente' en la BD ───────────
    pago = models.Pago(
        monto=payload.monto,
        metodo="stripe",
        estado="pendiente",
        stripe_session_id=sesion.id,
        contrato_id=payload.contrato_id,
        fecha=datetime.utcnow(),
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)

    return schemas.RespuestaSesion(
        checkout_url=sesion.url,
        stripe_session_id=sesion.id,
        tipo_contrato=contrato.tipo,
        pago_id=pago.id,
    )


# Webhook de Stripe  →  confirmar / rechazar pago

@app.post(
    "/api/pagos/webhook",
    status_code=status.HTTP_200_OK,
    summary="Endpoint que Stripe llama para notificar resultados",
)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload    = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    # Verificar firma para garantizar que viene de Stripe
    try:
        evento = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma Stripe inválida")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # checkout.session.completed  pago exitoso
    if evento["type"] == "checkout.session.completed":
        sesion       = evento["data"]["object"]
        session_id   = sesion["id"]
        contrato_id  = int(sesion["metadata"].get("contrato_id", 0))
        tipo         = sesion["metadata"].get("tipo_contrato", "")

        pago = db.query(models.Pago).filter(
            models.Pago.stripe_session_id == session_id
        ).first()

        if pago:
            pago.estado = "completado"
            db.commit()

            if tipo == "Venta":
                contrato = db.query(models.Contrato).filter(
                    models.Contrato.id == contrato_id
                ).first()
                if contrato:
                    total_pagado = sum(
                        float(p.monto)
                        for p in contrato.pagos
                        if p.estado == "completado"
                    )
                    if total_pagado >= float(contrato.monto):
                        contrato.estado = "finalizado"
                        db.commit()

    # checkout.session.expired → pago caducado
    elif evento["type"] == "checkout.session.expired":
        sesion     = evento["data"]["object"]
        session_id = sesion["id"]

        pago = db.query(models.Pago).filter(
            models.Pago.stripe_session_id == session_id
        ).first()
        if pago:
            pago.estado = "fallido"
            db.commit()

    return {"status": "ok"}

#   Consultar estado de un pago

@app.get(
    "/api/pagos/{pago_id}",
    response_model=schemas.EstadoPago,
    summary="Consultar el estado actual de un pago",
)
def obtener_estado_pago(pago_id: int, db: Session = Depends(get_db)):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return schemas.EstadoPago(
        pago_id=pago.id,
        estado=pago.estado,
        contrato_id=pago.contrato_id,
    )
