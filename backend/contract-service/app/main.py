from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import Response, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from datetime import date, timedelta
import os
import uuid
import stripe

import models, schemas, crud, pdf, property_client, user_client
from database import get_db
from security import get_current_user, get_current_admin, require_owner_or_admin, system_token

# Las tablas las crea db/init.sql; no se usa create_all aquí porque los modelos
# referencian tablas (Usuario, Inmueble) que pertenecen a otros servicios.

app = FastAPI(
    title="Contract Service",
    description="Gestión de contratos digitales (Venta/Renta) y sus pagos",
    version="2.0.0",
)

CONTRACTS_DIR = Path("/app/contracts")
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Monto mínimo por cargo con tarjeta que exige Stripe en MXN.
STRIPE_MIN_MXN = 10.0


@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado. Inténtalo de nuevo más tarde."},
    )


def _generar_y_guardar_pdf(db: Session, contrato, auth_header: str = ""):
    """Genera el PDF (completo, según operación) con datos reales y guarda su ruta."""
    # Datos reales para el contrato (degradación elegante si algún servicio falla).
    try:
        inmueble = property_client.get_inmueble(contrato.inmueble_id)
    except Exception:
        inmueble = None
    ubicacion = property_client.get_ubicacion(inmueble.get("ubicacion_id")) if inmueble else None
    cliente = user_client.get_usuario(contrato.usuario_id, auth_header)

    pdf_bytes = pdf.generar_pdf_contrato(
        contrato, cliente=cliente, inmueble=inmueble, ubicacion=ubicacion, pagos=list(contrato.pagos),
    )
    ruta = CONTRACTS_DIR / f"contrato_{contrato.id}_original.pdf"
    ruta.write_bytes(pdf_bytes)
    contrato.url_archivo = str(ruta)
    db.commit()
    db.refresh(contrato)
    return contrato


def _exigir_contrato_pagable(contrato):
    """Solo se aceptan pagos cuando el contrato está firmado y validado por el admin."""
    if not contrato.url_firmado:
        raise HTTPException(
            status_code=409,
            detail="No se puede pagar: el contrato aún no ha sido firmado por las partes.",
        )
    if contrato.estado_documento != "aprobado":
        raise HTTPException(
            status_code=409,
            detail="No se puede pagar: la documentación firmada aún no ha sido validada por el administrador.",
        )


# ─────────────────────────  CONTRATOS  ─────────────────────────

@app.post("/contratos", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Generar un contrato digital (solo administrador)")
def crear_contrato(
    datos: schemas.ContratoCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    contrato = crud.crear_contrato(db, datos)
    try:
        _generar_y_guardar_pdf(db, contrato, request.headers.get("Authorization", ""))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el PDF: {e}")
    return contrato


@app.get("/contratos/{contrato_id}", response_model=schemas.ContratoResponse)
def obtener_contrato(contrato_id: int, db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    return contrato


@app.get("/contratos/usuario/{usuario_id}", response_model=List[schemas.ContratoResponse])
def contratos_por_usuario(usuario_id: int, skip: int = 0, limit: int = 50,
                          db: Session = Depends(get_db), user=Depends(get_current_user)):
    require_owner_or_admin(user, usuario_id)
    return crud.obtener_contratos_por_usuario(db, usuario_id, skip, limit)


@app.get("/contratos/inmueble/{inmueble_id}", response_model=List[schemas.ContratoResponse])
def contratos_por_inmueble(inmueble_id: int, skip: int = 0, limit: int = 50,
                           db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return crud.obtener_contratos_por_inmueble(db, inmueble_id, skip, limit)


@app.get("/contratos", response_model=List[schemas.ContratoResponse],
         summary="Listar TODOS los contratos con filtros (administrador)")
def listar_contratos(
    estado: str | None = None, tipo: str | None = None, folio: str | None = None,
    usuario_id: int | None = None, inmueble_id: int | None = None,
    fecha_desde: str | None = None, fecha_hasta: str | None = None,
    skip: int = 0, limit: int = 200,
    db: Session = Depends(get_db), admin=Depends(get_current_admin),
):
    return crud.listar_contratos(db, estado=estado, tipo=tipo, folio=folio, usuario_id=usuario_id,
                                 inmueble_id=inmueble_id, fecha_desde=fecha_desde,
                                 fecha_hasta=fecha_hasta, skip=skip, limit=limit)


# ─────────────────────────  PDF: original / firmado  ─────────────────────────

@app.get("/contratos/{contrato_id}/pdf", summary="Descargar el contrato original (PDF)")
def descargar_pdf(contrato_id: int, request: Request, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)

    # Si por alguna razón no existe el archivo, se regenera al vuelo (con datos reales).
    ruta = Path(contrato.url_archivo) if contrato.url_archivo else None
    if ruta and ruta.exists():
        pdf_bytes = ruta.read_bytes()
    else:
        _generar_y_guardar_pdf(db, contrato, request.headers.get("Authorization", ""))
        pdf_bytes = Path(contrato.url_archivo).read_bytes()

    crud.registrar_descarga(db, contrato)   # trazabilidad de descarga
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="contrato_{contrato.id}.pdf"'},
    )


@app.post("/contratos/{contrato_id}/firmado", response_model=schemas.ContratoResponse,
          summary="Subir el contrato FIRMADO (cliente o administrador)")
async def subir_firmado(contrato_id: int, file: UploadFile = File(...),
                        db: Session = Depends(get_db), user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)

    # Una vez APROBADA la documentación por el administrador, ya no puede reemplazarse.
    if contrato.estado_documento == "aprobado":
        raise HTTPException(status_code=409,
            detail="El documento firmado ya fue aprobado; no puede reemplazarse.")
    # Tampoco si el contrato está cerrado. Si fue rechazado o está pendiente, sí se permite.
    if contrato.estado in ("cancelado", "finalizado", "liquidado"):
        raise HTTPException(status_code=409,
            detail=f"El contrato está {contrato.estado}; no se puede reemplazar el documento firmado.")

    if file.content_type not in ("application/pdf", "image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="Solo se admite PDF o imagen del contrato firmado")

    contenido = await file.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo supera 10 MB")

    ext = ".pdf" if file.content_type == "application/pdf" else Path(file.filename or "").suffix or ".bin"
    ruta = CONTRACTS_DIR / f"contrato_{contrato.id}_firmado_{uuid.uuid4().hex[:8]}{ext}"
    ruta.write_bytes(contenido)

    # Al (re)subir el documento, vuelve a quedar PENDIENTE de validación para que el
    # administrador pueda revisarlo de nuevo (corrige el ciclo rechazo→reemplazo→revisión).
    crud.registrar_firma(db, contrato, str(ruta))
    return contrato


@app.get("/contratos/{contrato_id}/firmado", summary="Descargar el contrato firmado")
def descargar_firmado(contrato_id: int, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    if not contrato.url_firmado or not Path(contrato.url_firmado).exists():
        raise HTTPException(status_code=404, detail="Aún no se ha subido el contrato firmado")
    return FileResponse(contrato.url_firmado, filename=f"contrato_{contrato.id}_firmado.pdf")


# ─────────────────────────  PAGOS  ─────────────────────────

@app.get("/contratos/{contrato_id}/pagos", response_model=List[schemas.PagoResponse],
         summary="Calendario / historial de pagos del contrato")
def listar_pagos(contrato_id: int, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)   # actualiza vencidos
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    return contrato.pagos


@app.post("/contratos/{contrato_id}/pagos", response_model=schemas.PagoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Registrar un pago en EFECTIVO (queda pendiente de verificación)")
def registrar_pago(contrato_id: int, datos: schemas.PagoCreate, request: Request,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    _exigir_contrato_pagable(contrato)
    # Transferencia debe usar el endpoint con comprobante.
    if datos.metodo == schemas.MetodoPago.transferencia:
        raise HTTPException(status_code=422,
            detail="La transferencia requiere adjuntar comprobante; usa el registro con comprobante.")
    ip = request.client.host if request.client else None
    uid = int(user["sub"])
    try:
        # Pago manual: queda 'pendiente_de_verificacion' (no se marca pagado).
        pago = crud.registrar_pago(db, contrato, datos, usuario_id=uid, ip=ip, confirmado=False)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return pago


@app.post("/contratos/{contrato_id}/pagos/transferencia", response_model=schemas.PagoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Registrar un pago por TRANSFERENCIA con comprobante (pendiente de verificación)")
async def registrar_pago_transferencia(contrato_id: int, request: Request,
                                       monto: float = Form(...), numero_cuota: int | None = Form(None),
                                       file: UploadFile = File(...),
                                       db: Session = Depends(get_db), user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    _exigir_contrato_pagable(contrato)

    if file.content_type not in ("application/pdf", "image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="El comprobante debe ser PDF o imagen")
    contenido = await file.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El comprobante supera 10 MB")

    ip = request.client.host if request.client else None
    uid = int(user["sub"])
    try:
        pago = crud.registrar_pago(
            db, contrato, schemas.PagoCreate(monto=monto, metodo=schemas.MetodoPago.transferencia, numero_cuota=numero_cuota),
            usuario_id=uid, ip=ip, confirmado=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Guardar el comprobante y vincularlo al pago.
    ext = ".pdf" if file.content_type == "application/pdf" else Path(file.filename or "").suffix or ".bin"
    ruta = CONTRACTS_DIR / f"comprobante_{contrato_id}_{uuid.uuid4().hex[:8]}{ext}"
    ruta.write_bytes(contenido)
    crud.crear_comprobante(db, contrato_id, uid, str(ruta), pago_id=pago.id)
    return pago


@app.patch("/pagos/{pago_id}/verificar", response_model=schemas.PagoResponse,
           summary="Aprobar o rechazar un pago pendiente de verificación (administrador)")
def verificar_pago(pago_id: int, datos: schemas.PagoVerificacion,
                   db: Session = Depends(get_db), admin=Depends(get_current_admin)):
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

    # Venta liquidada al aprobar → el inmueble pasa a 'vendido'.
    if datos.aprobado and contrato.tipo == "Venta" and crud.resumen_contrato(contrato).liquidado:
        try:
            property_client.set_estado_inmueble(contrato.inmueble_id, "vendido", system_token())
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Pago aprobado pero no se pudo marcar el inmueble como vendido: {e}")
    return pago


@app.post("/contratos/{contrato_id}/pagos/stripe", response_model=schemas.PagoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Pago con tarjeta vía Stripe (PaymentIntent real, entorno de pruebas)")
def pagar_con_stripe(contrato_id: int, datos: schemas.PagoStripeCreate, request: Request,
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    _exigir_contrato_pagable(contrato)
    uid = int(user["sub"])
    ip = request.client.host if request.client else None

    # Stripe exige un monto mínimo por transacción (~$10 MXN). Para importes menores
    # (p. ej. mensualidades pequeñas), se indica usar efectivo o transferencia.
    if float(datos.monto) < STRIPE_MIN_MXN:
        raise HTTPException(status_code=422,
            detail=f"El pago con tarjeta requiere al menos ${STRIPE_MIN_MXN:.2f} MXN. "
                   f"Para montos menores usa efectivo o transferencia.")

    # Crear y confirmar el PaymentIntent REAL contra Stripe (no se simula).
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
        # Datos inválidos del cargo (p. ej. monto fuera de rango): se devuelve la causa real.
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=422, detail=f"No se pudo procesar el pago con tarjeta: {msg}")
    except stripe.error.StripeError as e:
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(status_code=502, detail=f"No se pudo procesar el pago con Stripe: {msg}")

    if intent.status != "succeeded":
        raise HTTPException(status_code=402, detail=f"El pago no se completó (estado: {intent.status}).")

    # Pago exitoso y CONFIRMADO por Stripe → se registra directamente como 'pagado'.
    try:
        pago = crud._registrar_pago_confirmado_stripe(db, contrato, datos.monto, uid, ip, intent.id, datos.numero_cuota)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if contrato.tipo == "Venta" and crud.resumen_contrato(contrato).liquidado:
        try:
            property_client.set_estado_inmueble(contrato.inmueble_id, "vendido", system_token())
        except Exception:
            pass
    return pago


@app.get("/contratos/{contrato_id}/resumen", response_model=schemas.ResumenContrato,
         summary="Resumen económico (venta o renta): total, pagado, saldo, % y vencimientos")
def resumen(contrato_id: int, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    return crud.resumen_contrato(contrato)


@app.patch("/contratos/{contrato_id}/estado", response_model=schemas.ContratoResponse,
           summary="Cambiar el estado del contrato (administrador)")
def cambiar_estado_contrato(contrato_id: int, datos: schemas.ContratoEstadoUpdate,
                            db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    anterior = contrato.estado
    crud.cambiar_estado_contrato(db, contrato, datos.estado.value)
    return contrato


@app.post("/contratos/{contrato_id}/documento", response_model=schemas.ContratoResponse,
          summary="Aprobar o rechazar la documentación firmada (administrador)")
def validar_documento(contrato_id: int, datos: schemas.DocumentoValidacion,
                      db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if not contrato.url_firmado:
        raise HTTPException(status_code=409, detail="El contrato aún no tiene documento firmado para validar")
    if not datos.aprobado and not (datos.motivo or "").strip():
        raise HTTPException(status_code=422, detail="Indica el motivo del rechazo")
    crud.validar_documento(db, contrato, datos.aprobado, datos.motivo)
    # Al aprobar formalmente la documentación de una VENTA, el inmueble queda 'vendido'
    # (deja de aceptar nuevas operaciones: las solicitudes exigen 'en venta'/'en renta').
    if datos.aprobado and contrato.tipo == "Venta":
        try:
            property_client.set_estado_inmueble(contrato.inmueble_id, "vendido", system_token())
        except Exception as e:
            raise HTTPException(status_code=502,
                detail=f"Documento aprobado pero no se pudo marcar el inmueble como vendido: {e}")
    return contrato


# ─────────────────────────  SOLICITUDES DE RENTA  ─────────────────────────

@app.post("/solicitudes", response_model=schemas.SolicitudResponse,
          status_code=status.HTTP_201_CREATED,
          summary="El cliente solicita rentar un inmueble disponible")
def crear_solicitud(datos: schemas.SolicitudCreate, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    # Los administradores no usan el flujo de cliente para solicitar (renta o compra).
    if user.get("is_admin"):
        raise HTTPException(status_code=403,
            detail="Un administrador no puede generar solicitudes. Use el registro manual.")
    tipo = datos.tipo_operacion.value
    if tipo == "renta":
        if not datos.fecha_inicio or not datos.fecha_fin:
            raise HTTPException(status_code=422, detail="La renta requiere fecha de inicio y de fin")
        # Tolerancia de 1 día por diferencias de zona horaria entre cliente y servidor (UTC).
        if datos.fecha_inicio < date.today() - timedelta(days=1):
            raise HTTPException(status_code=422, detail="La fecha de inicio no puede ser anterior a hoy")
        if datos.fecha_fin <= datos.fecha_inicio:
            raise HTTPException(status_code=422, detail="La fecha de fin debe ser posterior a la de inicio")

    inm = property_client.get_inmueble(datos.inmueble_id)
    if not inm:
        raise HTTPException(status_code=404, detail="El inmueble no existe")
    # Regla de negocio: el estado del inmueble debe coincidir con la operación solicitada.
    estado_actual = property_client.estado_inmueble(inm)
    esperado = "en renta" if tipo == "renta" else "en venta"
    if estado_actual != esperado:
        raise HTTPException(status_code=409,
                            detail=f"El inmueble no está disponible para {tipo} (estado: {estado_actual})")

    sol = crud.crear_solicitud(db, int(user["sub"]), datos)
    return sol


@app.get("/solicitudes", response_model=List[schemas.SolicitudResponse],
         summary="Listar todas las solicitudes (administrador)")
def listar_solicitudes(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return crud.todas_solicitudes(db)


@app.get("/solicitudes/usuario/{usuario_id}", response_model=List[schemas.SolicitudResponse])
def solicitudes_usuario(usuario_id: int, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    require_owner_or_admin(user, usuario_id)
    return crud.solicitudes_por_usuario(db, usuario_id)


@app.get("/solicitudes/{solicitud_id}", response_model=schemas.SolicitudResponse)
def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    sol = crud.obtener_solicitud(db, solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    require_owner_or_admin(user, sol.usuario_id)
    return sol


@app.patch("/solicitudes/{solicitud_id}/estado", response_model=schemas.SolicitudResponse,
           summary="Cambiar el estado de la solicitud (administrador)")
def cambiar_estado_solicitud(solicitud_id: int, datos: schemas.SolicitudEstadoUpdate,
                             db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    sol = crud.obtener_solicitud(db, solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    crud.cambiar_estado_solicitud(db, sol, datos.estado.value)
    return sol


@app.patch("/solicitudes/{solicitud_id}/cancelar", response_model=schemas.SolicitudResponse,
           summary="El cliente cancela su solicitud")
def cancelar_solicitud(solicitud_id: int, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    sol = crud.obtener_solicitud(db, solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    require_owner_or_admin(user, sol.usuario_id)
    if sol.estado not in ("pendiente", "en revision"):
        raise HTTPException(status_code=409, detail="La solicitud ya no se puede cancelar")
    crud.cambiar_estado_solicitud(db, sol, "cancelada")
    return sol


@app.post("/solicitudes/{solicitud_id}/contrato", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Generar el contrato a partir de una solicitud APROBADA (admin)")
def generar_contrato_desde_solicitud(solicitud_id: int, datos: schemas.GenerarContratoRenta,
                                     request: Request, db: Session = Depends(get_db),
                                     admin=Depends(get_current_admin)):
    sol = crud.obtener_solicitud(db, solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if sol.estado != "aprobada":
        raise HTTPException(status_code=409, detail="La solicitud debe estar APROBADA para generar el contrato")
    if sol.contrato_id:
        raise HTTPException(status_code=409, detail="La solicitud ya tiene un contrato generado")
    if sol.tipo_operacion != "renta":
        raise HTTPException(status_code=422, detail="Esta solicitud es de compra; use el contrato de venta")

    # La duración del contrato proviene de la solicitud; el admin puede modificarla.
    fecha_inicio = datos.fecha_inicio or sol.fecha_inicio
    fecha_fin = datos.fecha_fin or sol.fecha_fin
    if not fecha_inicio or not fecha_fin:
        raise HTTPException(status_code=422, detail="Faltan fechas de inicio/fin del contrato")
    if fecha_fin <= fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha de fin debe ser posterior a la de inicio")

    # Crear contrato de renta asociado automáticamente al cliente y al inmueble.
    contrato = crud.crear_contrato(db, schemas.ContratoCreate(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        tipo=schemas.TipoContrato.renta, monto=datos.monto,
        condiciones=datos.condiciones,
        usuario_id=sol.usuario_id, inmueble_id=sol.inmueble_id,
        clausula_ids=datos.clausula_ids, clausulas_nuevas=datos.clausulas_nuevas,
    ))
    _generar_y_guardar_pdf(db, contrato, request.headers.get("Authorization", ""))

    # Vincular y formalizar: el inmueble pasa a 'rentado'.
    sol.contrato_id = contrato.id
    db.commit()
    try:
        property_client.set_estado_inmueble(sol.inmueble_id, "rentado",
                                             request.headers.get("Authorization", ""))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Contrato creado pero no se pudo actualizar el inmueble: {e}")

    return contrato


@app.post("/solicitudes/{solicitud_id}/contrato-venta", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Generar el contrato de COMPRAVENTA de una solicitud de compra APROBADA (admin)")
def generar_contrato_venta_desde_solicitud(solicitud_id: int, datos: schemas.GenerarContratoVenta,
                                           request: Request, db: Session = Depends(get_db),
                                           admin=Depends(get_current_admin)):
    sol = crud.obtener_solicitud(db, solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if sol.tipo_operacion != "venta":
        raise HTTPException(status_code=422, detail="Esta solicitud no es de compra")
    if sol.estado != "aprobada":
        raise HTTPException(status_code=409, detail="La solicitud debe estar APROBADA para generar el contrato")
    if sol.contrato_id:
        raise HTTPException(status_code=409, detail="La solicitud ya tiene un contrato generado")

    contrato = crud.crear_contrato(db, schemas.ContratoCreate(
        fecha_inicio=date.today(), fecha_fin=None,
        tipo=schemas.TipoContrato.venta, monto=datos.monto, condiciones=datos.condiciones,
        usuario_id=sol.usuario_id, inmueble_id=sol.inmueble_id,
        clausula_ids=datos.clausula_ids, clausulas_nuevas=datos.clausulas_nuevas,
        meses_plazo=datos.meses_plazo,
    ))
    _generar_y_guardar_pdf(db, contrato, request.headers.get("Authorization", ""))

    sol.contrato_id = contrato.id
    db.commit()
    # Al formalizar la venta el inmueble queda 'reservado' hasta la liquidación total.
    try:
        property_client.set_estado_inmueble(sol.inmueble_id, "reservado",
                                             request.headers.get("Authorization", ""))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Contrato creado pero no se pudo actualizar el inmueble: {e}")

    return contrato


# ─────────────────────────  COMPROBANTES DE PAGO  ─────────────────────────
# Los comprobantes se crean ligados a un pago en el endpoint /pagos/transferencia.
# No existe subida "suelta" para evitar comprobantes huérfanos sin pago asociado.


@app.get("/contratos/{contrato_id}/comprobantes", response_model=List[schemas.ComprobanteResponse])
def listar_comprobantes(contrato_id: int, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    return crud.comprobantes_por_contrato(db, contrato_id)


@app.get("/comprobantes/{comprobante_id}/archivo", summary="Descargar un comprobante")
def descargar_comprobante(comprobante_id: int, db: Session = Depends(get_db),
                          user=Depends(get_current_user)):
    comp = crud.obtener_comprobante(db, comprobante_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    contrato = crud.obtener_contrato(db, comp.contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    if not Path(comp.url_archivo).exists():
        raise HTTPException(status_code=404, detail="Archivo no disponible")
    return FileResponse(comp.url_archivo, filename=f"comprobante_{comp.id}{Path(comp.url_archivo).suffix}")


# ─────────────────────────  GESTIÓN DE RENTAS  ─────────────────────────
# El alta de renta se hace siempre desde una solicitud aprobada del cliente
# (no hay "renta manual" ni "renovación": no forman parte del flujo definido).

@app.patch("/contratos/{contrato_id}/finalizar", response_model=schemas.ContratoResponse,
           summary="Finalizar una renta (NO libera el inmueble automáticamente)")
def finalizar_renta(contrato_id: int, request: Request,
                    db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return _cerrar_renta(db, contrato_id, "finalizado", request, admin)


@app.patch("/contratos/{contrato_id}/cancelar", response_model=schemas.ContratoResponse,
           summary="Cancelar una renta (NO libera el inmueble automáticamente)")
def cancelar_renta(contrato_id: int, request: Request,
                   db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return _cerrar_renta(db, contrato_id, "cancelado", request, admin)


def _cerrar_renta(db, contrato_id, nuevo_estado, request, admin):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    crud.cambiar_estado_contrato(db, contrato, nuevo_estado)
    # Nota: finalizar/cancelar el contrato NO libera el inmueble automáticamente.
    # La disponibilidad la decide el administrador desde la gestión de inmuebles,
    # según las reglas de negocio (puede haber condiciones que impidan liberarlo).
    return contrato


# ─────────────────────────  CATÁLOGO DE CLÁUSULAS  ─────────────────────────

@app.get("/clausulas-catalogo", response_model=List[schemas.ClausulaCatalogoResponse],
         summary="Listar el catálogo de cláusulas (jerárquico)")
def listar_clausulas_catalogo(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.listar_clausulas_catalogo(db)


@app.post("/clausulas-catalogo", response_model=schemas.ClausulaCatalogoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Crear una cláusula en el catálogo (administrador)")
def crear_clausula_catalogo(datos: schemas.ClausulaCatalogoCreate,
                            db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        return crud.crear_clausula_catalogo(db, datos)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.delete("/clausulas-catalogo/{clausula_id}", summary="Eliminar una cláusula del catálogo (administrador)")
def eliminar_clausula_catalogo(clausula_id: int, db: Session = Depends(get_db),
                               admin=Depends(get_current_admin)):
    if not crud.eliminar_clausula_catalogo(db, clausula_id):
        raise HTTPException(status_code=404, detail="Cláusula no encontrada")
    return {"message": "Cláusula eliminada"}


@app.get("/stripe-config", summary="Clave publicable de Stripe para el formulario de tarjeta")
def stripe_config():
    return {"publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY", ""), "min_mxn": STRIPE_MIN_MXN}


@app.get("/health")
def health():
    return {"status": "ok"}
