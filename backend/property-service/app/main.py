from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
from pathlib import Path

from decimal import Decimal

from app.database import get_db
from app.security import get_current_user
from app.services.contacto_service import ContactoService, get_contacto_service
from app.services.historial_service import HistorialService, get_historial_service
from app.services.imagen_service import ImagenService, get_imagen_service
from app.services.inmueble_service import InmuebleService, get_inmueble_service
from app.services.ubicacion_service import UbicacionService, get_ubicacion_service

from app.repositories import inmueble_repository ,contacto_repository, historial_repository, imagen_repository, ubicacion_repository

from app import schemas, enums
import os
import uuid

app = FastAPI(title="Property Service")

STATIC_PROPERTY_DIR = Path("/app/static/propertyImages")
STATIC_PROPERTY_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="/app/static"), name="static")

def require_admin(user):
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

# --- API Endpoints ---

#------------------------------------
#            inmueble 
#------------------------------------

@app.post("/inmuebles", response_model=schemas.Inmueble)
def create_inmueble(
    inmueble: schemas.InmuebleCreate,
    current_user = Depends(get_current_user),
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    
    try:
        require_admin(current_user)        
        return inmueble_service.create_inmueble(inmueble)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )


@app.put("/inmuebles/{inmueble_id}", response_model=schemas.Inmueble)
def update_inmueble(
    inmueble_id: int,
    inmueble_update: schemas.InmuebleUpdate,
    current_user = Depends(get_current_user),
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    try:
        require_admin(current_user)
        return inmueble_service.update_inmueble(inmueble_id, inmueble_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )


@app.patch("/inmuebles/{inmueble_id}/estado/{status_id}", response_model=schemas.Inmueble)
def update_inmueble_status(
    inmueble_id: int,
    status_id: int,
    current_user = Depends(get_current_user),
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    try:
        require_admin(current_user)
        return inmueble_service.update_inmueble_status(inmueble_id, status_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    

@app.patch("/inmuebles/{inmueble_id}/propietario/{pro_id}", response_model=schemas.Inmueble)
def update_inmueble_propietario(
    inmueble_id: int,
    pro_id: int,
    current_user = Depends(get_current_user),
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    try:
        require_admin(current_user)
        return inmueble_service.update_inmueble_propietario(inmueble_id, pro_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.patch("/inmuebles/{inmueble_id}/propietario-clear", response_model=schemas.Inmueble)
def clear_propietario_inmueble(
    inmueble_id: int,
    current_user = Depends(get_current_user),
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    try:
        require_admin(current_user)
        return inmueble_service.clear_propietario_inmueble(inmueble_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )


@app.get("/inmuebles/all", response_model=list[schemas.InmuebleDetalle])
def get_all_inmuebles(
    limit: int = 100,
    offset: int = 0,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_all_inmuebles(limit, offset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )

@app.get("/inmuebles/id/{inmueble_id}", response_model=schemas.InmuebleDetalle)
def get_inmueble_id_endpoint(
    inmueble_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_inmueble_by_id(inmueble_id)


@app.get("/inmuebles/disponible", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_disponibles(
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_disponible_inmuebles()


@app.get("/inmuebles/admin/tipo/{tipo_id}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_tipo_admin(
    tipo_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
): 
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_tipo_admin(tipo_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )


@app.get("/inmuebles/tipo/{tipo_id}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_tipo(
    tipo_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_inmuebles_by_tipo(tipo_id)

#=============
# checkpoint
#=============

@app.get("/inmuebles/propietario/{id_pro}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_propietario(
    id_pro: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_propietario(id_pro)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )

@app.get("/mis-inmuebles", response_model=list[schemas.InmuebleDetalle])
def get_mis_inmuebles(
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    return inmueble_service.get_inmuebles_by_propietario(current_user.id)


#/inmuebles/titulo?q=Casa en Veracruz
@app.get("/inmuebles/admin/titulo", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_titulo_admin(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_titulo_admin(q)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
 
@app.get("/inmuebles/titulo", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_titulo(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_inmuebles_by_titulo(q)

@app.get("/inmuebles/admin/descripcion", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_descripcion_admin(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_descripcion_admin(q)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )

@app.get("/inmuebles/descripcion", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_descripcion(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_inmuebles_by_descripcion(q)


#para que los clientes no puedan ingresar el id de algun estado no publico (rentado, vendido, etc)
@app.get("/inmuebles/estado/{estado}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_estado(
    estado: enums.EstadoInmueblePublico,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    try:
        est = inmueble_service.get_estado_inmueble_by_valor(estado)
        return inmueble_service.get_inmuebles_by_estado(est.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )

#aqui si puede ingresar el id, pero solo admin
@app.get("/inmuebles/admin/estado/{estado_id}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_estado_admin(
    estado_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_estado(estado_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )


@app.get("/inmuebles/admin/search", response_model=list[schemas.InmuebleDetalle])
def search_inmuebles_admin(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.search_inmuebles_admin(q)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/search", response_model=list[schemas.InmuebleDetalle])
def search_inmuebles(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.search_inmuebles(q)


@app.get("/inmuebles/admin/estado-republica/{estado_id}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_estado_republica_admin(
    estado_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_estado_republica_admin(estado_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/estado-republica/{estado_id}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_estado_republica(
    estado_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_inmuebles_by_estado_republica(estado_id)
       

@app.get("/inmuebles/admin/ciudad", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_ciudad_admin(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_ciudad_admin(q)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/ciudad", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_ciudad(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_inmuebles_by_ciudad(q)
       

@app.get("/inmuebles/admin/colonia", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_colonia_admin(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_colonia_admin(q)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/colonia", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_colonia(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_inmuebles_by_colonia(q)
       
@app.get("/inmuebles/admin/calle", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_calle_admin(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_calle_admin(q)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/calle", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_calle(
    q: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_inmuebles_by_calle(q)
       

@app.get("/inmuebles/admin/precio/{precio}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_precio_admin(
    precio: Decimal,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_precio_admin(precio)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/precio/{precio}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_precio(
    precio: Decimal,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_inmuebles_by_precio(precio)
       
@app.get("/inmuebles/admin/num-recamaras/{num}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_num_recamaras_admin(
    num: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_num_recamaras_admin(num)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/num-recamaras/{num}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_num_recamaras(
    num: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_inmuebles_by_num_recamaras(num)
       
@app.get("/inmuebles/admin/num-banos/{num}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_num_banos_admin(
    num: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
    current_user = Depends(get_current_user)
):
    try:
        require_admin(current_user)
        return inmueble_service.get_inmuebles_by_num_banos_admin(num)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )
    
@app.get("/inmuebles/num-banos/{num}", response_model=list[schemas.InmuebleDetalle])
def get_inmuebles_by_num_banos(
    num: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_inmuebles_by_num_banos(num)
       

#------------------------------------
#          estado inmueble 
#------------------------------------

@app.get("/estado-inmueble/all", response_model=list[schemas.EstadoInmueble])
def get_all_estado_inmueble(
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_all_estado_inmueble()

@app.get("/estado-inmueble/id/{estado_id}", response_model=schemas.EstadoInmueble)
def get_estado_inmueble_by_id(
    estado_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_estado_inmueble_by_id(estado_id)

@app.get("/estado-inmueble/valor/{valor}", response_model=schemas.EstadoInmueble)
def get_estado_inmueble_by_valor(
    valor: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_estado_inmueble_by_valor(valor)


#------------------------------------
#          tipo inmueble 
#------------------------------------

@app.get("/tipo-inmueble/all", response_model=list[schemas.TipoInmueble])
def get_all_tipo_inmueble(
    inmueble_service: InmuebleService = Depends(get_inmueble_service),
):
    return inmueble_service.get_all_tipo_inmueble()

@app.get("/tipo-inmueble/id/{tipo_id}", response_model=schemas.TipoInmueble)
def get_tipo_inmueble_by_id(
    tipo_id: int,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_tipo_inmueble_by_id(tipo_id)

@app.get("/tipo-inmueble/valor/{valor}", response_model=schemas.TipoInmueble)
def get_tipo_inmueble_by_valor(
    valor: str,
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    return inmueble_service.get_tipo_inmueble_by_valor(valor)



#------------------------------------
#            ubicacion 
#------------------------------------

@app.post("/ubicaciones", response_model=schemas.Ubicacion)
def create_ubicacion(
    ubicacion: schemas.UbicacionCreate,
    current_user = Depends(get_current_user),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    try:
        require_admin(current_user)
        return ubicacion_service.create_ubicacion(ubicacion)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )


@app.put("/ubicaciones/{ubicacion_id}", response_model=schemas.Ubicacion)
def update_ubicacion(
    ubicacion_id: int,
    ubicacion_update: schemas.UbicacionUpdate,
    current_user = Depends(get_current_user),
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    try:
        require_admin(current_user)
        return ubicacion_service.update_ubicacion(ubicacion_id, ubicacion_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        )


@app.get("/ubicaciones/id/{ubicacion_id}", response_model=schemas.Ubicacion)
def get_ubicacion_by_id_endpoint(
    ubicacion_id: int,
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    return ubicacion_service.get_ubicacion_by_id(ubicacion_id)


@app.get("/ubicaciones/search", response_model=list[schemas.Ubicacion])
def search_ubicaciones(
    q: str,
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    return ubicacion_service.search_ubicaciones(q)


#------------------------------------
#          estado republica
#------------------------------------

@app.get("/estado-republica/all", response_model=list[schemas.EstadoRepublica])
def get_all_estado_republica(
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service),
):
    return ubicacion_service.get_all_estado_republica()

@app.get("/estado-republica/id/{estado_id}", response_model=schemas.EstadoRepublica)
def get_estado_republica_by_id(
    estado_id: int,
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    return ubicacion_service.get_estado_republica_by_id(estado_id)

@app.get("/estado-republica/valor/{valor}", response_model=schemas.EstadoRepublica)
def get_estado_republica_by_valor(
    valor: str,
    ubicacion_service: UbicacionService = Depends(get_ubicacion_service)
):
    return ubicacion_service.get_estado_republica_by_valor(valor)



#------------------------------------
#         Historial Estado 
#------------------------------------

@app.post("/historial-estado", response_model=schemas.Historial)
def create_historial_estado(
    historial: schemas.HistorialCreate,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.create_historial_estado(historial)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 

@app.put("/historial-estado/{historial_id}", response_model=schemas.Historial)
def update_historial_estado(
    historial_id: int,
    historial_update: schemas.HistorialUpdate,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.update_historial_estado(historial_id, historial_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 

@app.get("/historial-estado/{historial_id}", response_model=schemas.Historial)
def get_historial_estado_id_endpoint(
    historial_id: int,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):   
    try:
        require_admin(current_user)
        return historial_service.get_historial_estado_by_id(historial_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


@app.get("/historial-estado/inmueble/{inmueble_id}", response_model=list[schemas.Historial])
def get_historial_estado_by_inmueble(
    inmueble_id: int,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.get_historial_estado_by_inmueble(inmueble_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


@app.get("/historial-estado/inmueble/{inmueble_id}/actual", response_model=schemas.Historial)
def get_current_historial_by_inmueble(
    inmueble_id: int,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.get_current_historial_by_inmueble(inmueble_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


#------------------------------------
#       Historial Propietario 
#------------------------------------

@app.post("/historial-propietario", response_model=schemas.HistorialPropietario)
def create_historial_propietario(
    historial: schemas.HistorialPropietarioCreate,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.create_historial_propietario(historial)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 

@app.put("/historial-propietario/{historial_id}", response_model=schemas.HistorialPropietario)
def update_historial_propietario(
    historial_id: int,
    historial_update: schemas.HistorialPropietarioUpdate,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.update_historial_propietario(historial_id, historial_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 

@app.get("/historial-propietario/{historial_id}", response_model=schemas.HistorialPropietario)
def get_historial_propietario_id_endpoint(
    historial_id: int,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):   
    try:
        require_admin(current_user)
        return historial_service.get_historial_propietario_by_id(historial_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


@app.get("/historial-propietario/inmueble/{inmueble_id}", response_model=list[schemas.HistorialPropietario])
def get_historial_propietario_by_inmueble(
    inmueble_id: int,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.get_historial_propietario_by_inmueble(inmueble_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


@app.get("/historial-propietario/inmueble/{inmueble_id}/actual", response_model=schemas.HistorialPropietario)
def get_current_propietario_by_inmueble(
    inmueble_id: int,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.get_current_propietario_by_inmueble(inmueble_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 
    

@app.patch("/historial-propietario/inmueble/{inmueble_id}/actual/close", response_model=schemas.HistorialPropietario)
def close_current_propietario_by_inmueble(
    inmueble_id: int,
    current_user = Depends(get_current_user),
    historial_service: HistorialService = Depends(get_historial_service)
):
    try:
        require_admin(current_user)
        return historial_service.close_current_propietario(inmueble_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


#------------------------------------
#             Imagen 
#------------------------------------

@app.post("/imagenes/{inmueble_id}", response_model=schemas.Imagen)
async def create_imagen(
    inmueble_id: int,
    descripcion: str = Form(...),
    current_user = Depends(get_current_user),
    file: UploadFile = File(...),
    image_service: ImagenService = Depends(get_imagen_service),
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    try:
        require_admin(current_user)
        # 1) Verificar existencia de inmueble
        inmueble_service.get_inmueble_by_id(inmueble_id)
        

        # 2) Validar tipo MIME
        allowed_types = [
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/webp"
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Only PNG, JPG, JPEG or WEBP images are allowed"
            )

        # 3) Generar nombre único
        _, ext = os.path.splitext(file.filename)

        if not ext:
            ext = ".png"

        ext = ext.lower()

        filename = f"{uuid.uuid4().hex}{ext}"

        save_path = STATIC_PROPERTY_DIR / filename

        # 4) Leer archivo
        try:
            content = await file.read()

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading file: {e}"
            )

        # 5) Validar tamaño
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="File exceeds maximum size of 5MB"
            )

        # 6) Validar contenido real
        if ext in [".jpg", ".jpeg"]:
            if not content.startswith(b"\xff\xd8"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JPG file"
                )

        elif ext == ".png":
            if not content.startswith(b"\x89PNG"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PNG file"
                )

        elif ext == ".webp":
            if b"WEBP" not in content[:20]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid WEBP file"
                )

        # 7) Guardar archivo
        try:
            save_path.write_bytes(content)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error saving file: {e}"
            )

        # 8) Guardar path en BD
        file_path = f"/static/propertyImages/{filename}"

        imagen_data = schemas.ImagenCreate(
            url_archivo=file_path,
            inmueble_id=inmueble_id,
            descripcion=descripcion
        )

        try:
            imagen = image_service.create_imagen(
                imagen_data
            )
            return imagen

        except Exception:
            if save_path.exists():
                save_path.unlink()

            raise
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 
    

@app.put("/imagenes/{imagen_id}", response_model=schemas.Imagen)
def update_imagen(
    imagen_id: int,
    imagen_update: schemas.ImagenUpdate,
    current_user = Depends(get_current_user),
    imagen_service: ImagenService = Depends(get_imagen_service)
):
    
    try:
        require_admin(current_user)
        return imagen_service.update_imagen(imagen_id, imagen_update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


@app.get("/imagenes/{imagen_id}", response_model=schemas.Imagen)
def get_imagen_id_endpoint(
    imagen_id: int,
    imagen_service: ImagenService = Depends(get_imagen_service)
):
    return imagen_service.get_imagen_by_id(imagen_id)


@app.get("/imagenes/inmueble/{inmueble_id}", response_model=list[schemas.Imagen])
def get_imagenes_by_inmueble(
    inmueble_id: int,
    imagen_service: ImagenService = Depends(get_imagen_service)
):
    return imagen_service.get_imagenes_by_inmueble(inmueble_id)


@app.delete("/imagenes/{imagen_id}", response_model=str)
def delete_imagen(
    imagen_id: int,
    current_user = Depends(get_current_user),
    imagen_service: ImagenService = Depends(get_imagen_service)
):
    try:
        require_admin(current_user)
        # 1) Buscar imagen
        imagen = imagen_service.get_imagen_by_id(imagen_id)

        # 2) Obtener nombre del archivo
        try:
            filename = imagen.url_archivo.split("/")[-1]

            file_path = STATIC_PROPERTY_DIR / filename

            # 3) Eliminar archivo físico
            if file_path.exists():
                file_path.unlink()

        except Exception:
            pass

        # 4) Eliminar registro BD
        deleted = imagen_service.delete_imagen(imagen_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Image not found"
            )

        return "Image deleted successfully"
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


#------------------------------------
#             Contacto 
#------------------------------------


@app.post("/contactos", response_model=schemas.Contacto)
def create_contacto(
    contacto: schemas.ContactoCreate,
    contacto_service: ContactoService = Depends(get_contacto_service),
    inmueble_service: InmuebleService = Depends(get_inmueble_service)
):
    try:
        inmueble_service.get_inmueble_by_id(contacto.inmueble_id)
        return contacto_service.create_contacto(contacto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 

@app.get("/contactos/id/{contacto_id}", response_model=schemas.Contacto)
def get_contacto_id_endpoint(
    contacto_id: int,
    current_user = Depends(get_current_user),
    contacto_service: ContactoService = Depends(get_contacto_service)
):
    try:
        require_admin(current_user)
        return contacto_service.get_contacto_by_id(contacto_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 


@app.get("/contactos/inmueble/{id_inmueble}", response_model=list[schemas.Contacto])
def get_contacto_by_inmueble(
    id_inmueble: int,
    current_user = Depends(get_current_user),
    contacto_service: ContactoService = Depends(get_contacto_service)
):
    try:
        require_admin(current_user)
        return contacto_service.get_contactos_by_inmueble(id_inmueble)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 
    

@app.get("/contactos/all", response_model=list[schemas.Contacto])
def get_all_contactos(
    limit: int = 100,
    offset: int = 0,
    current_user = Depends(get_current_user),
    contacto_service: ContactoService = Depends(get_contacto_service)
):
    try:
        require_admin(current_user)
        return contacto_service.get_all_contactos(limit, offset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 

@app.delete("/contactos/{contacto_id}", response_model=bool)
def delete_contacto(
    contacto_id: int,
    current_user = Depends(get_current_user),
    contacto_service: ContactoService = Depends(get_contacto_service)
):
    try:
        require_admin(current_user)
        return contacto_service.delete_contacto(contacto_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 
    

@app.get("/contactos/correo/{correo}", response_model=list[schemas.Contacto])
def get_contactos_by_correo(
    correo: str,
    current_user = Depends(get_current_user),
    contacto_service: ContactoService = Depends(get_contacto_service)
):
    try:
        require_admin(current_user)
        return contacto_service.get_contactos_by_correo(correo)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable, please try again later"
        ) 
    

@app.get("/contactos/search", response_model=list[schemas.Contacto])
def search_contactos(
    q: str,
    current_user = Depends(get_current_user),
    contacto_service: ContactoService = Depends(get_contacto_service)
):
    try:
        require_admin(current_user)
        return contacto_service.search_contactos(q)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        ) 
    