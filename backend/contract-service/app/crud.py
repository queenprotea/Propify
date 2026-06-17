from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import models, schemas


#  CONTRATOS

def crear_contrato(db: Session, datos: schemas.ContratoCreate, contrato_padre_id=None) -> models.Contrato:
    campos = datos.model_dump()
    clausula_ids = campos.pop("clausula_ids", []) or []
    clausulas_nuevas = campos.pop("clausulas_nuevas", []) or []
    contrato = models.Contrato(**campos, contrato_padre_id=contrato_padre_id)
    db.add(contrato)
    db.commit()
    db.refresh(contrato)

    # Folio legible para el usuario (no el id interno).
    anio = (contrato.fecha_generacion or datetime.utcnow()).year
    contrato.folio = f"CTR-{anio}-{contrato.id:05d}"
    db.commit()

    # Copiar al contrato las cláusulas elegidas del catálogo + las escritas al momento.
    copiar_clausulas_a_contrato(db, contrato, clausula_ids)
    agregar_clausulas_nuevas(db, contrato, clausulas_nuevas)

    # Para contratos de RENTA se genera el calendario mensual de pagos.
    if contrato.tipo == "Renta":
        _generar_calendario_renta(db, contrato)
    # Venta a plazos: si se pactaron varias mensualidades, se genera su calendario.
    elif contrato.tipo == "Venta" and (contrato.meses_plazo or 1) > 1:
        _generar_calendario_venta(db, contrato, contrato.meses_plazo)
    db.refresh(contrato)
    return contrato


def _generar_calendario_venta(db: Session, contrato: models.Contrato, meses: int) -> None:
    """Divide el precio de venta en `meses` mensualidades (la última ajusta el redondeo)."""
    total = Decimal(contrato.monto)
    cuota = (total / meses).quantize(Decimal("0.01"))
    base = contrato.fecha_inicio or datetime.utcnow().date()
    acumulado = Decimal("0.00")
    for i in range(meses):
        monto = cuota if i < meses - 1 else (total - acumulado)
        acumulado += monto
        db.add(models.Pago(
            monto=monto, estado="pendiente", numero_cuota=i + 1,
            fecha_vencimiento=base + relativedelta(months=i, day=31),
            contrato_id=contrato.id,
        ))
    db.commit()


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


def agregar_clausulas_nuevas(db: Session, contrato: models.Contrato, nuevas):
    """Cláusulas escritas directamente al generar el contrato (no provienen del catálogo)."""
    if not nuevas:
        return
    for c in nuevas:
        numero = c.get("numero") if isinstance(c, dict) else c.numero
        titulo = c.get("titulo") if isinstance(c, dict) else c.titulo
        texto = c.get("texto") if isinstance(c, dict) else c.texto
        db.add(models.Clausula(numero=numero, titulo=titulo, descripcion=texto, id_contrato=contrato.id))
    db.commit()


def listar_contratos(db: Session, estado=None, tipo=None, usuario_id=None,
                     inmueble_id=None, fecha_desde=None, fecha_hasta=None,
                     folio=None, skip: int = 0, limit: int = 200):
    q = db.query(models.Contrato)
    if estado:
        q = q.filter(models.Contrato.estado == estado)
    if tipo:
        q = q.filter(models.Contrato.tipo == tipo)
    if folio:
        q = q.filter(models.Contrato.folio.ilike(f"%{folio}%"))
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
        # La mensualidad vence al FINAL del mes correspondiente (fecha de corte),
        # no el día de inicio: así una renta del mes en curso no aparece vencida.
        vencimiento = contrato.fecha_inicio + relativedelta(months=i, day=31)
        cuota = models.Pago(
            monto=contrato.monto,
            estado="pendiente",
            numero_cuota=i + 1,
            fecha_vencimiento=vencimiento,
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
    # El documento (re)subido vuelve a quedar pendiente de validación; se limpia el
    # motivo de un rechazo previo para que el admin pueda aprobarlo o rechazarlo de nuevo.
    contrato.estado_documento = "pendiente"
    contrato.motivo_rechazo = None
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


# Estados de pago que cuentan como "pendiente de cubrir" en una renta.
_PAGOS_NO_CUBIERTOS = ("pendiente", "vencido", "pendiente_de_verificacion")


def renta_totalmente_cubierta(contrato: models.Contrato) -> bool:
    """True si la renta tiene al menos una mensualidad y ninguna queda por cubrir."""
    cuotas = list(contrato.pagos or [])
    if not cuotas:
        return False
    return all(p.estado not in _PAGOS_NO_CUBIERTOS for p in cuotas)


def rentas_para_autofinalizar(db: Session) -> list[models.Contrato]:
    """Rentas ACTIVAS cuyo plazo ya venció y cuyos pagos están todos cubiertos.

    No modifica nada: solo identifica las candidatas. La transición de estado y la
    liberación del inmueble las realiza la capa de servicio (necesita property-service).
    """
    hoy = date.today()
    activas = (
        db.query(models.Contrato)
        .filter(
            models.Contrato.tipo == "Renta",
            models.Contrato.estado == "activo",
            models.Contrato.fecha_fin.isnot(None),
            models.Contrato.fecha_fin <= hoy,
        )
        .all()
    )
    for c in activas:
        _actualizar_vencidos(db, c)
    return [c for c in activas if renta_totalmente_cubierta(c)]


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
        # Venta: total = precio; pagado = suma de pagos cubiertos (cuotas + abonos).
        total = Decimal(contrato.monto)
        pagado = sum((Decimal(p.monto) for p in contrato.pagos if p.estado == "pagado"), Decimal(0))
        saldo = total - pagado
        if saldo < 0:
            saldo = Decimal(0)
        # Venta a plazos: hay mensualidades con número de cuota → reportar pendientes/vencimiento.
        cuotas_plan = [p for p in contrato.pagos if p.numero_cuota and p.estado in ("pendiente", "vencido")]
        venc = sorted([p.fecha_vencimiento for p in cuotas_plan if p.fecha_vencimiento])
        proximo = venc[0] if venc else None
        n_pend = len(cuotas_plan)
    pct = float(pagado / total * 100) if total > 0 else 0.0
    return schemas.ResumenContrato(
        contrato_id=contrato.id, tipo=contrato.tipo,
        monto_total=total, total_pagado=pagado, saldo_pendiente=saldo,
        porcentaje_cubierto=round(pct, 2), liquidado=saldo == 0,
        cuotas_pendientes=n_pend, proximo_vencimiento=proximo,
    )


def _metodo_str(metodo) -> str:
    return metodo.value if hasattr(metodo, "value") else str(metodo)


def _saldo_comprometido(contrato: models.Contrato) -> Decimal:
    """Saldo de venta descontando lo pagado y lo que está pendiente de verificación."""
    total = Decimal(contrato.monto)
    comprometido = sum(
        (Decimal(p.monto) for p in contrato.pagos
         if p.estado in ("pagado", "pendiente_de_verificacion")),
        Decimal(0),
    )
    saldo = total - comprometido
    return saldo if saldo > 0 else Decimal(0)


def registrar_pago(db: Session, contrato: models.Contrato, datos: schemas.PagoCreate,
                   usuario_id=None, ip=None, stripe_payment_intent=None,
                   confirmado=False) -> models.Pago:
    """
    Registra un pago. Los pagos manuales (efectivo/transferencia) quedan en
    'pendiente_de_verificacion' hasta que el administrador los apruebe; solo
    Stripe confirmado (confirmado=True) entra directamente como 'pagado'.

    Renta: ocupa la mensualidad pendiente/vencida más antigua.
    Venta: registra un pago (total o parcial); liquida el contrato al aprobarse.
    """
    if contrato.estado not in ("activo",):
        raise ValueError(f"El contrato está '{contrato.estado}' y no acepta pagos")

    estado_inicial = "pagado" if confirmado else "pendiente_de_verificacion"
    metodo = _metodo_str(datos.metodo)

    numero_cuota = getattr(datos, "numero_cuota", None)
    # Pago de una mensualidad concreta: renta siempre, o venta a plazos cuando se indica cuota.
    if contrato.tipo == "Renta" or numero_cuota is not None:
        q = (
            db.query(models.Pago)
            .filter(
                models.Pago.contrato_id == contrato.id,
                models.Pago.estado.in_(["pendiente", "vencido"]),
            )
        )
        if numero_cuota is not None:
            # Mensualidad específica elegida por el usuario (puede ser una atrasada).
            cuota = q.filter(models.Pago.numero_cuota == numero_cuota).first()
            if not cuota:
                raise ValueError(f"La mensualidad #{numero_cuota} no existe o ya fue cubierta")
        else:
            cuota = q.order_by(models.Pago.numero_cuota.asc()).first()
        if not cuota:
            raise ValueError("No hay mensualidades pendientes en este contrato")
        cuota.estado = estado_inicial
        cuota.metodo = metodo
        cuota.fecha = datetime.utcnow()
        cuota.usuario_id = usuario_id
        cuota.ip = ip
        cuota.stripe_payment_intent = stripe_payment_intent
        db.commit()
        db.refresh(cuota)
        # Venta liquidada al cubrir su última mensualidad (pago confirmado).
        if confirmado and contrato.tipo == "Venta" and resumen_venta(contrato).liquidado:
            contrato.estado = "liquidado"
            db.commit()
        return cuota

    # Venta: abono libre a capital (no atado a una mensualidad).
    if Decimal(datos.monto) > _saldo_comprometido(contrato):
        raise ValueError(
            f"El monto {datos.monto} supera el saldo disponible ({_saldo_comprometido(contrato)})"
        )
    pago = models.Pago(
        monto=datos.monto, metodo=metodo, estado=estado_inicial, fecha=datetime.utcnow(),
        contrato_id=contrato.id, usuario_id=usuario_id, ip=ip,
        stripe_payment_intent=stripe_payment_intent,
    )
    db.add(pago)
    db.commit()
    db.refresh(pago)

    # Solo un pago confirmado puede liquidar el contrato.
    if confirmado and resumen_venta(contrato).liquidado:
        contrato.estado = "liquidado"
        db.commit()

    return pago


class _PagoStripe:
    """Adaptador mínimo para reutilizar registrar_pago con método 'stripe'."""
    def __init__(self, monto, numero_cuota=None):
        self.monto = monto
        self.metodo = "stripe"
        self.numero_cuota = numero_cuota


def _registrar_pago_confirmado_stripe(db, contrato, monto, usuario_id, ip, intent_id, numero_cuota=None):
    """Registra un pago de Stripe ya confirmado (entra como 'pagado')."""
    return registrar_pago(db, contrato, _PagoStripe(monto, numero_cuota),
                          usuario_id=usuario_id, ip=ip,
                          stripe_payment_intent=intent_id, confirmado=True)


def verificar_pago(db: Session, pago: models.Pago, aprobado: bool, motivo=None):
    """El administrador aprueba (->pagado) o rechaza (->rechazado/pendiente) un pago manual."""
    contrato = pago.contrato
    if pago.estado != "pendiente_de_verificacion":
        raise ValueError("Este pago no está pendiente de verificación")

    if aprobado:
        pago.estado = "pagado"
        pago.fecha = datetime.utcnow()
        db.commit()
        db.refresh(pago)
        # Venta liquidada al aprobar el pago que cubre el saldo.
        if contrato.tipo == "Venta" and resumen_venta(contrato).liquidado:
            contrato.estado = "liquidado"
            db.commit()
    else:
        if contrato.tipo == "Renta":
            # La mensualidad vuelve a quedar disponible para pago.
            pago.estado = "pendiente"
            pago.metodo = None
            pago.fecha = None
        else:
            pago.estado = "rechazado"
        db.commit()
        db.refresh(pago)
    return pago


#  SOLICITUDES DE RENTA

def _meses_entre(inicio, fin) -> int:
    d = relativedelta(fin, inicio)
    return max(d.years * 12 + d.months, 1)


def existe_solicitud_activa(db: Session, usuario_id: int, inmueble_id: int, tipo: str) -> bool:

    return (
        db.query(models.SolicitudRenta)
        .outerjoin(models.Contrato, models.SolicitudRenta.contrato_id == models.Contrato.id)
        .filter(
            models.SolicitudRenta.usuario_id == usuario_id,
            models.SolicitudRenta.inmueble_id == inmueble_id,
            models.SolicitudRenta.tipo_operacion == tipo,
            models.SolicitudRenta.estado.in_(["pendiente", "en revision", "aprobada"]),
            or_(
                models.SolicitudRenta.contrato_id.is_(None),
                models.Contrato.estado.notin_(["finalizado", "cancelado"]),
            ),
        )
        .first()
        is not None
    )


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


#  COMPROBANTES

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
    """Compatibilidad con el flujo de Stripe """
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
