from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse

from app import schemas
from app.dependencies.dependencies import get_current_user
from app.services.user_service import UserService, get_user_service

app = FastAPI(title="Propify")


# Manejador global: convierte errores inesperados en un mensaje legible (no técnico).
@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado. Inténtalo de nuevo más tarde."},
    )

def require_admin(user):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")


# --- API Endpoints ---

# user endpoints
    
@app.post("/register", response_model=schemas.User)
def register(
    user: schemas.UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    try:
        creado = user_service.register_user(user)
        return creado
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

@app.post("/register/admin", response_model=schemas.User)
def register_admin(
    user: schemas.UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: schemas.User = Depends(get_current_user),
):
    try:
        if current_user.is_admin == True:
            creado = user_service.register_user_admin(user)
            return creado
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
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
        

@app.get("/verify-email")
def verify_email(token: str, user_service: UserService = Depends(get_user_service)):
    try:
        u = user_service.verify_email(token)
        return {"message": "Correo verificado correctamente. Ya puedes iniciar sesión."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/resend-verification")
def resend_verification(body: schemas.ResendVerification,
                        user_service: UserService = Depends(get_user_service)):
    user_service.resend_verification(body.correo)
    return {"message": "Si el correo está registrado y pendiente de verificar, se envió un nuevo enlace."}


@app.get("/verify-token", response_model=schemas.User)
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
        require_admin(current_user)
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
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    require_admin(current_user)
    return user_service.get_active_users(limit, offset)


# Debe declararse ANTES de "/users/{user_id}" para que "search" no se interprete como id.
@app.get("/users/search", response_model=list[schemas.User])
def search_users(
        q: str,
        user_service: UserService = Depends(get_user_service),
        current_user: schemas.User = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return user_service.search_users(q)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get("/users/{user_id}", response_model=schemas.User)
def get_user_by_id(
    user_id: int,
    current_user: schemas.User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        if current_user.id != user_id:
            require_admin(current_user)
        return user_service.get_user_by_id(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    

@app.get("/users/correo/{correo}", response_model=schemas.User)
def get_user_by_correo(
        correo: str,
        user_service: UserService = Depends(get_user_service),
        current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return user_service.get_user_by_correo(correo)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    

@app.get("/users/telefono/{telefono}", response_model=schemas.User)
def get_user_by_telefono(
        telefono: str,
        user_service: UserService = Depends(get_user_service),
        current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return user_service.get_user_by_telefono(telefono)
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
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized")
        return user_service.update_user(user_id, user_data)
    except ValueError as e:
        # Conflicto de unicidad (correo/teléfono ya registrados).
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    
@app.put("/users/admin/{user_id}", response_model=schemas.User)
def update_user_admin(
    user_id: int,
    user_data: schemas.UserUpdate,
    current_user: schemas.User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        if current_user.is_admin != True:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        quitando_acceso = (user_data.is_active is False) or (user_data.is_admin is False)
        # Un administrador no puede modificar su propio estado de acceso.
        if current_user.id == user_id and quitando_acceso:
            raise HTTPException(status_code=403,
                detail="Un administrador no puede modificar su propio estado de acceso")
        # Debe existir al menos un administrador activo.
        if quitando_acceso:
            target = user_service.get_user_by_id(user_id)
            if target.is_admin and target.is_active and user_service.count_active_admins() <= 1:
                raise HTTPException(status_code=409,
                    detail="No se puede desactivar/degradar al último administrador activo")

        return user_service.update_user_admin(user_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    

@app.patch("/users/{user_id}/deactivate", response_model=schemas.User)
def deactivate_user(
    user_id: int,
    current_user: schemas.User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        if current_user.is_admin == False:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Un administrador no puede inhabilitar su propia cuenta.
        if current_user.id == user_id:
            raise HTTPException(status_code=403,
                detail="Un administrador no puede modificar su propio estado de acceso")
        # Siempre debe existir al menos un administrador activo.
        target = user_service.get_user_by_id(user_id)
        if target.is_admin and target.is_active and user_service.count_active_admins() <= 1:
            raise HTTPException(status_code=409,
                detail="No se puede desactivar al último administrador activo del sistema")
        u = user_service.deactivate_user(user_id)
        return u
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.patch("/users/{user_id}/activate", response_model=schemas.User)
def activate_user(
    user_id: int,
    current_user: schemas.User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        if current_user.is_admin == False:
            raise HTTPException(403)
        u = user_service.activate_user(user_id)
        return u
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

#----- estado visitas ------
@app.get("/visit-states/all", response_model=list[schemas.EstadoVisita])
def get_all_states_visit(
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_all_state()


@app.get("/visit-states/id/{state_id}", response_model=schemas.EstadoVisita)
def get_state_visit_id_endpoint(
    state_id: int,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_state_by_id(state_id)


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
        # 409 si es conflicto de horario; 400 para otras validaciones.
        code = status.HTTP_409_CONFLICT if "visita agendada" in str(e) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(e))


@app.put("/visits/{visit_id}", response_model=schemas.Visita)
def update_visit(
    visit_id: int,
    visit_update: schemas.VisitaUpdate,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    try:
        require_admin(current_user)
        return user_service.update_visit(visit_id, visit_update)
    except ValueError as e:
        code = status.HTTP_409_CONFLICT if "visita agendada" in str(e) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(e))


@app.get("/visits/all", response_model=list[schemas.Visita])
def get_all_visits(
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    require_admin(current_user)
    return user_service.get_all_visits()


@app.get("/visits/id/{visit_id}", response_model=schemas.Visita)
def get_visit_id_endpoint(
    visit_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    require_admin(current_user)
    return user_service.get_visit_by_id(visit_id)


@app.get("/visits/user/{user_id}", response_model=list[schemas.Visita])
def get_visits_by_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    if current_user.id != user_id:
        require_admin(current_user)
    return user_service.get_visits_by_user(user_id)


@app.get("/visits/property/{pro_id}", response_model=list[schemas.Visita])
def get_visits_by_property(
    pro_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    require_admin(current_user)
    return user_service.get_visits_by_property(pro_id)


@app.get("/visits/state/id/{state_id}", response_model=list[schemas.Visita])
def get_visits_by_state_id(
    state_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    require_admin(current_user)
    return user_service.get_visit_by_estado_id(state_id)


@app.get("/visits/state/{state}", response_model=list[schemas.Visita])
def get_visits_by_state_name(
    state: str,
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    require_admin(current_user)
    return user_service.get_visit_by_estado(state)
