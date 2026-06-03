from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi import UploadFile, File
from pathlib import Path
from app.enums import TipoInmueble, EstadoInmueble

from app.database import get_db
from app.security import get_current_user, get_current_admin
from app.services.property_service import PropertyService, get_property_service
from app.repositories import property_repository
from app import schemas, audit
from app.enums import TipoInmueble, OperacionInmueble, UsoInmueble, EstadoInmueble
import os
import uuid

app = FastAPI(title="Property Service")


@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado. Inténtalo de nuevo más tarde."},
    )


# --- Catálogos / categorías (normalizados en BD) ---
@app.get("/categorias")
def get_categorias(inmueble_service: PropertyService = Depends(get_property_service)):
    """Catálogos para poblar selectores y filtros (fuente: tablas de catálogo)."""
    return property_repository.get_catalogos(inmueble_service.db)


@app.post("/categorias/{catalogo}", summary="Agregar un valor de catálogo (administrador)")
def add_categoria(catalogo: str, body: dict,
                  current_user=Depends(get_current_admin),
                  inmueble_service: PropertyService = Depends(get_property_service)):
    if catalogo not in property_repository.CATALOG_MODELS:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    try:
        row = property_repository.add_catalog(inmueble_service.db, catalogo, str(body.get("valor", "")))
        return {"id": row.id, "valor": row.valor}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@app.delete("/categorias/{catalogo}/{valor}", summary="Eliminar un valor de catálogo (administrador)")
def delete_categoria(catalogo: str, valor: str,
                     current_user=Depends(get_current_admin),
                     inmueble_service: PropertyService = Depends(get_property_service)):
    if catalogo not in property_repository.CATALOG_MODELS:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    try:
        if not property_repository.delete_catalog(inmueble_service.db, catalogo, valor):
            raise HTTPException(status_code=404, detail="Valor no encontrado")
        return {"message": "Valor eliminado"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

STATIC_PROPERTY_DIR = Path("/app/static/propertyImages")
STATIC_PROPERTY_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# --- API Endpoints ---
@app.post("/inmuebles", response_model=schemas.Inmueble)
def create_inmueble(
    inmueble: schemas.InmuebleCreate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        creado = inmueble_service.create_inmueble(inmueble)
        audit.registrar(inmueble_service.db, int(current_user["sub"]), "inmueble_creado",
                        "Inmueble", creado.id, valor_nuevo=creado.titulo,
                        detalle=f"{creado.tipo}/{creado.operacion}")
        return creado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/inmuebles/{inmueble_id}", response_model=schemas.Inmueble)
def update_inmueble(
    inmueble_id: int,
    inmueble_update: schemas.InmuebleUpdate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        actualizado = inmueble_service.update_inmueble(inmueble_id, inmueble_update)
        cambios = inmueble_update.model_dump(exclude_none=True)
        audit.registrar(inmueble_service.db, int(current_user["sub"]), "inmueble_modificado",
                        "Inmueble", inmueble_id, valor_nuevo=str(cambios)[:500],
                        detalle="modificación de inmueble")
        return actualizado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/inmuebles/all", response_model=list[schemas.Inmueble])
def get_all_inmuebles(
    limit: int = 100,
    offset: int = 0,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_all_inmuebles(limit, offset)


@app.get("/inmuebles/id/{inmueble_id}", response_model=schemas.Inmueble)
def get_inmueble_id_endpoint(
    inmueble_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_inmueble_by_id(inmueble_id)


@app.get("/inmuebles/disponible", response_model=list[schemas.Inmueble])
def get_inmuebles_disponibles(
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_disponible_inmuebles()


@app.get("/inmuebles/tipo/{tipo}", response_model=list[schemas.Inmueble])
def get_inmuebles_by_tipo(
    tipo: str,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_inmuebles_by_tipo(tipo)


@app.get("/inmuebles/propietario/{id_pro}", response_model=list[schemas.Inmueble])
def get_inmuebles_by_propietario(
    id_pro: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_inmuebles_by_propietario(id_pro)


@app.get("/inmuebles/titulo/{titulo}", response_model=list[schemas.Inmueble])
def get_inmuebles_by_titulo(
    titulo: str,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_inmuebles_by_titulo(titulo)


@app.get("/inmuebles/descripcion/{des}", response_model=list[schemas.Inmueble])
def get_inmuebles_by_descripcion(
    des: str,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_inmuebles_by_descripcion(des)


@app.patch("/inmuebles/id/{inmueble_id}/status/{status}", response_model=schemas.Inmueble)
def update_inmueble_status(
    inmueble_id: int,
    status: EstadoInmueble,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    anterior = inmueble_service.get_inmueble_by_id(inmueble_id).estado
    actualizado = inmueble_service.update_inmueble_status(inmueble_id, status)
    audit.registrar(inmueble_service.db, int(current_user["sub"]), "inmueble_estado",
                    "Inmueble", inmueble_id, valor_anterior=anterior, valor_nuevo=status.value,
                    detalle="cambio de estado del inmueble")
    return actualizado


@app.delete("/inmuebles/{inmueble_id}")
def delete_inmueble(
    inmueble_id: int,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    titulo = inmueble_service.get_inmueble_by_id(inmueble_id).titulo
    inmueble_service.delete_inmueble(inmueble_id)
    audit.registrar(inmueble_service.db, int(current_user["sub"]), "inmueble_eliminado",
                    "Inmueble", inmueble_id, valor_anterior=titulo, detalle="eliminación de inmueble")
    return {"message": "Property deleted successfully"}


#------------------------------------
#            ubicacion 
#------------------------------------

@app.post("/ubicaciones", response_model=schemas.Ubicacion)
def create_ubicacion(
    ubicacion: schemas.UbicacionCreate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        return inmueble_service.create_ubicacion(ubicacion)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/ubicaciones/{ubicacion_id}", response_model=schemas.Ubicacion)
def update_ubicacion(
    ubicacion_id: int,
    ubicacion_update: schemas.UbicacionUpdate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        return inmueble_service.update_ubicacion(ubicacion_id, ubicacion_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/ubicaciones/{ubicacion_id}", response_model=schemas.Ubicacion)
def get_ubicacion_id_endpoint(
    ubicacion_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_ubicacion_by_id(ubicacion_id)


@app.get("/ubicaciones/completa/{dircom}", response_model=list[schemas.Ubicacion])
def get_ubicaciones_by_direccion_completa(
    dircom: str,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_ubicaciones_by_direccion_completa(dircom)


#------------------------------------
#         Historial Estado 
#------------------------------------

@app.post("/historial", response_model=schemas.Historial)
def create_historial(
    historial: schemas.HistorialCreate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        return inmueble_service.create_historial_estado(historial)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/historial/{historial_id}", response_model=schemas.Historial)
def update_historial(
    historial_id: int,
    historial_update: schemas.HistorialUpdate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        return inmueble_service.update_historial_estado(historial_id, historial_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/historial/{historial_id}", response_model=schemas.Historial)
def get_historial_id_endpoint(
    historial_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_historial_by_id(historial_id)


@app.get("/historial/inmueble/{inmueble_id}", response_model=list[schemas.Historial])
def get_historial_by_inmueble(
    inmueble_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_historial_by_inmueble(inmueble_id)


@app.get("/historial/inmueble/{inmueble_id}/actual", response_model=schemas.Historial)
def get_current_historial_by_inmueble(
    inmueble_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_current_historial_by_inmueble(inmueble_id)


#------------------------------------
#             Imagen 
#------------------------------------

@app.post("/imagenes", response_model=schemas.Imagen)
async def create_imagen(
    inmueble_id: int = Form(...),
    texto_alternativo: str = Form(..., min_length=1, max_length=255),
    current_user = Depends(get_current_admin),
    file: UploadFile = File(...),
    inmueble_service: PropertyService = Depends(get_property_service)
):

    # 1) Verificar existencia de inmueble
    inmueble = inmueble_service.get_inmueble_by_id(inmueble_id)

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
        texto_alternativo=texto_alternativo,
        inmueble_id=inmueble_id
    )

    return inmueble_service.create_imagen(imagen_data)

@app.put("/imagenes/{imagen_id}", response_model=schemas.Imagen)
def update_imagen(
    imagen_id: int,
    imagen_update: schemas.ImagenUpdate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        return inmueble_service.update_imagen(imagen_id, imagen_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/imagenes/{imagen_id}", response_model=schemas.Imagen)
def get_imagen_id_endpoint(
    imagen_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_imagen_by_id(imagen_id)


@app.get("/imagenes/inmueble/{inmueble_id}", response_model=list[schemas.Imagen])
def get_imagenes_by_inmueble(
    inmueble_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_imagenes_by_inmueble(inmueble_id)


@app.delete("/imagenes/{imagen_id}", response_model=str)
def delete_imagen(
    imagen_id: int,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):

    # 1) Buscar imagen
    imagen = inmueble_service.get_imagen_by_id(imagen_id)

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
    deleted = inmueble_service.delete_imagen(imagen_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    return "Image deleted successfully"


#------------------------------------
#             Contacto 
#------------------------------------


@app.post("/contactos", response_model=schemas.Contacto)
def create_contacto(
    contacto: schemas.ContactoCreate,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    # Público: cualquier interesado puede enviar el formulario de contacto.
    inmueble_service.get_inmueble_by_id(contacto.inmueble_id)

    try:
        return inmueble_service.create_contacto(contacto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/contactos/{contacto_id}", response_model=schemas.Contacto)
def update_contacto(
    contacto_id: int,
    contacto_update: schemas.ContactoUpdate,
    current_user = Depends(get_current_admin),
    inmueble_service: PropertyService = Depends(get_property_service)
):
    try:
        return inmueble_service.update_contacto(contacto_id, contacto_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/contactos/id/{contacto_id}", response_model=schemas.Contacto)
def get_contacto_id_endpoint(
    contacto_id: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_contacto_by_id(contacto_id)


@app.get("/contactos/inmueble/{id_inmueble}", response_model=list[schemas.Contacto])
def get_contacto_by_inmueble(
    id_inmueble: int,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_contactos_by_inmueble(id_inmueble)


@app.get("/contactos/all", response_model=list[schemas.Contacto])
def get_all_contactos(
    limit: int = 100,
    offset: int = 0,
    inmueble_service: PropertyService = Depends(get_property_service)
):
    return inmueble_service.get_all_contactos(limit, offset)
