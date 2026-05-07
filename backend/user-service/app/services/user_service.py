from datetime import timedelta

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, security
from app.database import get_db
from app.repositories import user_repository

class UserService:
    def __init__(self, db: Session):
        self.db = db
    

    def register_user(self, user_data: schemas.UserCreate) -> schemas.User:
        try:
            if user_repository.get_user_by_correo(self.db, user_data.correo):
                raise ValueError("Email already registered")
            
            db_user = user_repository.create_user(self.db, user_data)

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
            
            if (user.estado.lower() != "activo"):
                raise ValueError("Incorrect credentials")

            access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = security.create_access_token(
                data={"sub": str(user.id), "rol": user.rol},
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
        us = user_repository.update_user(self.db, user_id, user_update)
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
        
    def forward_auth_header(self, token: str):
        return {"Authorization": f"Bearer {token}"}
    

    # visitas

    def create_visit(self, visit_data: schemas.VisitaCreate):
        return user_repository.create_visit(self.db, visit_data)

    def update_visit(self, visit_id: int, visit_update: schemas.VisitaUpdate):
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
            raise HTTPException(status_code=404, detail="Client not found")
        return cl
    
   
def get_user_service(db: Session = Depends(get_db)):
    return UserService(db)