from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.repositories import contacto_repository, inmueble_repository
from app.enums import TipoInmueble, EstadoInmueble

class ContactoService:
    def __init__(self, db: Session):
        self.db = db

#------------------------------------
#             Contacto 
#------------------------------------

    def create_contacto(self, contacto_data: schemas.ContactoCreate):
        
        inmueble = inmueble_repository.get_inmueble_by_id(
            self.db,
            contacto_data.inmueble_id
        )

        if not inmueble:
            raise ValueError("Property not found")
        
        if not contacto_data.nombre.strip():
            raise ValueError("Name required")
        
        if not contacto_data.correo.strip():
            raise ValueError("Email required")
        
        if not contacto_data.mensaje.strip():
            raise ValueError("Message required")
        
        return contacto_repository.create_contacto(self.db, contacto_data)

    def delete_contacto(self, contacto_id: int):
        con = contacto_repository.delete_contacto(self.db, contacto_id)
        if not con:
            raise HTTPException(status_code=404, detail="Contact not found")
        return con

    def get_contacto_by_id(self, contacto_id: int):
        con = contacto_repository.get_contacto_by_id(self.db, contacto_id)
        if not con:
            raise HTTPException(status_code=404, detail="Contact not found")
        return con
    

    def get_contactos_by_inmueble(self, id_inmueble: int):
        return contacto_repository.get_contactos_by_inmueble(self.db, id_inmueble)

    def get_contactos_by_correo(self, correo: str):
        return contacto_repository.get_contactos_by_correo(self.db, correo)

    def get_all_contactos(self, limit: int = 100, offset: int = 0):
        return contacto_repository.get_all_contactos(self.db, limit, offset)

    def search_contactos(self, query: str):
        return contacto_repository.search_contactos(self.db, query)


def get_contacto_service(
    db: Session = Depends(get_db),
):
    return ContactoService(db)
