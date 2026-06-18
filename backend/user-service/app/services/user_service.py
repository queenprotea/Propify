from datetime import timedelta

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, security, email_utils
from app.database import get_db
from app.repositories import user_repository

class UserService:
    def __init__(self, db: Session):
        self.db = db
    

    def _check_unique(self, correo, telefono, exclude_id=None):
        """Valida unicidad de correo y teléfono (excluyendo al propio usuario)."""
        if correo:
            existente = user_repository.get_user_by_correo(self.db, correo)
            if existente and existente.id != exclude_id:
                raise ValueError("El correo ya se encuentra registrado")
        if telefono:
            existente = user_repository.get_user_by_telefono(self.db, telefono)
            if existente and existente.id != exclude_id:
                raise ValueError("El teléfono ya se encuentra registrado por otro usuario")

    def count_active_admins(self) -> int:
        return user_repository.count_active_admins(self.db)

    def register_user(self, user_data: schemas.UserCreate) -> schemas.User:
        try:
            self._check_unique(user_data.correo, user_data.telefono)

            db_user = user_repository.create_user(self.db, user_data)
            email_utils.enviar_verificacion(db_user.correo, db_user.nombre, db_user.verification_token)

            return db_user
        except (ValueError, ConnectionError) as e:
            raise e
        except Exception as e:
            raise Exception("Registration service unavailable - please try again later")


    def register_user_admin(self, user_data: schemas.UserCreate) -> schemas.User:
        try:
            self._check_unique(user_data.correo, user_data.telefono)

            db_user = user_repository.create_user_admin(self.db, user_data)

            return db_user
        except (ValueError, ConnectionError) as e:
            raise e
        except Exception as e:
            raise Exception("Registration service unavailable - please try again later")
    


    def login_user(self, identifier: str, password: str) -> schemas.Token:
        try:
            user = user_repository.get_user_by_correo(self.db, identifier)
            if not user:
                user = user_repository.get_user_by_telefono(self.db, identifier)

            if not user or not security.verify_password(password, user.password):
                raise ValueError("Incorrect credentials")
            
            if not user.is_active:
                raise ValueError("Incorrect credentials")

            if not user.is_verified:
                raise ValueError("Tu correo no está verificado. Revisa tu bandeja de entrada o solicita un nuevo enlace.")

            access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = security.create_access_token(
                data={
                    "sub": str(user.id), 
                    "is_admin": user.is_admin
                },
                expires_delta=access_token_expires
            )

            return schemas.Token(access_token=access_token, token_type="bearer")

        except ValueError as e:
            raise e
        except Exception as e:
            raise RuntimeError("Login service unavailable - please try again later") from e

    
    def get_user_by_id(self, user_id: int) -> schemas.User:
        user = user_repository.get_user_by_id(self.db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_user_by_nombre(self, nombre: str) -> schemas.User:
        user = user_repository.get_user_by_nombre(self.db, nombre)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
    def get_user_by_correo(self, correo: str) -> schemas.User:
        user = user_repository.get_user_by_correo(self.db, correo)
        if not user:
           raise HTTPException(status_code=404, detail="User not found")
        return user
    
    def get_user_by_telefono(self, telefono: str) -> schemas.User:
        user = user_repository.get_user_by_telefono(self.db, telefono)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_all_users(self, limit: int = 100, offset: int = 0):
        users = user_repository.get_all_users(self.db, limit=limit, offset=offset)
        return users
    
    def get_active_users(self, limit: int = 100, offset: int = 0):
        users = user_repository.get_active_users(self.db, limit=limit, offset=offset)
        return users
    
    def update_user(self, user_id: int, user_update: schemas.UserUpdate):
        self._check_unique(user_update.correo, user_update.telefono, exclude_id=user_id)
        us = user_repository.update_user(self.db, user_id, user_update)
        if not us:
            raise HTTPException(status_code=404, detail="User not found")
        return us

    def update_user_admin(self, user_id: int, user_update: schemas.UserUpdate):
        self._check_unique(user_update.correo, user_update.telefono, exclude_id=user_id)
        us = user_repository.update_user_admin(self.db, user_id, user_update)
        if not us:
            raise HTTPException(status_code=404, detail="User not found")
        return us

    def search_users(self, query: str):
        return user_repository.search_users(self.db, query)
    
    def deactivate_user(self, user_id: int):
        user = user_repository.deactivate_user(self.db, user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
        return user
    
    def activate_user(self, user_id: int):
        user = user_repository.activate_user(self.db, user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
        return user
        
    def verify_email(self, token: str):
        user = user_repository.get_user_by_verification_token(self.db, token)
        if not user:
            raise ValueError("El enlace de verificación no es válido o ya fue utilizado")
        return user_repository.mark_verified(self.db, user)

    def resend_verification(self, correo: str):
        user = user_repository.get_user_by_correo(self.db, correo)
        # No se revela si el correo existe o ya está verificado.
        if user and not user.is_verified:
            user = user_repository.reset_verification_token(self.db, user)
            email_utils.enviar_verificacion(user.correo, user.nombre, user.verification_token)

    def forward_auth_header(self, token: str):
        return {"Authorization": f"Bearer {token}"}
    
    #---------------------------------
    #--------ESTADO VISITAS-----------
    #---------------------------------

    def get_state_by_id(self, state_id: int):
        return user_repository.get_state_by_id(self.db, state_id)
    
    def get_all_state(self):
        return user_repository.get_all_states(self.db)


    #---------------------------------
    #------------VISITAS--------------
    #---------------------------------

    def create_visit(self, visit_data: schemas.VisitaCreate):

        estado = user_repository.get_state_by_id(
            self.db,
            visit_data.estado_id
        )

        if not estado:
            raise ValueError("El estado de la visita no es válido")

        # La visita debe agendarse a partir de mañana (no fechas pasadas ni el mismo día).
        from datetime import datetime, timedelta, timezone
        fecha = visit_data.fecha
        hoy = datetime.now(timezone.utc).date()
        fecha_dia = fecha.date() if hasattr(fecha, "date") else fecha
        if fecha_dia <= hoy:
            raise ValueError("La visita debe agendarse para una fecha posterior a hoy")

        return user_repository.create_visit(self.db, visit_data)

    def update_visit(self, visit_id: int, visit_update: schemas.VisitaUpdate):

        if visit_update.estado_id is not None:

            estado = user_repository.get_state_by_id(
                self.db,
                visit_update.estado_id
            )

            if not estado:
                raise ValueError("Invalid visit state")

        vi = user_repository.update_visit(self.db, visit_id, visit_update)
        if not vi:
            raise HTTPException(status_code=404, detail="Visit not found")
        return vi

    def get_visits_by_user(self, user_id: int):
        return user_repository.get_visits_by_user(self.db, user_id)
    
    
    def get_visits_by_property(self, pro_id: int):
        return user_repository.get_visits_by_property(self.db, pro_id)
       

    def get_all_visits(self):
        return user_repository.get_all_visits(self.db)

    def get_visit_by_id(self, id: int):
        cl = user_repository.get_visit_by_id(self.db, id)
        if not cl:
            raise HTTPException(status_code=404, detail="Visit not found")
        return cl
    
    def get_visit_by_estado_id(self, estado_id: int):
        return user_repository.get_visits_by_estado_id(self.db, estado_id)
    
    def get_visit_by_estado(self, estado: str):
        return user_repository.get_visits_by_estado(self.db, estado)
   
def get_user_service(db: Session = Depends(get_db)):
    return UserService(db)