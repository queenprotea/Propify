from fastapi import FastAPI, Depends, Request, status
from sqlalchemy.orm import Session

import schemas
from database import get_db
from services import pago_service


app = FastAPI(
    title="Payment Service",
    description="Integración con Stripe para contratos de Venta y Renta",
    version="1.0.0",
)


@app.post("/api/pagos/iniciar", response_model=schemas.RespuestaSesion,
          status_code=status.HTTP_201_CREATED,
          summary="Inicia el flujo de pago y devuelve la URL de Stripe")
def iniciar_pago(payload: schemas.IniciarPago, db: Session = Depends(get_db)):
    return pago_service.iniciar_pago(db, payload)


@app.post("/api/pagos/webhook", status_code=status.HTTP_200_OK,
          summary="Endpoint que Stripe llama para notificar resultados")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    return pago_service.procesar_webhook(db, payload, sig_header)


@app.get("/api/pagos/{pago_id}", response_model=schemas.EstadoPago,
         summary="Consultar el estado actual de un pago")
def obtener_estado_pago(pago_id: int, db: Session = Depends(get_db)):
    return pago_service.estado_pago(db, pago_id)
