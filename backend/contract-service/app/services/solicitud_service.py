"""Lógica de negocio de solicitudes de renta/venta del cliente."""
from datetime import date, timedelta

from fastapi import HTTPException

import crud
import schemas
import property_client
from security import require_owner_or_admin
from services import contrato_service


def _solicitud_o_404(db, solicitud_id):
    sol = crud.obtener_solicitud(db, solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return sol


def crear(db, datos, user):
    if user.get("is_admin"):
        raise HTTPException(status_code=403,
            detail="Un administrador no puede generar solicitudes de cliente.")
    tipo = datos.tipo_operacion.value
    if crud.existe_solicitud_activa(db, int(user["sub"]), datos.inmueble_id, tipo):
        raise HTTPException(status_code=409,
            detail=f"Ya tienes una solicitud de {tipo} registrada para este inmueble.")
    if tipo == "renta":
        if not datos.fecha_inicio or not datos.fecha_fin:
            raise HTTPException(status_code=422, detail="La renta requiere fecha de inicio y de fin")
        # Tolerancia de 1 día por zona horaria entre cliente y servidor (UTC).
        if datos.fecha_inicio < date.today() - timedelta(days=1):
            raise HTTPException(status_code=422, detail="La fecha de inicio no puede ser anterior a hoy")
        if datos.fecha_fin <= datos.fecha_inicio:
            raise HTTPException(status_code=422, detail="La fecha de fin debe ser posterior a la de inicio")

    inm = property_client.get_inmueble(datos.inmueble_id)
    if not inm:
        raise HTTPException(status_code=404, detail="El inmueble no existe")
    estado_actual = property_client.estado_inmueble(inm)
    esperado = "en renta" if tipo == "renta" else "en venta"
    if estado_actual != esperado:
        raise HTTPException(status_code=409,
            detail=f"El inmueble no está disponible para {tipo} (estado: {estado_actual})")

    return crud.crear_solicitud(db, int(user["sub"]), datos)


def listar_todas(db):
    return crud.todas_solicitudes(db)


def por_usuario(db, usuario_id, user):
    require_owner_or_admin(user, usuario_id)
    return crud.solicitudes_por_usuario(db, usuario_id)


def obtener(db, solicitud_id, user):
    sol = _solicitud_o_404(db, solicitud_id)
    require_owner_or_admin(user, sol.usuario_id)
    return sol


def cambiar_estado(db, solicitud_id, nuevo_estado):
    sol = _solicitud_o_404(db, solicitud_id)
    crud.cambiar_estado_solicitud(db, sol, nuevo_estado)
    return sol


def cancelar(db, solicitud_id, user):
    sol = _solicitud_o_404(db, solicitud_id)
    require_owner_or_admin(user, sol.usuario_id)
    if sol.estado not in ("pendiente", "en revision"):
        raise HTTPException(status_code=409, detail="La solicitud ya no se puede cancelar")
    crud.cambiar_estado_solicitud(db, sol, "cancelada")
    return sol


def generar_contrato_renta(db, solicitud_id, datos, auth_header: str = ""):
    sol = _solicitud_o_404(db, solicitud_id)
    if sol.estado != "aprobada":
        raise HTTPException(status_code=409, detail="La solicitud debe estar APROBADA para generar el contrato")
    if sol.contrato_id:
        raise HTTPException(status_code=409, detail="La solicitud ya tiene un contrato generado")
    if sol.tipo_operacion != "renta":
        raise HTTPException(status_code=422, detail="Esta solicitud es de compra; use el contrato de venta")

    fecha_inicio = datos.fecha_inicio or sol.fecha_inicio
    fecha_fin = datos.fecha_fin or sol.fecha_fin
    if not fecha_inicio or not fecha_fin:
        raise HTTPException(status_code=422, detail="Faltan fechas de inicio/fin del contrato")
    if fecha_fin <= fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha de fin debe ser posterior a la de inicio")

    contrato = crud.crear_contrato(db, schemas.ContratoCreate(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        tipo=schemas.TipoContrato.renta, monto=datos.monto, condiciones=datos.condiciones,
        usuario_id=sol.usuario_id, inmueble_id=sol.inmueble_id,
        clausula_ids=datos.clausula_ids, clausulas_nuevas=datos.clausulas_nuevas,
    ))
    contrato_service.generar_y_guardar_pdf(db, contrato, auth_header)

    sol.contrato_id = contrato.id
    db.commit()
    try:
        property_client.set_estado_inmueble(sol.inmueble_id, "rentado", auth_header)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Contrato creado pero no se pudo actualizar el inmueble: {e}")
    return contrato


def generar_contrato_venta(db, solicitud_id, datos, auth_header: str = ""):
    sol = _solicitud_o_404(db, solicitud_id)
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
    contrato_service.generar_y_guardar_pdf(db, contrato, auth_header)

    sol.contrato_id = contrato.id
    db.commit()
    try:
        property_client.set_estado_inmueble(sol.inmueble_id, "reservado", auth_header)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Contrato creado pero no se pudo actualizar el inmueble: {e}")
    return contrato
