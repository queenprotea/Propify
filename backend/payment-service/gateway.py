
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# Venta: pago unico / abono
def crear_sesion_venta(
    monto: float,
    contrato_id: int,
    moneda: str,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:
    #Checkout Session de pago único.Cada llamada puede representar el total o un abono parcial del contrato.

    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": moneda,
                "product_data": {
                    "name": f"Pago contrato de Venta #{contrato_id}",
                    "description": "Pago único / abono",
                },
                "unit_amount": _a_centavos(monto),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "contrato_id": str(contrato_id),
            "tipo_contrato": "Venta",
        },
    )


# Renta: mensualidad

def crear_sesion_renta(
    monto: float,
    contrato_id: int,
    moneda: str,
    success_url: str,
    cancel_url: str,
) -> stripe.checkout.Session:

    #Genera una Checkout Session para una mensualidad de renta.

    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": moneda,
                "product_data": {
                    "name": f"Mensualidad — Contrato Renta #{contrato_id}",
                    "description": "Pago mensual de arrendamiento",
                },
                "unit_amount": _a_centavos(monto),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "contrato_id": str(contrato_id),
            "tipo_contrato": "Renta",
        },
    )


# Router principal

def crear_sesion(
    tipo_contrato: str,
    monto: float,
    contrato_id: int,
    moneda: str = "mxn",
    success_url: str = "https://mi-sitio.com/pago-exitoso",
    cancel_url: str  = "https://mi-sitio.com/pago-cancelado", #pjo recuerda cambiarlos
) -> stripe.checkout.Session:
    #Despacha al flujo correcto según el tipo de contrato
    if tipo_contrato == "Venta":
        return crear_sesion_venta(monto, contrato_id, moneda, success_url, cancel_url)
    elif tipo_contrato == "Renta":
        return crear_sesion_renta(monto, contrato_id, moneda, success_url, cancel_url)
    else:
        raise ValueError(f"Tipo de contrato desconocido: {tipo_contrato}")


# Utilidades
def _a_centavos(monto: float) -> int:
    #Convierte pesos MXN a centavos (Stripe trabaja en la unidad menor)
    return int(round(monto * 100))
