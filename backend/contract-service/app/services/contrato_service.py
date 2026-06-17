"""Lógica de negocio de contratos."""
from pathlib import Path

from fastapi import HTTPException

import crud
import pdf
import property_client
import user_client
import storage
from security import require_owner_or_admin, system_token


def generar_y_guardar_pdf(db, contrato, auth_header: str = ""):
    try:
        inmueble = property_client.get_inmueble(contrato.inmueble_id)
    except Exception:
        inmueble = None
    ubicacion = property_client.get_ubicacion(inmueble.get("ubicacion_id")) if inmueble else None
    cliente = user_client.get_usuario(contrato.usuario_id, auth_header)

    pdf_bytes = pdf.generar_pdf_contrato(
        contrato, cliente=cliente, inmueble=inmueble, ubicacion=ubicacion, pagos=list(contrato.pagos),
    )
    ruta = storage.guardar_pdf_original(contrato.id, pdf_bytes)
    contrato.url_archivo = str(ruta)
    db.commit()
    db.refresh(contrato)
    return contrato


def liberar_inmueble_renta(inmueble_id: int, token: str | None = None) -> None:
    property_client.set_estado_inmueble(inmueble_id, "en renta", token or system_token())


def auto_finalizar_rentas_vencidas(db) -> None:
    """Finaliza rentas con plazo vencido y pagos cubiertos, liberando el inmueble."""
    for contrato in crud.rentas_para_autofinalizar(db):
        crud.cambiar_estado_contrato(db, contrato, "finalizado")
        try:
            liberar_inmueble_renta(contrato.inmueble_id)
        except Exception:
            pass


def _obtener_o_404(db, contrato_id):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato


def crear_contrato(db, datos, auth_header: str = ""):
    contrato = crud.crear_contrato(db, datos)
    try:
        generar_y_guardar_pdf(db, contrato, auth_header)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el PDF: {e}")
    return contrato


def obtener(db, contrato_id, user):
    contrato = _obtener_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    return contrato


def por_usuario(db, usuario_id, user, skip=0, limit=50):
    require_owner_or_admin(user, usuario_id)
    auto_finalizar_rentas_vencidas(db)
    return crud.obtener_contratos_por_usuario(db, usuario_id, skip, limit)


def por_inmueble(db, inmueble_id, skip=0, limit=50):
    return crud.obtener_contratos_por_inmueble(db, inmueble_id, skip, limit)


def listar(db, **filtros):
    auto_finalizar_rentas_vencidas(db)
    return crud.listar_contratos(db, **filtros)


def pdf_original(db, contrato_id, user, auth_header: str = ""):
    contrato = _obtener_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)

    ruta = Path(contrato.url_archivo) if contrato.url_archivo else None
    if ruta and ruta.exists():
        pdf_bytes = ruta.read_bytes()
    else:
        generar_y_guardar_pdf(db, contrato, auth_header)
        pdf_bytes = Path(contrato.url_archivo).read_bytes()

    crud.registrar_descarga(db, contrato)
    return pdf_bytes


async def subir_firmado(db, contrato_id, user, file):
    contrato = _obtener_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)

    if contrato.estado_documento == "aprobado":
        raise HTTPException(status_code=409,
            detail="El documento firmado ya fue aprobado; no puede reemplazarse.")
    if contrato.estado in ("cancelado", "finalizado", "liquidado"):
        raise HTTPException(status_code=409,
            detail=f"El contrato está {contrato.estado}; no se puede reemplazar el documento firmado.")

    nombre = (file.filename or "").lower()
    if file.content_type != "application/pdf" or not nombre.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El contrato firmado debe ser un archivo PDF")

    contenido = await file.read()
    if len(contenido) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo supera 10 MB")

    ruta = storage.guardar_firmado(contrato.id, contenido)
    crud.registrar_firma(db, contrato, str(ruta))
    return contrato


def ruta_firmado(db, contrato_id, user) -> str:
    contrato = _obtener_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    if not contrato.url_firmado or not Path(contrato.url_firmado).exists():
        raise HTTPException(status_code=404, detail="Aún no se ha subido el contrato firmado")
    return contrato.url_firmado


def resumen(db, contrato_id, user):
    contrato = _obtener_o_404(db, contrato_id)
    require_owner_or_admin(user, contrato.usuario_id)
    return crud.resumen_contrato(contrato)


def cambiar_estado(db, contrato_id, nuevo_estado: str):
    contrato = _obtener_o_404(db, contrato_id)
    crud.cambiar_estado_contrato(db, contrato, nuevo_estado)
    if contrato.tipo == "Renta" and nuevo_estado in ("finalizado", "cancelado"):
        try:
            liberar_inmueble_renta(contrato.inmueble_id)
        except Exception as e:
            raise HTTPException(status_code=502,
                detail=f"Estado actualizado pero no se pudo liberar el inmueble: {e}")
    return contrato


def validar_documento(db, contrato_id, datos):
    contrato = _obtener_o_404(db, contrato_id)
    if not contrato.url_firmado:
        raise HTTPException(status_code=409, detail="El contrato aún no tiene documento firmado para validar")
    if not datos.aprobado and not (datos.motivo or "").strip():
        raise HTTPException(status_code=422, detail="Indica el motivo del rechazo")
    crud.validar_documento(db, contrato, datos.aprobado, datos.motivo)
    if datos.aprobado and contrato.tipo == "Venta":
        try:
            property_client.set_estado_inmueble(contrato.inmueble_id, "vendido", system_token())
        except Exception as e:
            raise HTTPException(status_code=502,
                detail=f"Documento aprobado pero no se pudo marcar el inmueble como vendido: {e}")
    return contrato


def cerrar_renta(db, contrato_id, nuevo_estado: str):
    contrato = _obtener_o_404(db, contrato_id)
    crud.cambiar_estado_contrato(db, contrato, nuevo_estado)
    try:
        liberar_inmueble_renta(contrato.inmueble_id)
    except Exception as e:
        raise HTTPException(status_code=502,
            detail=f"Renta cerrada pero no se pudo liberar el inmueble: {e}")
    return contrato
