from __future__ import annotations

from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import models, schemas


#  CONTRATOS

def crear_contrato(db: Session, datos: schemas.ContratoCreate, contrato_padre_id=None) -> models.Contrato:
    campos = datos.model_dump()
    clausula_ids = campos.pop("clausula_ids", []) or []
    contrato = models.Contrato(**campos, contrato_padre_id=contrato_padre_id)
    db.add(contrato)
    db.commit()
    db.refresh(contrato)

    # Folio legible para el usuario (no el id interno).
    anio = (contrato.fecha_generacion or datetime.utcnow()).year
    contrato.folio = f"CTR-{anio}-{contrato.id:05d}"
    db.commit()

    # Copiar al contrato las cláusulas elegidas del catálogo.
    copiar_clausulas_a_contrato(db, contrato, clausula_ids)

    # Para contratos de RENTA se genera el calendario mensual de pagos.
    if contrato.tipo == "Renta":
        _generar_calendario_renta(db, contrato)
    db.refresh(contrato)
    return contrato


# ─────────────────────────  CATÁLOGO DE CLÁUSULAS  ─────────────────────────

def _orden_numero(numero: str):
    """Ordena '2.10' después de '2.2' tratando cada segmento como entero."""
    try:
        return [int(x) for x in (numero or "").split(".") if x != ""]
    except ValueError:
        return [0]


def listar_clausulas_catalogo(db: Session):
    filas = db.query(models.ClausulaCatalogo).all()
    return sorted(filas, key=lambda c: _orden_numero(c.numero))


def crear_clausula_catalogo(db: Session, datos: schemas.ClausulaCatalogoCreate):
    existe = db.query(models.ClausulaCatalogo).filter(
        models.ClausulaCatalogo.numero == datos.numero).first()
    if existe:
        raise ValueError(f"Ya existe una cláusula con el número {datos.numero}")
    fila = models.ClausulaCatalogo(numero=datos.numero, titulo=datos.titulo, texto=datos.texto)
    db.add(fila)
    db.commit()
    db.refresh(fila)
    return fila


def eliminar_clausula_catalogo(db: Session, clausula_id: int) -> bool:
    fila = db.query(models.ClausulaCatalogo).filter(models.ClausulaCatalogo.id == clausula_id).first()
    if not fila:
        return False
    db.delete(fila)
    db.commit()
    return True


def copiar_clausulas_a_contrato(db: Session, contrato: models.Contrato, ids):
    if not ids:
        return
    filas = db.query(models.ClausulaCatalogo).filter(models.ClausulaCatalogo.id.in_(ids)).all()
    for c in sorted(filas, key=lambda x: _orden_numero(x.numero)):
        db.add(models.Clausula(numero=c.numero, titulo=c.titulo, descripcion=c.texto, id_contrato=contrato.id))
    db.commit()


def listar_contratos(db: Session, estado=None, tipo=None, usuario_id=None,
                     inmueble_id=None, fecha_desde=None, fecha_hasta=None,
                     skip: int = 0, limit: int = 200):
    q = db.query(models.Contrato)
    if estado:
        q = q.filter(models.Contrato.estado == estado)
    if tipo:
        q = q.filter(models.Contrato.tipo == tipo)
    if usuario_id:
        q = q.filter(models.Contrato.usuario_id == usuario_id)
    if inmueble_id:
        q = q.filter(models.Contrato.inmueble_id == inmueble_id)
    if fecha_desde:
        q = q.filter(models.Contrato.fecha_inicio >= fecha_desde)
    if fecha_hasta:
        q = q.filter(models.Contrato.fecha_inicio <= fecha_hasta)
    contratos = q.order_by(models.Contrato.id.desc()).offset(skip).limit(limit).all()
    for c in contratos:
        _actualizar_vencidos(db, c)
    return contratos


def cambiar_estado_contrato(db: Session, contrato: models.Contrato, nuevo_estado: str):
    contrato.estado = nuevo_estado
    db.commit()
    db.refresh(contrato)
    return contrato


def validar_documento(db: Session, contrato: models.Contrato, aprobado: bool, motivo=None):
    contrato.estado_documento = "aprobado" if aprobado else "rechazado"
    contrato.motivo_rechazo = None if aprobado else motivo
    # Al aprobar la documentación firmada, el contrato pasa a 'firmado'.
    if aprobado and contrato.estado in ("pendiente_de_firma", "borrador"):
        contrato.estado = "firmado"
    db.commit()
    db.refresh(contrato)
    return contrato


def _generar_calendario_renta(db: Session, contrato: models.Contrato) -> None:
    """Crea una mensualidad pendiente por cada mes entre inicio y fin."""
    if not contrato.fecha_fin:
        # Sin fecha fin no se puede acotar el calendario; se crea 1 mensualidad.
        meses = 1
    else:
        delta = relativedelta(contrato.fecha_fin, contrato.fecha_inicio)
        meses = delta.years * 12 + delta.months
        if meses < 1:
            meses = 1

    for i in range(meses):
        cuota = models.Pago(
            monto=contrato.monto,
            estado="pendiente",
            numero_cuota=i + 1,
            fecha_vencimiento=contrato.fecha_inicio + relativedelta(months=i),
            contrato_id=contrato.id,
        )
        db.add(cuota)
    db.commit()


def obtener_contrato(db: Session, contrato_id: int) -> models.Contrato | None:
    contrato = db.query(models.Contrato).filter(models.Contrato.id == contrato_id).first()
    if contrato:
        _actualizar_vencidos(db, contrato)
    return contrato


def obtener_contratos_por_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 50):
    return (
        db.query(models.Contrato)
        .filter(models.Contrato.usuario_id == usuario_id)
        .offset(skip).limit(limit).all()
    )


def obtener_contratos_por_inmueble(db: Session, inmueble_id: int, skip: int = 0, limit: int = 50):
    return (
        db.query(models.Contrato)
        .filter(models.Contrato.inmueble_id == inmueble_id)
        .offset(skip).limit(limit).all()
    )


def registrar_descarga(db: Session, contrato: models.Contrato) -> None:
    contrato.fecha_descarga = datetime.utcnow()
    db.commit()


def registrar_firma(db: Session, contrato: models.Contrato, url_firmado: str) -> None:
    contrato.url_firmado = url_firmado
    contrato.fecha_firma_subida = datetime.utcnow()
    db.commit()
    db.refresh(contrato)


#  PAGOS

def _actualizar_vencidos(db: Session, contrato: models.Contrato) -> None:
    """Marca como 'vencido' las mensualidades pendientes cuya fecha ya pasó."""
    hoy = date.today()
    cambio = False
    for p in contrato.pagos:
        if p.estado == "pendiente" and p.fecha_vencimiento and p.fecha_vencimiento < hoy:
            p.estado = "vencido"
            cambio = True
    if cambio:
        db.commit()


def resumen_venta(contrato: models.Contrato) -> schemas.ResumenVenta:
    total = Decimal(contrato.monto)
    pagado = sum((Decimal(p.monto) for p in contrato.pagos if p.estado == "pagado"), Decimal(0))
    saldo = total - pagado
    if saldo < 0:
        saldo = Decimal(0)
    pct = float(pagado / total * 100) if total > 0 else 0.0
    return schemas.ResumenVenta(
        contrato_id=contrato.id,
        monto_total=total,
        total_pagado=pagado,
        saldo_pendiente=saldo,
        porcentaje_cubierto=round(pct, 2),
        liquidado=saldo == 0,
    )


def resumen_contrato(contrato: models.Contrato) -> schemas.ResumenContrato:
    """Resumen económico para Venta o Renta (total, pagado, saldo, %, vencimientos)."""
    if contrato.tipo == "Renta":
        cuotas = list(contrato.pagos)
        total = sum((Decimal(p.monto) for p in cuotas), Decimal(0))
        pagado = sum((Decimal(p.monto) for p in cuotas if p.estado == "pagado"), Decimal(0))
        pendientes = [p for p in cuotas if p.estado in ("pendiente", "vencido")]
        saldo = sum((Decimal(p.monto) for p in pendientes), Decimal(0))
        venc = sorted([p.fecha_vencimiento for p in pendientes if p.fecha_vencimiento])
        proximo = venc[0] if venc else None
        n_pend = len(pendientes)
    else:
        total = Decimal(contrato.monto)
        pagado = sum((Decimal(p.monto) for p in contrato.pagos if p.estado == "pagado"), Decimal(0))
        saldo = total - pagado
        if saldo < 0:
            saldo = Decimal(0)
        proximo = None
        n_pend = 0
    pct = float(pagado / total * 100) if total > 0 else 0.0
    return schemas.ResumenContrato(
        contrato_id=contrato.id, tipo=contrato.tipo,
        monto_total=total, total_pagado=pagado, saldo_pendiente=saldo,
        porcentaje_cubierto=round(pct, 2), liquidado=saldo == 0,
        cuotas_pendientes=n_pend, proximo_vencimiento=proximo,
    )


def registrar_pago(db: Session, contrato: models.Contrato, datos: schemas.PagoCreate,
                   usuario_id=None, ip=None, stripe_payment_intent=None) -> models.Pago:
    """
    Renta: liquida la mensualidad pendiente/vencida más antigua.
    Venta: registra un pago (total o parcial) y liquida el contrato si el saldo llega a 0.
    """
    if contrato.estado not in ("activo",):
        raise ValueError(f"El contrato está '{contrato.estado}' y no acepta pagos")

    if contrato.tipo == "Renta":
        cuota = (
            db.query(models.Pago)
            .filter(
                models.Pago.contrato_id == contrato.id,
                models.Pago.estado.in_(["pendiente", "vencido"]),
            )
            .order_by(models.Pago.numero_cuota.asc())
            .first()
        )
        if not cuota:
            raise ValueError("No hay mensualidades pendientes en este contrato de renta")
        cuota.estado = "pagado"
        cuota.metodo = datos.metodo
        cuota.fecha = datetime.utcnow()
        cuota.usuario_id = usuario_id
        cuota.ip = ip
        cuota.stripe_payment_intent = stripe_payment_intent
        db.commit()
        db.refresh(cuota)
        return cuota

    # Venta: pago total o parcial
    resumen = resumen_venta(contrato)
    if Decimal(datos.monto) > resumen.saldo_pendiente:
        raise ValueError(
            f"El monto {datos.monto} supera el saldo pendiente ({resumen.saldo_pendiente})"
        )
    pago = models.Pago(
        monto=datos.monto, metodo=datos.metodo, estado="pagado", fecha=datetime.utcnow(),
        contrato_id=contrato.id, usuario_id=usuario_id, ip=ip,
        stripe_payment_intent=stripe_payment_intent,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)

    # ¿Saldo cero? → liquidar contrato
    if resumen_venta(contrato).liquidado:
        contrato.estado = "liquidado"
        db.commit()

    return pago


# ─────────────────────────  SOLICITUDES DE RENTA  ─────────────────────────

def _meses_entre(inicio, fin) -> int:
    d = relativedelta(fin, inicio)
    return max(d.years * 12 + d.months, 1)


def crear_solicitud(db: Session, usuario_id: int, datos: schemas.SolicitudCreate) -> models.SolicitudRenta:
    tipo = datos.tipo_operacion.value
    duracion = None
    if tipo == "renta":
        duracion = datos.duracion_meses or _meses_entre(datos.fecha_inicio, datos.fecha_fin)
    sol = models.SolicitudRenta(
        usuario_id=usuario_id, inmueble_id=datos.inmueble_id, mensaje=datos.mensaje, estado="pendiente",
        tipo_operacion=tipo, fecha_inicio=datos.fecha_inicio, fecha_fin=datos.fecha_fin, duracion_meses=duracion,
    )
    db.add(sol)
    db.commit()
    db.refresh(sol)
    return sol


def obtener_solicitud(db: Session, solicitud_id: int):
    return db.query(models.SolicitudRenta).filter(models.SolicitudRenta.id == solicitud_id).first()


def solicitudes_por_usuario(db: Session, usuario_id: int):
    return (
        db.query(models.SolicitudRenta)
        .filter(models.SolicitudRenta.usuario_id == usuario_id)
        .order_by(models.SolicitudRenta.fecha_solicitud.desc()).all()
    )


def todas_solicitudes(db: Session):
    return db.query(models.SolicitudRenta).order_by(models.SolicitudRenta.fecha_solicitud.desc()).all()


def cambiar_estado_solicitud(db: Session, sol: models.SolicitudRenta, nuevo_estado: str):
    sol.estado = nuevo_estado
    db.commit()
    db.refresh(sol)
    return sol


# ─────────────────────────  COMPROBANTES  ─────────────────────────

def crear_comprobante(db: Session, contrato_id: int, usuario_id: int, url: str, pago_id=None):
    comp = models.Comprobante(
        contrato_id=contrato_id, usuario_id=usuario_id, url_archivo=url, pago_id=pago_id,
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


def comprobantes_por_contrato(db: Session, contrato_id: int):
    return (
        db.query(models.Comprobante)
        .filter(models.Comprobante.contrato_id == contrato_id)
        .order_by(models.Comprobante.fecha_carga.desc()).all()
    )


def obtener_comprobante(db: Session, comprobante_id: int):
    return db.query(models.Comprobante).filter(models.Comprobante.id == comprobante_id).first()


def crear_pago(db: Session, contrato_id: int, datos, stripe_session_id: str | None = None):
    """Compatibilidad con el flujo de Stripe (pago 'pendiente')."""
    pago = models.Pago(
        monto=datos.monto,
        metodo=getattr(datos, "metodo", "stripe"),
        estado="pendiente",
        fecha=datetime.utcnow(),
        stripe_session_id=stripe_session_id,
        contrato_id=contrato_id,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)
    return pago
