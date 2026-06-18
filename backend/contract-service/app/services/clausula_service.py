# Lógica de negocio del catálogo de cláusulas
from fastapi import HTTPException

import crud


def listar(db):
    return crud.listar_clausulas_catalogo(db)


def crear(db, datos):
    try:
        return crud.crear_clausula_catalogo(db, datos)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


def eliminar(db, clausula_id):
    if not crud.eliminar_clausula_catalogo(db, clausula_id):
        raise HTTPException(status_code=404, detail="Cláusula no encontrada")
    return {"message": "Cláusula eliminada"}
