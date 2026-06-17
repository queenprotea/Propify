import os
import requests
from urllib.parse import quote

PROPERTY_URL = os.getenv("PROPERTY_SERVICE_URL", "http://property_service:8002")
TIMEOUT = 5


def get_inmueble(inmueble_id: int):
    try:
        r = requests.get(f"{PROPERTY_URL}/inmuebles/id/{inmueble_id}", timeout=TIMEOUT)
    except requests.RequestException as e:
        raise RuntimeError(f"No se pudo contactar al servicio de inmuebles: {e}")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def estado_inmueble(inmueble: dict) -> str:
    return ((inmueble or {}).get("estado_inmueble") or {}).get("valor", "")


def get_ubicacion(ubicacion_id: int):
    if not ubicacion_id:
        return None
    try:
        r = requests.get(f"{PROPERTY_URL}/ubicaciones/id/{ubicacion_id}", timeout=TIMEOUT)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    return r.json()


def set_estado_inmueble(inmueble_id: int, estado: str, auth_header: str):
    """Actualiza el estado del inmueble requiere token de administrador"""
    try:
        r = requests.patch(
            f"{PROPERTY_URL}/inmuebles/{inmueble_id}/estado-valor/{quote(estado)}",
            headers={"Authorization": auth_header},
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"No se pudo actualizar el estado del inmueble: {e}")
    r.raise_for_status()
    return r.json()
