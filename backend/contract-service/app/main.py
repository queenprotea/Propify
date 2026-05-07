from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import models, schemas, crud
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contract Service",
    description="Gestión de Contratos (Venta/Renta) y sus Pagos asociados",
    version="1.0.0",
)



#  CONTRATOS

@app.post(
    "/contratos",
    response_model=schemas.ContratoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un contrato de Venta o Renta",
)
def crear_contrato(datos: schemas.ContratoCreate, db: Session = Depends(get_db)):
    return crud.crear_contrato(db, datos)


@app.get(
    "/contratos/{contrato_id}",
    response_model=schemas.ContratoResponse,
    summary="Obtener contrato por ID (incluye sus pagos)",
)
def obtener_contrato(contrato_id: int, db: Session = Depends(get_db)):
    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato


@app.get(
    "/contratos/usuario/{usuario_id}",
    response_model=List[schemas.ContratoResponse],
    summary="Listar todos los contratos de un usuario",
)
def contratos_por_usuario(
    usuario_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return crud.obtener_contratos_por_usuario(db, usuario_id, skip, limit)


@app.get(
    "/contratos/inmueble/{inmueble_id}",
    response_model=List[schemas.ContratoResponse],
    summary="Listar todos los contratos asociados a un inmueble",
)
def contratos_por_inmueble(
    inmueble_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return crud.obtener_contratos_por_inmueble(db, inmueble_id, skip, limit)


#  PAGOS  (con contrato)


@app.post(
    "/contratos/{contrato_id}/pagos",
    response_model=schemas.PagoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un pago manual sobre un contrato existente",
)
def registrar_pago(
    contrato_id: int,
    datos: schemas.PagoCreate,
    db: Session = Depends(get_db),
):

    contrato = crud.obtener_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(
            status_code=404,
            detail=f"No existe un contrato con id={contrato_id}",
        )

    if contrato.estado != "activo":
        raise HTTPException(
            status_code=422,
            detail=f"El contrato está '{contrato.estado}' y no acepta nuevos pagos",
        )

    pago = crud.crear_pago(db, contrato_id, datos)

    if contrato.tipo == "Venta":
        total_pagado = sum(
            p.monto for p in contrato.pagos if p.estado == "completado"
        ) + datos.monto

        if total_pagado >= contrato.monto:
            contrato.estado = "finalizado"
            db.commit()

    return pago
