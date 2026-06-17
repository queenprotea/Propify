"""Infraestructura de almacenamiento de archivos de contratos (PDF y comprobantes)."""
from pathlib import Path
import uuid

CONTRACTS_DIR = Path("/app/contracts")
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)


def guardar_pdf_original(contrato_id: int, pdf_bytes: bytes) -> Path:
    ruta = CONTRACTS_DIR / f"contrato_{contrato_id}_original.pdf"
    ruta.write_bytes(pdf_bytes)
    return ruta


def guardar_firmado(contrato_id: int, contenido: bytes) -> Path:
    ruta = CONTRACTS_DIR / f"contrato_{contrato_id}_firmado_{uuid.uuid4().hex[:8]}.pdf"
    ruta.write_bytes(contenido)
    return ruta


def guardar_comprobante(contrato_id: int, contenido: bytes, extension: str) -> Path:
    ruta = CONTRACTS_DIR / f"comprobante_{contrato_id}_{uuid.uuid4().hex[:8]}{extension}"
    ruta.write_bytes(contenido)
    return ruta
