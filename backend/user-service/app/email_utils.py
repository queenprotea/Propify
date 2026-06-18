"""Envío de correos de verificación.

Si hay SMTP configurado (SMTP_HOST) se envía un correo real; si no,
el enlace se imprime en el log del servicio (modo desarrollo).
"""
import os
import smtplib
from email.mime.text import MIMEText

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "no-reply@propify.com")


def enviar_verificacion(correo: str, nombre: str, token: str) -> None:
    enlace = f"{FRONTEND_URL}/verificar-correo?token={token}"
    if not SMTP_HOST:
        print(f"[verificacion] Enlace para {correo}: {enlace}", flush=True)
        return
    cuerpo = (
        f"Hola {nombre},\n\n"
        "Gracias por registrarte en Propify. Confirma tu correo electrónico "
        f"abriendo este enlace:\n\n{enlace}\n\n"
        "Si no creaste esta cuenta, ignora este mensaje."
    )
    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = "Verifica tu correo — Propify"
    msg["From"] = SMTP_FROM
    msg["To"] = correo
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            if SMTP_USER:
                s.login(SMTP_USER, SMTP_PASSWORD)
            s.sendmail(SMTP_FROM, [correo], msg.as_string())
    except Exception as e:
        # El registro no debe fallar por un problema de correo.
        print(f"[verificacion] No se pudo enviar a {correo}: {e}. Enlace: {enlace}", flush=True)
