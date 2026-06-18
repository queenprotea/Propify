# Lógica de negocio de pagos (efectivo, transferencia y tarjeta)
from pathlib import Path
import os

from fastapi import HTTPException, status
import stripe

import crud
import models
import schemas
import property_client
import storage
from security import require_owner_or_admin, system_token

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

STRIPE_MIN_MXN = 10.0


def exigir_contrato_pagable(contrato):
    if not contrato.url_firmado:
        raise HTTPException(status_code=409,
            detail="No se puede pagar: el contrato aún no ha sido firmado por las partes.")
    if contrato.estado_documento != "aprobado":
        raise HTTPException(status_code=409,
            detail="No se puede pagar: la documentación firmada aún no ha sido validada por el administrador.")


def _contrato_o_404(db, contrato_id):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato


def _marcar_vendido_si_liquidado(db, contrato, propagar_error: bool):
    if contrato.tipo == "Venta" and crud.resumen_contrato(contrato).liquidado:
        try:
            property_client.set_estado_inmueble(contrato.inmueble_id, "vendido", system_token())
        except Exception as e:
            if propagar_error:
                raise HTTPException(status_code=502,
                    detail=f"Pago aprobado pero no se pudo marcar el inmueble como vendido: {e}")


def listar_pagos(db, contrato_id, user):
    contrato = _contrato_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    return contrato.pagos


def registrar_efectivo(db, contrato_id, datos, user, ip):
    contrato = _contrato_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    exigir_contrato_pagable(contrato)
    if datos.metodo == schemas.MetodoPago.transferencia:
        raise HTTPException(status_code=422,
            detail="La transferencia requiere adjuntar comprobante; usa el registro con comprobante.")
    try:
        return crud.registrar_pago(db, contrato, datos, usuario_id=int(user["sub"]), ip=ip, confirmado=False)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


async def registrar_transferencia(db, contrato_id, monto, numero_cuota, file, user, ip):
    contrato = _contrato_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    exigir_contrato_pagable(contrato)

    if file.content_type not in ("application/pdf", "image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="El comprobante debe ser PDF o imagen")
    contenido = await file.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El comprobante supera 10 MB")

    uid = int(user["sub"])
    try:
        pago = crud.registrar_pago(
            db, contrato,
            schemas.PagoCreate(monto=monto, metodo=schemas.MetodoPago.transferencia, numero_cuota=numero_cuota),
            usuario_id=uid, ip=ip, confirmado=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    ext = ".pdf" if file.content_type == "application/pdf" else Path(file.filename or "").suffix or ".bin"
    ruta = storage.guardar_comprobante(contrato_id, contenido, ext)
    crud.crear_comprobante(db, contrato_id, uid, str(ruta), pago_id=pago.id)
    return pago


def verificar_pago(db, pago_id, datos):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    contrato = crud.obtener_contrato(db, pago.contrato_id)
    if not datos.aprobado and not (datos.motivo or "").strip():
        raise HTTPException(status_code=422, detail="Indica el motivo del rechazo")
    try:
        pago = crud.verificar_pago(db, pago, datos.aprobado, datos.motivo)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if datos.aprobado:
        _marcar_vendido_si_liquidado(db, contrato, propagar_error=True)
    return pago


def pagar_stripe(db, contrato_id, datos, user, ip):
    contrato = _contrato_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    exigir_contrato_pagable(contrato)
    uid = int(user["sub"])

    if float(datos.monto) < STRIPE_MIN_MXN:
        raise HTTPException(status_code=422,
            detail=f"El pago con tarjeta requiere al menos ${STRIPE_MIN_MXN:.2f} MXN. "
                   f"Para montos menores usa efectivo o transferencia.")

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(round(float(datos.monto) * 100)),
            currency="mxn",
            payment_method=datos.payment_method,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={"contrato_id": str(contrato_id), "usuario_id": str(uid)},
        )
    except stripe.error.CardError as e:
        raise HTTPException(status_code=402, detail=f"Tarjeta rechazada: {e.user_message or 'verifica los datos'}")
    except stripe.error.InvalidRequestError as e:
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=422, detail=f"No se pudo procesar el pago con tarjeta: {msg}")
    except stripe.error.StripeError as e:
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=502, detail=f"No se pudo procesar el pago con Stripe: {msg}")

    if intent.status != "succeeded":
        raise HTTPException(status_code=402, detail=f"El pago no se completó (estado: {intent.status}).")

    try:
        pago = crud._registrar_pago_confirmado_stripe(db, contrato, datos.monto, uid, ip, intent.id, datos.numero_cuota)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    _marcar_vendido_si_liquidado(db, contrato, propagar_error=False)
    return pago


def listar_comprobantes(db, contrato_id, user):
    contrato = _contrato_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    return crud.comprobantes_por_contrato(db, contrato_id)


def comprobante_descargable(db, comprobante_id, user):
    comp = crud.obtener_comprobante(db, comprobante_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    contrato = crud.obtener_contrato(db, comp.contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    if not Path(comp.url_archivo).exists():
        raise HTTPException(status_code=404, detail="Archivo no disponible")
    return comp
