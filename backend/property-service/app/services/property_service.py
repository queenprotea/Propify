from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import property_repository
from app.enums import TipoInmueble, EstadoInmueble


class PropertyService:
    def __init__(self, db: Session):
        self.db = db

    def create_inmueble(self, inmueble_data: schemas.InmuebleCreate):
        if not inmueble_data.titulo.strip():
            raise ValueError("Property title required")
        if inmueble_data.precio <= 0:
            raise ValueError("Price must be greater than 0")
        if (
            inmueble_data.area_terreno is not None
            and inmueble_data.area_terreno <= 0
        ):
            raise ValueError(
                "Area must be greater than 0"
            )
        return property_repository.create_inmueble(self.db, inmueble_data)

    def update_inmueble(self, inmueble_id: int, inmueble_update: schemas.InmuebleUpdate):
        if (
            inmueble_update.precio is not None
            and inmueble_update.precio <= 0
        ):
            raise ValueError(
                "Price must be greater than 0"
            )

        if (
            inmueble_update.area_terreno is not None
            and inmueble_update.area_terreno <= 0
        ):
            raise ValueError(
                "Area must be greater than 0"
            )
        
        inm = property_repository.update_inmueble(self.db, inmueble_id, inmueble_update)
        if not inm:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return inm

    def get_all_inmuebles(self, limit: int = 100, offset: int = 0):
        return property_repository.get_all_inmuebles(self.db, limit, offset)

    def delete_inmueble(self, inmueble_id: int):
        deleted = property_repository.delete_inmueble(self.db, inmueble_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Property not found")
        return True

    def get_inmueble_by_id(self, inmueble_id: int):
        inm = property_repository.get_inmueble_by_id(self.db, inmueble_id)
        if not inm:
            raise HTTPException(status_code=404, detail="Property not found")
        return inm
    
    
    def get_disponible_inmuebles(self):
        return property_repository.get_disponible_inmuebles(self.db)
    
    def get_inmuebles_by_tipo(self, tipo: TipoInmueble):
        return property_repository.get_inmuebles_by_tipo(self.db, tipo)
    
    def get_inmuebles_by_propietario(self, pro_id: int):
        return property_repository.get_inmuebles_by_propietario(self.db, pro_id)
    
    def get_inmuebles_by_titulo(self, titulo: str):
        return property_repository.get_inmuebles_by_titulo(self.db, titulo)

    def get_inmuebles_by_descripcion(self, des: str):
        return property_repository.get_inmuebles_by_descripcion(self.db, des)

    def update_inmueble_status(
        self,
        inmueble_id: int,
        status: EstadoInmueble
    ):

        inmueble = property_repository.update_inmueble_status(
            self.db,
            inmueble_id,
            status
        )

        if not inmueble:
            raise HTTPException(
                status_code=404,
                detail="Property not found"
            )

        return inmueble


#------------------------------------
#            ubicacion 
#------------------------------------
 
    def create_ubicacion(self, ubicacion_data: schemas.UbicacionCreate):
        # direccion_completa es autogenerada; se validan las partes obligatorias.
        if not ubicacion_data.estado.strip():
            raise ValueError("State required")

        if not ubicacion_data.ciudad.strip():
            raise ValueError("City required")

        if not ubicacion_data.calle.strip():
            raise ValueError("Street required")

        return property_repository.create_ubicacion(self.db, ubicacion_data)

    def update_ubicacion(self, ubicacion_id: int, ubicacion_update: schemas.UbicacionUpdate):
        ubi = property_repository.update_ubicacion(self.db, ubicacion_id, ubicacion_update)
        if not ubi:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return ubi


    def get_ubicacion_by_id(self, ubicacion_id: int):
        ubi = property_repository.get_ubicacion_by_id(self.db, ubicacion_id)
        if not ubi:
            raise HTTPException(status_code=404, detail="Location not found")
        return ubi
    
    def get_ubicaciones_by_direccion_completa(self, dir: str):
        return property_repository.get_ubicaciones_by_direccion_completa(self.db, dir)


#------------------------------------
#         Historial Estado 
#------------------------------------

    def create_historial_estado(self, historial_data: schemas.HistorialCreate):
        # 1. Crear historial
        historial = property_repository.create_historial_estado(
            self.db,
            historial_data
        )

        # 2. Actualizar estado actual del inmueble
        property_repository.update_inmueble_status(
            self.db,
            historial_data.inmueble_id,
            historial_data.estado
        )

        return historial

    def update_historial_estado(self, historial_id: int, historial_update: schemas.HistorialUpdate):

        his = property_repository.update_historial_estado(self.db, historial_id, historial_update)
        if not his:
            raise HTTPException(status_code=404, detail="History not found")
        
        return his


    def get_historial_by_id(self, historial_id: int):
        his = property_repository.get_historial_estado_by_id(self.db, historial_id)
        if not his:
            raise HTTPException(status_code=404, detail="History not found")
        return his
    
    def get_historial_by_inmueble(self, inmueble_id: int):
        return property_repository.get_historial_estado_by_inmueble(self.db, inmueble_id)

    def get_current_historial_by_inmueble(
        self,
        inmueble_id: int
    ):
        historial = property_repository.get_current_historial_by_inmueble(
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
#             Imagen 
#------------------------------------

    def create_imagen(self, imagen_data: schemas.ImagenCreate):
        return property_repository.create_imagen(self.db, imagen_data)


    def update_imagen(self, imagen_id: int, imagen_update: schemas.ImagenUpdate):

        img = property_repository.update_imagen(self.db, imagen_id, imagen_update)
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return img


    def get_imagen_by_id(self, imagen_id: int):
        img = property_repository.get_imagen_by_id(self.db, imagen_id)
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        return img
    
    def get_imagenes_by_inmueble(self, inmueble_id: int):
        return property_repository.get_imagenes_by_inmueble(self.db, inmueble_id)

    def delete_imagen(self, imagen_id: int):
        deleted = property_repository.delete_imagen(
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

#------------------------------------
#             Contacto 
#------------------------------------

    def create_contacto(self, contacto_data: schemas.ContactoCreate):
        if not contacto_data.nombre.strip():
            raise ValueError("Name required")
        
        if not contacto_data.mensaje.strip():
            raise ValueError("Message required")
        
        return property_repository.create_contacto(self.db, contacto_data)


    def update_contacto(self, contacto_id: int, contacto_update: schemas.ContactoUpdate):

        con = property_repository.update_contacto(self.db, contacto_id, contacto_update)
        if not con:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return con


    def get_contacto_by_id(self, contacto_id: int):
        con = property_repository.get_contacto_by_id(self.db, contacto_id)
        if not con:
            raise HTTPException(status_code=404, detail="Contact not found")
        return con
    

    def get_contactos_by_inmueble(self, id_inmueble: int):
        return property_repository.get_contactos_by_inmueble(self.db, id_inmueble)


    def get_all_contactos(self, limit: int = 100, offset: int = 0):
        return property_repository.get_all_contactos(self.db, limit, offset)


def get_property_service(
    db: Session = Depends(get_db),
):
    return PropertyService(db)

