from fastapi import FastAPI, Depends, status, UploadFile, File, Form, Request
from fastapi.responses import Response, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import os

import schemas
from database import get_db
from security import get_current_user, get_current_admin
from services import contrato_service, pago_service, solicitud_service, clausula_service

# Capas: main (HTTP) → services (negocio) → crud (datos). Las tablas las crea db/init.sql.

app = FastAPI(
    title="Contract Service",
    description="Gestión de contratos digitales (Venta/Renta) y sus pagos",
    version="2.0.0",
)


@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado. Inténtalo de nuevo más tarde."},
    )


# ─────────────────────────  CONTRATOS  ─────────────────────────

@app.post("/contratos", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Generar un contrato digital (solo administrador)")
def crear_contrato(datos: schemas.ContratoCreate, request: Request,
                   db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return contrato_service.crear_contrato(db, datos, request.headers.get("Authorization", ""))


@app.get("/contratos/{contrato_id}", response_model=schemas.ContratoResponse)
def obtener_contrato(contrato_id: int, db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    return contrato_service.obtener(db, contrato_id, user)


@app.get("/contratos/usuario/{usuario_id}", response_model=List[schemas.ContratoResponse])
def contratos_por_usuario(usuario_id: int, skip: int = 0, limit: int = 50,
                          db: Session = Depends(get_db), user=Depends(get_current_user)):
    return contrato_service.por_usuario(db, usuario_id, user, skip, limit)


@app.get("/contratos/inmueble/{inmueble_id}", response_model=List[schemas.ContratoResponse])
def contratos_por_inmueble(inmueble_id: int, skip: int = 0, limit: int = 50,
                           db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return contrato_service.por_inmueble(db, inmueble_id, skip, limit)


@app.get("/contratos", response_model=List[schemas.ContratoResponse],
         summary="Listar TODOS los contratos con filtros (administrador)")
def listar_contratos(
    estado: str | None = None, tipo: str | None = None, folio: str | None = None,
    usuario_id: int | None = None, inmueble_id: int | None = None,
    fecha_desde: str | None = None, fecha_hasta: str | None = None,
    skip: int = 0, limit: int = 200,
    db: Session = Depends(get_db), admin=Depends(get_current_admin),
):
    return contrato_service.listar(db, estado=estado, tipo=tipo, folio=folio, usuario_id=usuario_id,
                                   inmueble_id=inmueble_id, fecha_desde=fecha_desde,
                                   fecha_hasta=fecha_hasta, skip=skip, limit=limit)


# ─────────────────────────  PDF: original / firmado  ─────────────────────────

@app.get("/contratos/{contrato_id}/pdf", summary="Descargar el contrato original (PDF)")
def descargar_pdf(contrato_id: int, request: Request, db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    pdf_bytes = contrato_service.pdf_original(db, contrato_id, user, request.headers.get("Authorization", ""))
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="contrato_{contrato_id}.pdf"'},
    )


@app.post("/contratos/{contrato_id}/firmado", response_model=schemas.ContratoResponse,
          summary="Subir el contrato FIRMADO (cliente o administrador)")
async def subir_firmado(contrato_id: int, file: UploadFile = File(...),
                        db: Session = Depends(get_db), user=Depends(get_current_user)):
    return await contrato_service.subir_firmado(db, contrato_id, user, file)


@app.get("/contratos/{contrato_id}/firmado", summary="Descargar el contrato firmado")
def descargar_firmado(contrato_id: int, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    ruta = contrato_service.ruta_firmado(db, contrato_id, user)
    return FileResponse(ruta, filename=f"contrato_{contrato_id}_firmado.pdf")


# ─────────────────────────  PAGOS  ─────────────────────────

@app.get("/contratos/{contrato_id}/pagos", response_model=List[schemas.PagoResponse],
         summary="Calendario / historial de pagos del contrato")
def listar_pagos(contrato_id: int, db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    return pago_service.listar_pagos(db, contrato_id, user)


@app.post("/contratos/{contrato_id}/pagos", response_model=schemas.PagoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Registrar un pago en EFECTIVO (queda pendiente de verificación)")
def registrar_pago(contrato_id: int, datos: schemas.PagoCreate, request: Request,
                   db: Session = Depends(get_db), user=Depends(get_current_user)):
    ip = request.client.host if request.client else None
    return pago_service.registrar_efectivo(db, contrato_id, datos, user, ip)


@app.post("/contratos/{contrato_id}/pagos/transferencia", response_model=schemas.PagoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Registrar un pago por TRANSFERENCIA con comprobante (pendiente de verificación)")
async def registrar_pago_transferencia(contrato_id: int, request: Request,
                                       monto: float = Form(...), numero_cuota: int | None = Form(None),
                                       file: UploadFile = File(...),
                                       db: Session = Depends(get_db), user=Depends(get_current_user)):
    ip = request.client.host if request.client else None
    return await pago_service.registrar_transferencia(db, contrato_id, monto, numero_cuota, file, user, ip)


@app.patch("/pagos/{pago_id}/verificar", response_model=schemas.PagoResponse,
           summary="Aprobar o rechazar un pago pendiente de verificación (administrador)")
def verificar_pago(pago_id: int, datos: schemas.PagoVerificacion,
                   db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return pago_service.verificar_pago(db, pago_id, datos)


@app.post("/contratos/{contrato_id}/pagos/stripe", response_model=schemas.PagoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Pago con tarjeta vía Stripe (PaymentIntent real, entorno de pruebas)")
def pagar_con_stripe(contrato_id: int, datos: schemas.PagoStripeCreate, request: Request,
                     db: Session = Depends(get_db), user=Depends(get_current_user)):
    ip = request.client.host if request.client else None
    return pago_service.pagar_stripe(db, contrato_id, datos, user, ip)


@app.get("/contratos/{contrato_id}/resumen", response_model=schemas.ResumenContrato,
         summary="Resumen económico (venta o renta): total, pagado, saldo, % y vencimientos")
def resumen(contrato_id: int, db: Session = Depends(get_db),
            user=Depends(get_current_user)):
    return contrato_service.resumen(db, contrato_id, user)


@app.patch("/contratos/{contrato_id}/estado", response_model=schemas.ContratoResponse,
           summary="Cambiar el estado del contrato (administrador)")
def cambiar_estado_contrato(contrato_id: int, datos: schemas.ContratoEstadoUpdate,
                            db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return contrato_service.cambiar_estado(db, contrato_id, datos.estado.value)


@app.post("/contratos/{contrato_id}/documento", response_model=schemas.ContratoResponse,
          summary="Aprobar o rechazar la documentación firmada (administrador)")
def validar_documento(contrato_id: int, datos: schemas.DocumentoValidacion,
                      db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return contrato_service.validar_documento(db, contrato_id, datos)


# ─────────────────────────  SOLICITUDES DE RENTA  ─────────────────────────

@app.post("/solicitudes", response_model=schemas.SolicitudResponse,
          status_code=status.HTTP_201_CREATED,
          summary="El cliente solicita rentar un inmueble disponible")
def crear_solicitud(datos: schemas.SolicitudCreate, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    return solicitud_service.crear(db, datos, user)


@app.get("/solicitudes", response_model=List[schemas.SolicitudResponse],
         summary="Listar todas las solicitudes (administrador)")
def listar_solicitudes(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return solicitud_service.listar_todas(db)


@app.get("/solicitudes/usuario/{usuario_id}", response_model=List[schemas.SolicitudResponse])
def solicitudes_usuario(usuario_id: int, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    return solicitud_service.por_usuario(db, usuario_id, user)


@app.get("/solicitudes/{solicitud_id}", response_model=schemas.SolicitudResponse)
def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    return solicitud_service.obtener(db, solicitud_id, user)


@app.patch("/solicitudes/{solicitud_id}/estado", response_model=schemas.SolicitudResponse,
           summary="Cambiar el estado de la solicitud (administrador)")
def cambiar_estado_solicitud(solicitud_id: int, datos: schemas.SolicitudEstadoUpdate,
                             db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return solicitud_service.cambiar_estado(db, solicitud_id, datos.estado.value)


@app.patch("/solicitudes/{solicitud_id}/cancelar", response_model=schemas.SolicitudResponse,
           summary="El cliente cancela su solicitud")
def cancelar_solicitud(solicitud_id: int, db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    return solicitud_service.cancelar(db, solicitud_id, user)


@app.post("/solicitudes/{solicitud_id}/contrato", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Generar el contrato a partir de una solicitud APROBADA (admin)")
def generar_contrato_desde_solicitud(solicitud_id: int, datos: schemas.GenerarContratoRenta,
                                     request: Request, db: Session = Depends(get_db),
                                     admin=Depends(get_current_admin)):
    return solicitud_service.generar_contrato_renta(db, solicitud_id, datos,
                                                     request.headers.get("Authorization", ""))


@app.post("/solicitudes/{solicitud_id}/contrato-venta", response_model=schemas.ContratoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Generar el contrato de COMPRAVENTA de una solicitud de compra APROBADA (admin)")
def generar_contrato_venta_desde_solicitud(solicitud_id: int, datos: schemas.GenerarContratoVenta,
                                           request: Request, db: Session = Depends(get_db),
                                           admin=Depends(get_current_admin)):
    return solicitud_service.generar_contrato_venta(db, solicitud_id, datos,
                                                     request.headers.get("Authorization", ""))


# ─────────────────────────  COMPROBANTES DE PAGO  ─────────────────────────

@app.get("/contratos/{contrato_id}/comprobantes", response_model=List[schemas.ComprobanteResponse])
def listar_comprobantes(contrato_id: int, db: Session = Depends(get_db),
                        user=Depends(get_current_user)):
    return pago_service.listar_comprobantes(db, contrato_id, user)


@app.get("/comprobantes/{comprobante_id}/archivo", summary="Descargar un comprobante")
def descargar_comprobante(comprobante_id: int, db: Session = Depends(get_db),
                          user=Depends(get_current_user)):
    comp = pago_service.comprobante_descargable(db, comprobante_id, user)
    return FileResponse(comp.url_archivo, filename=f"comprobante_{comp.id}{Path(comp.url_archivo).suffix}")


# ─────────────────────────  GESTIÓN DE RENTAS  ─────────────────────────

@app.patch("/contratos/{contrato_id}/finalizar", response_model=schemas.ContratoResponse,
           summary="Finalizar una renta (libera el inmueble: vuelve a 'en renta')")
def finalizar_renta(contrato_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return contrato_service.cerrar_renta(db, contrato_id, "finalizado")


@app.patch("/contratos/{contrato_id}/cancelar", response_model=schemas.ContratoResponse,
           summary="Cancelar una renta (libera el inmueble: vuelve a 'en renta')")
def cancelar_renta(contrato_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return contrato_service.cerrar_renta(db, contrato_id, "cancelado")


# ─────────────────────────  CATÁLOGO DE CLÁUSULAS  ─────────────────────────

@app.get("/clausulas-catalogo", response_model=List[schemas.ClausulaCatalogoResponse],
         summary="Listar el catálogo de cláusulas (jerárquico)")
def listar_clausulas_catalogo(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return clausula_service.listar(db)


@app.post("/clausulas-catalogo", response_model=schemas.ClausulaCatalogoResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Crear una cláusula en el catálogo (administrador)")
def crear_clausula_catalogo(datos: schemas.ClausulaCatalogoCreate,
                            db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return clausula_service.crear(db, datos)


@app.delete("/clausulas-catalogo/{clausula_id}", summary="Eliminar una cláusula del catálogo (administrador)")
def eliminar_clausula_catalogo(clausula_id: int, db: Session = Depends(get_db),
                               admin=Depends(get_current_admin)):
    return clausula_service.eliminar(db, clausula_id)


@app.get("/stripe-config", summary="Clave publicable de Stripe para el formulario de tarjeta")
def stripe_config():
    return {"publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY", ""), "min_mxn": pago_service.STRIPE_MIN_MXN}


@app.get("/health")
def health():
    return {"status": "ok"}
