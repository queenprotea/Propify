"""Comunicación con user-service (red interna de Docker)."""
import os
import requests

USER_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8001")
TIMEOUT = 5


def get_usuario(usuario_id: int, auth_header: str):
    """Devuelve los datos del usuario (requiere token válido) o None."""
    if not usuario_id:
        return None
    try:
        r = requests.get(
            f"{USER_URL}/users/{usuario_id}",
            headers={"Authorization": auth_header} if auth_header else {},
            timeout=TIMEOUT,
        )
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    return r.json()
