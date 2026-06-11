from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import inmueble_repository, ubicacion_repository, historial_repository
from app.enums import TipoInmueble, EstadoInmueble
from decimal import Decimal


class InmuebleService:
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
        if (
            inmueble_data.area_construccion is not None
            and inmueble_data.area_construccion <= 0
        ):
            raise ValueError(
                "Construction area must be greater than 0"
            )
        
        tipo = inmueble_repository.get_tipo_inmueble_by_id(
            self.db,
            inmueble_data.tipo_id
        )

        if not tipo:
            raise ValueError("Property type not found")

        estado = inmueble_repository.get_estado_inmueble_by_id(
            self.db,
            inmueble_data.estado_id
        )

        if not estado:
            raise ValueError("Property state not found")

        ubicacion = ubicacion_repository.get_ubicacion_by_id(
            self.db,
            inmueble_data.ubicacion_id
        )

        if not ubicacion:
            raise ValueError("Property location not found")


        inmueble = inmueble_repository.create_inmueble(self.db, inmueble_data)
        historial_repository.create_historial_estado(
            self.db,
            schemas.HistorialCreate(inmueble_id=inmueble.id, estado_id=inmueble.estado_id),
        )
        return inmueble

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
        
        if (
            inmueble_update.area_construccion is not None
            and inmueble_update.area_construccion <= 0
        ):
            raise ValueError(
                "Construction area must be greater than 0"
            )
        
        inm = inmueble_repository.update_inmueble(self.db, inmueble_id, inmueble_update)
        if not inm:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return inm

    def get_all_inmuebles(self, limit: int = 100, offset: int = 0):
        return inmueble_repository.get_all_inmuebles(self.db, limit, offset)

    def get_inmueble_by_id(self, inmueble_id: int):
        inm = inmueble_repository.get_inmueble_by_id(self.db, inmueble_id)
        if not inm:
            raise HTTPException(status_code=404, detail="Property not found")
        return inm
    
    
    def get_disponible_inmuebles(self):
        return inmueble_repository.get_disponible_inmuebles(self.db)
    
    def get_inmuebles_by_tipo(self, tipo_id: int):
        return inmueble_repository.get_inmuebles_by_tipo(self.db, tipo_id)
    
    def get_inmuebles_by_tipo_admin(self, tipo_id: int):
        return inmueble_repository.get_inmuebles_by_tipo_admin(self.db, tipo_id)

    def get_inmuebles_by_propietario(self, pro_id: int):
        return inmueble_repository.get_inmuebles_by_propietario(self.db, pro_id)
    
    def get_inmuebles_by_titulo(self, titulo: str):
        return inmueble_repository.get_inmuebles_by_titulo(self.db, titulo)
    
    def get_inmuebles_by_titulo_admin(self, titulo: str):
        return inmueble_repository.get_inmuebles_by_titulo_admin(self.db, titulo)

    def get_inmuebles_by_descripcion(self, des: str):
        return inmueble_repository.get_inmuebles_by_descripcion(self.db, des)

    def get_inmuebles_by_descripcion_admin(self, des: str):
        return inmueble_repository.get_inmuebles_by_descripcion_admin(self.db, des)

    def get_inmuebles_by_estado(self, estado_id: int):
        return inmueble_repository.get_inmuebles_by_estado(self.db, estado_id)

    def search_inmuebles_admin(self, query: str):
        return inmueble_repository.search_inmuebles_admin(self.db, query)

    def search_inmuebles(self, query: str):
        return inmueble_repository.search_inmuebles(self.db, query)

    def get_inmuebles_by_estado_republica(self, estado_id: int):
        return inmueble_repository.get_inmuebles_by_estado_republica(self.db, estado_id)

    def get_inmuebles_by_estado_republica_admin(self, estado_id: int):
        return inmueble_repository.get_inmuebles_by_estado_republica_admin(self.db, estado_id)

    def get_inmuebles_by_ciudad_admin(self, ciudad: str):
        return inmueble_repository.get_inmuebles_by_ciudad_admin(self.db, ciudad)

    def get_inmuebles_by_ciudad(self, ciudad: str):
        return inmueble_repository.get_inmuebles_by_ciudad(self.db, ciudad)

    def get_inmuebles_by_colonia_admin(self, colonia: str):
        return inmueble_repository.get_inmuebles_by_colonia_admin(self.db, colonia)

    def get_inmuebles_by_colonia(self, colonia: str):
        return inmueble_repository.get_inmuebles_by_colonia(self.db, colonia)

    def get_inmuebles_by_calle_admin(self, calle: str):
        return inmueble_repository.get_inmuebles_by_calle_admin(self.db, calle)

    def get_inmuebles_by_calle(self, calle: str):
        return inmueble_repository.get_inmuebles_by_calle(self.db, calle)

    def get_inmuebles_by_precio_admin(self, precio: Decimal):
        return inmueble_repository.get_inmuebles_by_precio_admin(self.db, precio)

    def get_inmuebles_by_precio(self, precio: Decimal):
        return inmueble_repository.get_inmuebles_by_precio(self.db, precio)

    def get_inmuebles_by_num_recamaras_admin(self, num: int):
        return inmueble_repository.get_inmuebles_by_num_recamaras_admin(self.db, num)

    def get_inmuebles_by_num_recamaras(self, num: int):
        return inmueble_repository.get_inmuebles_by_num_recamaras(self.db, num)
    
    def get_inmuebles_by_num_banos_admin(self, num: int):
        return inmueble_repository.get_inmuebles_by_num_banos_admin(self.db, num)

    def get_inmuebles_by_num_banos(self, num: int):
        return inmueble_repository.get_inmuebles_by_num_banos(self.db, num)
    

    def update_inmueble_status(
        self,
        inmueble_id: int,
        estado_id: int
    ):

        estado = inmueble_repository.get_estado_inmueble_by_id(self.db, estado_id)
        if not estado:
            raise ValueError("Property state not found")

        inmueble = inmueble_repository.update_inmueble_status(
            self.db,
            inmueble_id,
            estado_id
        )

        if not inmueble:
            raise HTTPException(
                status_code=404,
                detail="Property not found"
            )

        historial_repository.create_historial_estado(
            self.db,
            schemas.HistorialCreate(inmueble_id=inmueble_id, estado_id=estado_id),
        )
        return inmueble
    

    def update_inmueble_propietario(
        self,
        inmueble_id: int,
        propietario_id: int
    ):

        inmueble = inmueble_repository.update_inmueble_propietario(
            self.db,
            inmueble_id,
            propietario_id
        )

        if not inmueble:
            raise HTTPException(
                status_code=404,
                detail="Property not found"
            )

        return inmueble
    

    def clear_propietario_inmueble(
        self,
        inmueble_id: int,
    ):

        inmueble = inmueble_repository.clear_propietario_inmueble(
            self.db,
            inmueble_id
        )

        if not inmueble:
            raise HTTPException(
                status_code=404,
                detail="Property not found"
            )

        return inmueble

#--------------------------
#       Estado inmueble 
#--------------------------

    def get_all_estado_inmueble(self):
        return inmueble_repository.get_all_estado_inmueble(self.db)

    def get_estado_inmueble_by_id(self, estado_id: int):
        
        estado = inmueble_repository.get_estado_inmueble_by_id(self.db, estado_id)

        if not estado:
            raise HTTPException(
                status_code=404,
                detail="State not found"
            )
        
        return estado
    

    def get_estado_inmueble_by_valor(self, valor: str):

        estado = inmueble_repository.get_estado_inmueble_by_valor(self.db, valor)

        if not estado:
            raise HTTPException(
                status_code=404,
                detail="State not found"
            )

        return estado
    
#--------------------------
#       Tipo inmueble 
#--------------------------

    def get_all_tipo_inmueble(self):
        return inmueble_repository.get_all_tipo_inmueble(self.db)

    def get_tipo_inmueble_by_id(self, tipo_id: int):

        tipo = inmueble_repository.get_tipo_inmueble_by_id(self.db, tipo_id)

        if not tipo:
            raise HTTPException(
                status_code=404,
                detail="Type not found"
            )

        return tipo
    
    def get_tipo_inmueble_by_valor(self, tipo_id: str):

        tipo = inmueble_repository.get_tipo_inmueble_by_valor(self.db, tipo_id)

        if not tipo:
            raise HTTPException(
                status_code=404,
                detail="Type not found"
            )

        return tipo

def get_inmueble_service(
    db: Session = Depends(get_db),
):
    return InmuebleService(db)

