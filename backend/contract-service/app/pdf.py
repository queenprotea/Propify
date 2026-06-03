"""Generación de contratos en PDF, completos y diferenciados por operación.

Se generan dos formatos profesionales (renta / venta) con todas las cláusulas,
usando información real de cliente, inmueble, pagos y fechas. Listos para
exportación/impresión y revisión jurídica posterior.
"""
from io import BytesIO
from datetime import datetime, date
from decimal import Decimal

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# La inmobiliaria actúa como ARRENDADOR / VENDEDOR (modelo agencia).
EMPRESA = "Inmuebles a tu Alcance, S.A. de C.V."
EMPRESA_RFC = "IAA000000XXX"
EMPRESA_DOM = "Av. Principal 100, Col. Centro, Ciudad de México, C.P. 06000"


# ---------- utilidades ----------
def _money(v):
    try:
        return f"$ {Decimal(v):,.2f} MXN"
    except Exception:
        return f"$ {v} MXN"


def _fecha(v):
    if not v:
        return "—"
    if isinstance(v, (date, datetime)):
        return v.strftime("%d/%m/%Y")
    return str(v)


def _persona_cliente(cliente, contrato):
    if cliente:
        return (f"{cliente.get('nombre','')} (correo: {cliente.get('correo','—')}, "
                f"tel: {cliente.get('telefono') or '—'})")
    return f"Cliente con identificador #{contrato.usuario_id}"


def _inmueble_desc(inmueble, ubicacion, contrato):
    if not inmueble:
        return f"Inmueble con identificador #{contrato.inmueble_id}"
    partes = [inmueble.get("titulo", "")]
    if inmueble.get("tipo"):
        partes.append(f"tipo {inmueble['tipo']}")
    dir_ = (ubicacion or {}).get("direccion_completa") if ubicacion else None
    if dir_:
        partes.append(f"ubicado en {dir_}")
    extra = []
    for k, lbl in [("num_recamaras", "recámaras"), ("num_banos", "baños"),
                   ("area_construccion", "m² construcción")]:
        if inmueble.get(k):
            extra.append(f"{inmueble[k]} {lbl}")
    if extra:
        partes.append("(" + ", ".join(extra) + ")")
    return ", ".join(p for p in partes if p)


def _estilos():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Titulo", parent=s["Title"], textColor=colors.HexColor("#4c1d95"), fontSize=18))
    s.add(ParagraphStyle("H", parent=s["Heading2"], textColor=colors.HexColor("#4c1d95"), fontSize=12, spaceBefore=10))
    s.add(ParagraphStyle("Just", parent=s["BodyText"], alignment=TA_JUSTIFY, fontSize=9.5, leading=14))
    s.add(ParagraphStyle("Center", parent=s["BodyText"], alignment=TA_CENTER))
    return s


def _tabla_datos(filas):
    t = Table(filas, colWidths=[5.5 * cm, 10.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0eefb")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8dae5")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _clausulas(st, titulo, items):
    flow = [Paragraph(titulo, st["H"])]
    flow.append(ListFlowable(
        [ListItem(Paragraph(t, st["Just"]), value=i + 1) for i, t in enumerate(items)],
        bulletType="1", leftIndent=14,
    ))
    return flow


def _firmas(st):
    t = Table([["_______________________________", "_______________________________"],
               [EMPRESA, "El Cliente"]], colWidths=[8 * cm, 8 * cm])
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 1), (-1, 1), 4)]))
    return t


# ---------- documento principal ----------
def generar_pdf_contrato(contrato, cliente=None, inmueble=None, ubicacion=None, pagos=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title=f"Contrato {contrato.folio or contrato.id}")
    st = _estilos()
    if contrato.tipo == "Renta":
        elems = _contrato_renta(st, contrato, cliente, inmueble, ubicacion, pagos)
    else:
        elems = _contrato_venta(st, contrato, cliente, inmueble, ubicacion, pagos)
    doc.build(elems)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ---------- CONTRATO DE RENTA (ARRENDAMIENTO) ----------
def _contrato_renta(st, c, cliente, inmueble, ubicacion, pagos):
    e = []
    e.append(Paragraph("CONTRATO DE ARRENDAMIENTO", st["Titulo"]))
    e.append(Paragraph(f"Folio: <b>{c.folio or c.id}</b> &nbsp;·&nbsp; Generado: {_fecha(datetime.utcnow())}", st["Center"]))
    e.append(Spacer(1, 0.4 * cm))

    e.append(Paragraph(
        f"En la Ciudad de México, se celebra el presente <b>Contrato de Arrendamiento</b> entre "
        f"<b>{EMPRESA}</b>, en su carácter de <b>EL ARRENDADOR</b>, y "
        f"<b>{_persona_cliente(cliente, c)}</b>, en su carácter de <b>EL ARRENDATARIO</b>, "
        f"respecto del inmueble: {_inmueble_desc(inmueble, ubicacion, c)}.", st["Just"]))
    e.append(Spacer(1, 0.3 * cm))

    e.append(_tabla_datos([
        ["Arrendador", f"{EMPRESA} · RFC {EMPRESA_RFC} · {EMPRESA_DOM}"],
        ["Arrendatario", _persona_cliente(cliente, c)],
        ["Inmueble", _inmueble_desc(inmueble, ubicacion, c)],
        ["Vigencia", f"Del {_fecha(c.fecha_inicio)} al {_fecha(c.fecha_fin)}"],
        ["Renta mensual", _money(c.monto)],
        ["Forma de pago", "Transferencia, tarjeta (Stripe) o efectivo, según calendario."],
        ["Estado del contrato", c.estado],
    ]))

    if c.condiciones:
        e += [Paragraph("CONDICIONES ESPECIALES", st["H"]), Paragraph(c.condiciones, st["Just"])]

    # Calendario de pagos
    if pagos:
        e.append(Paragraph("CALENDARIO DE PAGOS (FECHAS LÍMITE)", st["H"]))
        filas = [["#", "Fecha límite", "Monto", "Estado"]]
        for p in pagos:
            filas.append([str(p.numero_cuota or "—"), _fecha(p.fecha_vencimiento), _money(p.monto), p.estado])
        t = Table(filas, colWidths=[1.5 * cm, 5 * cm, 5 * cm, 4.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4c1d95")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8dae5")),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

    e += _clausulas(st, "OBLIGACIONES DEL ARRENDADOR", [
        "Entregar el inmueble en condiciones de habitabilidad, limpio y con los servicios funcionando.",
        "Garantizar el uso y goce pacífico del inmueble durante la vigencia del contrato.",
        "Realizar las reparaciones mayores y estructurales que no deriven del mal uso del arrendatario.",
        "Expedir los recibos correspondientes por cada pago recibido.",
    ])
    e += _clausulas(st, "OBLIGACIONES DEL ARRENDATARIO", [
        "Pagar puntualmente la renta mensual en las fechas límite establecidas en el calendario.",
        "Usar el inmueble exclusivamente para el destino pactado y conforme a la ley.",
        "Conservar el inmueble en buen estado y cubrir los servicios a su cargo (agua, luz, gas, internet).",
        "Permitir las inspecciones razonables previa notificación del arrendador.",
        "Restituir el inmueble al término del contrato en las mismas condiciones en que lo recibió, salvo el desgaste normal.",
    ])
    e += _clausulas(st, "PENALIZACIONES", [
        "El atraso en el pago de la renta generará un interés moratorio del 5% mensual sobre el monto vencido.",
        "El incumplimiento reiterado (dos o más mensualidades) faculta al arrendador a rescindir el contrato.",
        "Los daños ocasionados por mal uso serán cubiertos por el arrendatario.",
    ])
    e += _clausulas(st, "TERMINACIÓN ANTICIPADA", [
        "Cualquiera de las partes podrá dar por terminado el contrato mediante aviso por escrito con 30 días de anticipación.",
        "La terminación anticipada por parte del arrendatario podrá causar una penalización equivalente a un mes de renta, salvo pacto en contrario.",
    ])
    e += _clausulas(st, "MANTENIMIENTO", [
        "El mantenimiento menor y la conservación cotidiana corresponden al arrendatario.",
        "El mantenimiento mayor y estructural corresponde al arrendador.",
    ])
    e += _clausulas(st, "USO DEL INMUEBLE", [
        "El inmueble se destinará únicamente al uso pactado; queda prohibido subarrendar sin autorización escrita.",
        "Queda prohibido realizar actividades ilícitas o que alteren el orden y la convivencia.",
    ])

    e.append(Spacer(1, 1 * cm))
    e.append(Paragraph("Leído el presente contrato y enteradas las partes de su contenido y alcance legal, lo firman de conformidad:", st["Just"]))
    e.append(Spacer(1, 1.2 * cm))
    e.append(_firmas(st))
    return e


# ---------- CONTRATO DE COMPRAVENTA ----------
def _contrato_venta(st, c, cliente, inmueble, ubicacion, pagos):
    e = []
    e.append(Paragraph("CONTRATO DE COMPRAVENTA", st["Titulo"]))
    e.append(Paragraph(f"Folio: <b>{c.folio or c.id}</b> &nbsp;·&nbsp; Generado: {_fecha(datetime.utcnow())}", st["Center"]))
    e.append(Spacer(1, 0.4 * cm))

    pagado = sum((Decimal(p.monto) for p in (pagos or []) if p.estado == "pagado"), Decimal(0))
    saldo = Decimal(c.monto) - pagado
    if saldo < 0:
        saldo = Decimal(0)

    e.append(Paragraph(
        f"En la Ciudad de México, se celebra el presente <b>Contrato de Compraventa</b> entre "
        f"<b>{EMPRESA}</b>, en su carácter de <b>EL VENDEDOR</b>, y "
        f"<b>{_persona_cliente(cliente, c)}</b>, en su carácter de <b>EL COMPRADOR</b>, "
        f"respecto del inmueble: {_inmueble_desc(inmueble, ubicacion, c)}.", st["Just"]))
    e.append(Spacer(1, 0.3 * cm))

    e.append(_tabla_datos([
        ["Vendedor", f"{EMPRESA} · RFC {EMPRESA_RFC} · {EMPRESA_DOM}"],
        ["Comprador", _persona_cliente(cliente, c)],
        ["Inmueble", _inmueble_desc(inmueble, ubicacion, c)],
        ["Precio de venta", _money(c.monto)],
        ["Total pagado", _money(pagado)],
        ["Saldo pendiente", _money(saldo)],
        ["Forma de pago", "Pago único o pagos parciales (transferencia, tarjeta o efectivo)."],
        ["Estado del contrato", c.estado],
    ]))

    if c.condiciones:
        e += [Paragraph("CONDICIONES ESPECIALES", st["H"]), Paragraph(c.condiciones, st["Just"])]

    if pagos:
        e.append(Paragraph("PAGOS REGISTRADOS", st["H"]))
        filas = [["Fecha", "Monto", "Método", "Estado"]]
        for p in pagos:
            filas.append([_fecha(p.fecha), _money(p.monto), p.metodo or "—", p.estado])
        t = Table(filas, colWidths=[4.5 * cm, 4.5 * cm, 4 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4c1d95")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8dae5")),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        e.append(t)

    e += _clausulas(st, "CONDICIONES DE ENTREGA", [
        "El vendedor entregará el inmueble libre de gravámenes y al corriente en el pago de servicios y contribuciones.",
        "La posesión se transmitirá una vez cubierto el precio total o conforme a lo pactado para pagos parciales.",
    ])
    e += _clausulas(st, "DECLARACIONES DE LAS PARTES", [
        "El vendedor declara ser legítimo propietario y tener facultades para enajenar el inmueble.",
        "El comprador declara conocer el estado físico y jurídico del inmueble y aceptarlo.",
        "Ambas partes manifiestan que no existe dolo, error ni mala fe en la celebración de este contrato.",
    ])
    e += _clausulas(st, "RESPONSABILIDADES LEGALES", [
        "Los gastos de escrituración, impuestos y derechos correrán por cuenta de quien corresponda conforme a la ley.",
        "El vendedor responde por la evicción y los vicios ocultos en términos de la legislación civil aplicable.",
    ])
    e += _clausulas(st, "CLÁUSULAS DE INCUMPLIMIENTO", [
        "El incumplimiento en el pago faculta al vendedor a exigir el cumplimiento forzoso o la rescisión, con el pago de daños y perjuicios.",
        "El atraso en pagos parciales podrá generar intereses moratorios conforme a lo pactado.",
    ])
    e += _clausulas(st, "CLÁUSULAS DE RESCISIÓN", [
        "Será causa de rescisión el incumplimiento de cualquiera de las obligaciones esenciales aquí pactadas.",
        "En caso de rescisión imputable al comprador, el vendedor podrá retener un porcentaje de los pagos parciales como pena convencional.",
    ])

    e.append(Spacer(1, 1 * cm))
    e.append(Paragraph("Leído el presente contrato y enteradas las partes de su contenido y alcance legal, lo firman de conformidad:", st["Just"]))
    e.append(Spacer(1, 1.2 * cm))
    e.append(_firmas(st))
    return e
