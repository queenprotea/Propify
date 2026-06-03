from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import Response, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from datetime import date
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
    crud.registrar_auditoria(db, int(admin["sub"]), "contrato_generado", "Contrato", contrato.id,
                             f"tipo {contrato.tipo}, inmueble {contrato.inmueble_id}")
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
    estado: str | None = None, tipo: str | None = None,
    usuario_id: int | None = None, inmueble_id: int | None = None,
    fecha_desde: str | None = None, fecha_hasta: str | None = None,
    skip: int = 0, limit: int = 200,
    db: Session = Depends(get_db), admin=Depends(get_current_admin),
):
    return crud.listar_contratos(db, estado=estado, tipo=tipo, usuario_id=usuario_id,
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

    if file.content_type not in ("application/pdf", "image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="Solo se admite PDF o imagen del contrato firmado")

    contenido = await file.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo supera 10 MB")

    ext = ".pdf" if file.content_type == "application/pdf" else Path(file.filename or "").suffix or ".bin"
    ruta = CONTRACTS_DIR / f"contrato_{contrato.id}_firmado_{uuid.uuid4().hex[:8]}{ext}"
    ruta.write_bytes(contenido)

    crud.registrar_firma(db, contrato, str(ruta))
    crud.registrar_auditoria(db, int(user["sub"]), "contrato_firmado_subido", "Contrato", contrato.id,
                             "carga de documento firmado")
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
          summary="Registrar/realizar un pago (renta: mensualidad; venta: total o parcial)")
def registrar_pago(contrato_id: int, datos: schemas.PagoCreate, request: Request,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    ip = request.client.host if request.client else None
    uid = int(user["sub"])
    try:
        pago = crud.registrar_pago(db, contrato, datos, usuario_id=uid, ip=ip)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # Evento de pago en la bitácora (historial por pago).
    crud.registrar_auditoria(db, uid, "pago_aprobado", "Pago", pago.id,
                             detalle=f"contrato {contrato_id}, método {datos.metodo}",
                             valor_nuevo=f"{datos.monto} ({pago.estado})")
    # Venta liquidada → el inmueble pasa a 'vendido'.
    if contrato.tipo == "Venta" and crud.resumen_contrato(contrato).liquidado:
        try:
            property_client.set_estado_inmueble(contrato.inmueble_id, "vendido", system_token())
            crud.registrar_auditoria(db, uid, "venta_liquidada", "Contrato", contrato.id,
                                     detalle=f"inmueble {contrato.inmueble_id} -> vendido")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Pago registrado pero no se pudo marcar el inmueble como vendido: {e}")
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
    uid = int(user["sub"])
    ip = request.client.host if request.client else None

    crud.registrar_auditoria(db, uid, "pago_generado", "Contrato", contrato_id,
                             detalle=f"Stripe, monto {datos.monto}")
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
        crud.registrar_auditoria(db, uid, "pago_rechazado", "Contrato", contrato_id,
                                 detalle=f"Stripe: {e.user_message or str(e)}")
        raise HTTPException(status_code=402, detail=f"Tarjeta rechazada: {e.user_message or 'verifica los datos'}")
    except stripe.error.StripeError as e:
        crud.registrar_auditoria(db, uid, "pago_error", "Contrato", contrato_id, detalle=f"Stripe: {str(e)}")
        raise HTTPException(status_code=502, detail="No se pudo procesar el pago con Stripe. Intenta más tarde.")

    if intent.status != "succeeded":
        crud.registrar_auditoria(db, uid, "pago_rechazado", "Contrato", contrato_id,
                                 detalle=f"Stripe estado: {intent.status}")
        raise HTTPException(status_code=402, detail=f"El pago no se completó (estado: {intent.status}).")

    # Pago exitoso → registrar con el identificador de transacción de Stripe.
    try:
        pago = crud.registrar_pago(db, contrato, schemas.PagoCreate(monto=datos.monto, metodo="stripe"),
                                   usuario_id=uid, ip=ip, stripe_payment_intent=intent.id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    crud.registrar_auditoria(db, uid, "pago_aprobado", "Pago", pago.id,
                             detalle=f"Stripe intent {intent.id}", valor_nuevo=f"{datos.monto} pagado")
    if contrato.tipo == "Venta" and crud.resumen_contrato(contrato).liquidado:
        try:
            property_client.set_estado_inmueble(contrato.inmueble_id, "vendido", system_token())
            crud.registrar_auditoria(db, uid, "venta_liquidada", "Contrato", contrato.id,
                                     detalle=f"inmueble {contrato.inmueble_id} -> vendido")
        except Exception:
            pass
    return pago


@app.get("/pagos/{pago_id}/eventos", response_model=List[schemas.AuditoriaResponse],
         summary="Historial de eventos de un pago")
def eventos_pago(pago_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pago = db.query(models.Pago).filter(models.Pago.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    contrato = crud.obtener_contrato(db, pago.contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    return crud.auditoria_por_entidad(db, "Pago", pago_id)


@app.get("/contratos/{contrato_id}/resumen", response_model=schemas.ResumenContrato,
         summary="Resumen económico (venta o renta): total, pagado, saldo, % y vencimientos")
def resumen(contrato_id: int, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    return crud.resumen_contrato(contrato)


@app.get("/contratos/{contrato_id}/historial", response_model=List[schemas.AuditoriaResponse],
         summary="Historial de cambios del contrato")
def historial_contrato(contrato_id: int, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)
    return crud.auditoria_por_entidad(db, "Contrato", contrato_id)


@app.patch("/contratos/{contrato_id}/estado", response_model=schemas.ContratoResponse,
           summary="Cambiar el estado del contrato (administrador)")
def cambiar_estado_contrato(contrato_id: int, datos: schemas.ContratoEstadoUpdate,
                            db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    anterior = contrato.estado
    crud.cambiar_estado_contrato(db, contrato, datos.estado.value)
    crud.registrar_auditoria(db, int(admin["sub"]), "contrato_estado", "Contrato", contrato_id,
                             detalle="cambio de estado", valor_anterior=anterior, valor_nuevo=datos.estado.value)
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
    crud.registrar_auditoria(db, int(admin["sub"]), "documento_validado", "Contrato", contrato_id,
                             "aprobado" if datos.aprobado else f"rechazado: {datos.motivo}")
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
    if tipo == "renta" and (not datos.fecha_inicio or not datos.fecha_fin):
        raise HTTPException(status_code=422, detail="La renta requiere fecha de inicio y de fin")

    inm = property_client.get_inmueble(datos.inmueble_id)
    if not inm:
        raise HTTPException(status_code=404, detail="El inmueble no existe")
    # Regla de negocio: el inmueble debe estar disponible.
    if inm.get("estado") != "disponible":
        raise HTTPException(status_code=409,
                            detail=f"El inmueble no está disponible (estado: {inm.get('estado')})")
    # La operación solicitada debe coincidir con la oferta del inmueble.
    if inm.get("operacion") != tipo:
        raise HTTPException(status_code=422, detail=f"El inmueble no está ofertado en {tipo}")

    sol = crud.crear_solicitud(db, int(user["sub"]), datos)
    crud.registrar_auditoria(db, int(user["sub"]), f"solicitud_{tipo}_creada", "SolicitudRenta", sol.id,
                             f"inmueble {datos.inmueble_id}")
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
    crud.registrar_auditoria(db, int(admin["sub"]), "solicitud_estado", "SolicitudRenta", sol.id,
                             f"-> {datos.estado.value}")
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
    crud.registrar_auditoria(db, int(user["sub"]), "solicitud_cancelada", "SolicitudRenta", sol.id)
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

    crud.registrar_auditoria(db, int(admin["sub"]), "contrato_desde_solicitud", "Contrato", contrato.id,
                             f"solicitud {sol.id}, inmueble {sol.inmueble_id} -> rentado")
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

    crud.registrar_auditoria(db, int(admin["sub"]), "contrato_venta_desde_solicitud", "Contrato", contrato.id,
                             f"solicitud {sol.id}, inmueble {sol.inmueble_id} -> reservado")
    return contrato


# ─────────────────────────  COMPROBANTES DE PAGO  ─────────────────────────

@app.post("/contratos/{contrato_id}/comprobantes", response_model=schemas.ComprobanteResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Subir un comprobante de pago")
async def subir_comprobante(contrato_id: int, file: UploadFile = File(...),
                            db: Session = Depends(get_db), user=Depends(get_current_user)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    require_owner_or_admin(user, contrato.usuario_id)

    if file.content_type not in ("application/pdf", "image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="Solo se admite PDF o imagen")
    contenido = await file.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo supera 10 MB")
    ext = ".pdf" if file.content_type == "application/pdf" else Path(file.filename or "").suffix or ".bin"
    ruta = CONTRACTS_DIR / f"comprobante_{contrato_id}_{uuid.uuid4().hex[:8]}{ext}"
    ruta.write_bytes(contenido)

    comp = crud.crear_comprobante(db, contrato_id, int(user["sub"]), str(ruta))
    crud.registrar_auditoria(db, int(user["sub"]), "comprobante_subido", "Comprobante", comp.id,
                             f"contrato {contrato_id}")
    return comp


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


# ─────────────────────────  AUDITORÍA  ─────────────────────────

@app.get("/auditoria", response_model=List[schemas.AuditoriaResponse],
         summary="Bitácora de acciones (administrador)")
def listar_auditoria(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return crud.listar_auditoria(db)


# ─────────────────────────  REGISTRO MANUAL DE RENTA (ADMIN)  ─────────────────────────

@app.post("/rentas/manual", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="El administrador registra directamente una renta (genera contrato, calendario y rentado)")
def registrar_renta_manual(datos: schemas.RentaManualCreate, request: Request,
                           db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    # Validaciones de negocio: el inmueble debe existir, estar disponible y ser de renta.
    inm = property_client.get_inmueble(datos.inmueble_id)
    if not inm:
        raise HTTPException(status_code=404, detail="El inmueble no existe")
    if inm.get("estado") != "disponible":
        raise HTTPException(status_code=409, detail=f"El inmueble no está disponible (estado: {inm.get('estado')})")

    contrato = crud.crear_contrato(db, schemas.ContratoCreate(
        fecha_inicio=datos.fecha_inicio, fecha_fin=datos.fecha_fin,
        tipo=schemas.TipoContrato.renta, monto=datos.monto,
        condiciones=datos.condiciones, usuario_id=datos.usuario_id, inmueble_id=datos.inmueble_id,
    ))
    if datos.estado and datos.estado.value != "activo":
        crud.cambiar_estado_contrato(db, contrato, datos.estado.value)
    _generar_y_guardar_pdf(db, contrato, request.headers.get("Authorization", ""))

    # Relación cliente-inmueble formalizada: el inmueble pasa a 'rentado'.
    try:
        property_client.set_estado_inmueble(datos.inmueble_id, "rentado", request.headers.get("Authorization", ""))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Contrato creado pero no se pudo actualizar el inmueble: {e}")

    crud.registrar_auditoria(db, int(admin["sub"]), "renta_manual", "Contrato", contrato.id,
                             f"cliente {datos.usuario_id}, inmueble {datos.inmueble_id} -> rentado")
    return contrato


# ─────────────────────────  GESTIÓN DE RENTAS  ─────────────────────────

@app.post("/contratos/{contrato_id}/renovar", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Renovar un contrato de renta (genera uno nuevo y finaliza el anterior)")
def renovar_contrato(contrato_id: int, datos: schemas.RenovarContrato, request: Request,
                     db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    anterior = crud.obtener_contrato(db, contrato_id)
    if not anterior:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    if anterior.tipo != "Renta":
        raise HTTPException(status_code=422, detail="Solo se renuevan contratos de renta")
    if datos.fecha_fin <= datos.fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha de fin debe ser posterior a la de inicio")

    nuevo = crud.crear_contrato(db, schemas.ContratoCreate(
        fecha_inicio=datos.fecha_inicio, fecha_fin=datos.fecha_fin,
        tipo=schemas.TipoContrato.renta, monto=datos.monto,
        usuario_id=anterior.usuario_id, inmueble_id=anterior.inmueble_id,
    ), contrato_padre_id=anterior.id)
    _generar_y_guardar_pdf(db, nuevo, request.headers.get("Authorization", ""))
    crud.cambiar_estado_contrato(db, anterior, "finalizado")  # el anterior se cierra
    crud.registrar_auditoria(db, int(admin["sub"]), "renta_renovada", "Contrato", nuevo.id,
                             f"renueva contrato {anterior.id}")
    return nuevo


@app.patch("/contratos/{contrato_id}/finalizar", response_model=schemas.ContratoResponse,
           summary="Finalizar una renta (libera el inmueble)")
def finalizar_renta(contrato_id: int, request: Request,
                    db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return _cerrar_renta(db, contrato_id, "finalizado", request, admin)


@app.patch("/contratos/{contrato_id}/cancelar", response_model=schemas.ContratoResponse,
           summary="Cancelar una renta (libera el inmueble)")
def cancelar_renta(contrato_id: int, request: Request,
                   db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return _cerrar_renta(db, contrato_id, "cancelado", request, admin)


def _cerrar_renta(db, contrato_id, nuevo_estado, request, admin):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    crud.cambiar_estado_contrato(db, contrato, nuevo_estado)
    # Liberar el inmueble: vuelve a 'disponible'.
    try:
        property_client.set_estado_inmueble(contrato.inmueble_id, "disponible",
                                             request.headers.get("Authorization", ""))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Estado actualizado pero no se pudo liberar el inmueble: {e}")
    crud.registrar_auditoria(db, int(admin["sub"]), f"renta_{nuevo_estado}", "Contrato", contrato_id,
                             f"inmueble {contrato.inmueble_id} -> disponible")
    return contrato


@app.get("/health")
def health():
    return {"status": "ok"}
