from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import historial_repository
from app.enums import TipoInmueble, EstadoInmueble

class HistorialService:
    def __init__(self, db: Session):
        self.db = db

#------------------------------------
#         Historial Estado 
#------------------------------------

    def create_historial_estado(self, historial_data: schemas.HistorialCreate):
        # 1. Crear historial
        historial = historial_repository.create_historial_estado(
            self.db,
            historial_data
        )

        return historial

    def update_historial_estado(self, historial_id: int, historial_update: schemas.HistorialUpdate):

        his = historial_repository.update_historial_estado(self.db, historial_id, historial_update)
        if not his:
            raise HTTPException(status_code=404, detail="History not found")

        return his


    def get_historial_estado_by_id(self, historial_id: int):
        his = historial_repository.get_historial_estado_by_id(self.db, historial_id)
        if not his:
            raise HTTPException(status_code=404, detail="History not found")
        return his
    
    def get_historial_estado_by_inmueble(self, inmueble_id: int):
        return historial_repository.get_historial_estado_by_inmueble(self.db, inmueble_id)

    def get_current_historial_by_inmueble(
        self,
        inmueble_id: int
    ):
        historial = historial_repository.get_current_historial_by_inmueble(
            self.db,
            inmueble_id
        )

        if not historial:
            raise HTTPException(
                status_code=404,
                detail="Current history not found"
            )

        return historial
    


#------------------------------------
#      Historial Propietario 
#------------------------------------

    def create_historial_propietario(self, historial_data: schemas.HistorialPropietarioCreate):
        # 1. Crear historial
        historial = historial_repository.create_historial_propietario(
            self.db,
            historial_data
        )

        return historial

    def update_historial_propietario(self, historial_id: int, historial_update: schemas.HistorialPropietarioUpdate):

        his = historial_repository.update_historial_propietario(self.db, historial_id, historial_update)
        if not his:
            raise HTTPException(status_code=404, detail="History not found")
        
        return his
    
    def close_current_propietario(self, inmueble_id: int):

        his = historial_repository.close_current_propietario(self.db, inmueble_id)

        if not his:
            raise HTTPException(status_code=404, detail="Current history not found")
        
        return his


    def get_historial_propietario_by_id(self, historial_id: int):
        his = historial_repository.get_historial_propietario_by_id(self.db, historial_id)
        if not his:
            raise HTTPException(status_code=404, detail="History not found")
        return his
    
    def get_historial_propietario_by_inmueble(self, inmueble_id: int):
        return historial_repository.get_historial_propietario_by_inmueble(self.db, inmueble_id)

    def get_current_propietario_by_inmueble(
        self,
        inmueble_id: int
    ):
        historial = historial_repository.get_current_propietario_by_inmueble(
            self.db,
            inmueble_id
        )

        if not historial:
            raise HTTPException(
                status_code=404,
                detail="Current history not found"
            )

        return historial


def get_historial_service(
    db: Session = Depends(get_db),
):
    return HistorialService(db)