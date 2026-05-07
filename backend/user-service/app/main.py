from fastapi import FastAPI, Depends, HTTPException, status

from app import schemas
from app.dependencies.dependencies import get_current_user
from app.services.user_service import UserService, get_user_service

app = FastAPI(title="Propify")

# --- API Endpoints ---

# user endpoints
    
@app.post("/register", response_model=schemas.User)
def register(
    user: schemas.UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.register_user(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    

@app.post("/login", response_model=schemas.Token)
def login(
    form_data: schemas.UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    try: 
        return user_service.login_user(form_data.identifier, form_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
        

@app.get("/verify-token")
def verify_token(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/users/all", response_model=list[schemas.User])
def list_all_users(
    limit: int = 50,
    offset: int = 0,
    current_user: schemas.User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.get_all_users(limit=limit, offset=offset)
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@app.get("/users/active", response_model=list[schemas.User])
def get_active_users(
    limit: int = 50,
    offset: int = 0,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_active_users(limit, offset)


@app.get("/users/{user_id}", response_model=schemas.User)
def get_user_by_id(
    user_id: int,
    current_user: schemas.User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.get_user_by_id(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    

@app.get("/users/correo/{correo}", response_model=schemas.User)
def get_user_by_correo(
        correo: str,
        user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.get_user_by_correo(correo)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    

@app.get("/users/telefono/{telefono}", response_model=schemas.User)
def get_user_by_telefono(
        telefono: str,
        user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.get_user_by_telefono(telefono)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
@app.get("/users/search/{query}", response_model=list[schemas.User])
def search_users(
        query: str,
        user_service: UserService = Depends(get_user_service),
        current_user: schemas.User = Depends(get_current_user)
):
    try:
        return user_service.search_users(query)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    current_user: schemas.User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.update_user(user_id, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    
@app.patch("/users/{user_id}/deactivate", response_model=schemas.User)
def deactivate_user(
    user_id: int,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        if current_user.rol != "admin":
            raise HTTPException(403)
        return user_service.deactivate_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@app.patch("/users/{user_id}/activate", response_model=schemas.User)
def activate_user(
    user_id: int,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        if current_user.rol != "admin":
            raise HTTPException(403)
        return user_service.activate_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

# --- Visitas ---
@app.post("/visits", response_model=schemas.Visita)
def create_visit(
    visit: schemas.VisitaCreate,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.create_visit(visit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/visits/{visit_id}", response_model=schemas.Visita)
def update_visit(
    visit_id: int,
    visit_update: schemas.VisitaUpdate,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        return user_service.update_visit(visit_id, visit_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/visits/all", response_model=list[schemas.Visita])
def get_all_visits(
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_all_visits()


@app.get("/visits/id/{visit_id}", response_model=schemas.Visita)
def get_visit_id_endpoint(
    visit_id: int,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_visit_by_id(visit_id)


@app.get("/visits/user/{user_id}", response_model=list[schemas.Visita])
def get_visits_by_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_visits_by_user(user_id)


@app.get("/visits/property/{pro_id}", response_model=list[schemas.Visita])
def get_visits_by_property(
    pro_id: int,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_visits_by_property(pro_id)
