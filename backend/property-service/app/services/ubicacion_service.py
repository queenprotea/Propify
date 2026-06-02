from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import ubicacion_repository

class UbicacionService:
    def __init__(self, db: Session):
        self.db = db

#------------------------------------
#            ubicacion 
#------------------------------------
 
    def create_ubicacion(self, ubicacion_data: schemas.UbicacionCreate):
        
        if not ubicacion_data.estado_id:
            raise ValueError(
                "State required"
            )

        if not ubicacion_data.ciudad.strip():
            raise ValueError(
                "City required"
            )

        return ubicacion_repository.create_ubicacion(self.db, ubicacion_data)


    def update_ubicacion(self, ubicacion_id: int, ubicacion_update: schemas.UbicacionUpdate):
        if (
            ubicacion_update.estado_id is not None
            and ubicacion_update.estado_id <= 0
        ):
            raise ValueError(
                "State required"
            )

        ubi = ubicacion_repository.update_ubicacion(self.db, ubicacion_id, ubicacion_update)
        if not ubi:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return ubi


    def get_ubicacion_by_id(self, ubicacion_id: int):
        ubi = ubicacion_repository.get_ubicacion_by_id(self.db, ubicacion_id)
        if not ubi:
            raise HTTPException(status_code=404, detail="Location not found")
        return ubi
    
    def search_ubicaciones(self, query: str):
        return ubicacion_repository.search_ubicaciones(self.db, query)


    #--------------------------
    #       Estado Republica 
    #--------------------------

    def get_all_estado_republica(self):
        return ubicacion_repository.get_all_estado_republica(self.db)

    def get_estado_republica_by_id(self, estado_id: int):
        
        estado = ubicacion_repository.get_estado_republica_by_id(self.db, estado_id)
        
        if not estado:
                raise HTTPException(
                    status_code=404,
                    detail="State of country not found"
                )
        
        return estado
    
    def get_estado_republica_by_valor(self, valor: str):
        
        estado = ubicacion_repository.get_estado_republica_by_valor(self.db, valor)

        if not estado:
                raise HTTPException(
                    status_code=404,
                    detail="State of country not found"
                )

        return estado

def get_ubicacion_service(
    db: Session = Depends(get_db),
):
    return UbicacionService(db)