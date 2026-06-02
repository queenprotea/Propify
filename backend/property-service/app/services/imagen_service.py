from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import imagen_repository
from app.enums import TipoInmueble, EstadoInmueble


class ImagenService:
    def __init__(self, db: Session):
        self.db = db


#------------------------------------
#             Imagen 
#------------------------------------

    def create_imagen(self, imagen_data: schemas.ImagenCreate):
        return imagen_repository.create_imagen(self.db, imagen_data)


    def update_imagen(self, imagen_id: int, imagen_update: schemas.ImagenUpdate):

        img = imagen_repository.update_imagen(self.db, imagen_id, imagen_update)
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return img


    def get_imagen_by_id(self, imagen_id: int):
        img = imagen_repository.get_imagen_by_id(self.db, imagen_id)
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        return img
    
    def get_imagenes_by_inmueble(self, inmueble_id: int):
        return imagen_repository.get_imagenes_by_inmueble(self.db, inmueble_id)

    def delete_imagen(self, imagen_id: int):
        deleted = imagen_repository.delete_imagen(
            self.db,
            imagen_id
        )

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Image not found"
            )

        return {
            "message": "Image deleted successfully"
        }


def get_imagen_service(
    db: Session = Depends(get_db),
):
    return ImagenService(db)