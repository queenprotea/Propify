"""Registro de auditoría (tabla compartida "Auditoria") desde property-service."""
from sqlalchemy import text


def registrar(db, usuario_id, accion, entidad, entidad_id=None,
              valor_anterior=None, valor_nuevo=None, detalle=None):
    try:
        db.execute(text(
            'INSERT INTO "Auditoria" (usuario_id, accion, entidad, entidad_id, '
            'valor_anterior, valor_nuevo, detalle) '
            'VALUES (:u, :a, :e, :eid, :va, :vn, :d)'
        ), {"u": usuario_id, "a": accion, "e": entidad, "eid": entidad_id,
            "va": valor_anterior, "vn": valor_nuevo, "d": detalle})
        db.commit()
    except Exception:
        db.rollback()  # la auditoría nunca debe romper la operación principal
