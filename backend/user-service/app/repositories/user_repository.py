from sqlalchemy.orm import Session
from app import models, schemas
from app.security import get_password_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import or_

def get_user_by_correo(db: Session, correo: str):
    """Find a user by their email address."""
    return db.query(models.Usuario).filter(models.Usuario.correo == correo).first()

def get_user_by_nombre(db: Session, nombre: str):
    """Find a user by their name"""
    return db.query(models.Usuario).filter(models.Usuario.nombre == nombre).first()

def get_user_by_telefono(db: Session, telefono: str):
    """Find a user by their phone"""
    return db.query(models.Usuario).filter(models.Usuario.telefono == telefono).first()


def get_user_by_id(db: Session, user_id: int):
    """Find a user by their ID."""
    try:
        return db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    except OperationalError as e:
        raise ConnectionError("Database connection error - please try again later")
    except Exception as e:
        raise e
    

def create_user(db: Session, usuario: schemas.UserCreate):
    try:
        new_user = models.Usuario(
            correo=usuario.correo,
            password=get_password_hash(usuario.password),
            nombre=usuario.nombre,
            telefono=usuario.telefono,
            is_active=True,
            is_admin=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise ValueError("User with this email or username already registered")
    except OperationalError as e:
        db.rollback()
        raise ConnectionError("Database connection error - please try again later")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception("Database error - please try again later")
    except Exception as e:
        db.rollback()
        raise e


def create_user_admin(db: Session, usuario: schemas.UserCreate):
    try:
        new_user = models.Usuario(
            correo=usuario.correo,
            password=get_password_hash(usuario.password),
            nombre=usuario.nombre,
            telefono=usuario.telefono,
            is_active=True,
            is_admin=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise ValueError("User with this email or username already registered")
    except OperationalError as e:
        db.rollback()
        raise ConnectionError("Database connection error - please try again later")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception("Database error - please try again later")
    except Exception as e:
        db.rollback()
        raise e

def update_user_password(db: Session, user_id: int, new_password: str):
    try: 
        user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
        if user: 
            user.password = get_password_hash(new_password)
            db.commit()
            db.refresh(user)
        return user
    except OperationalError as e:
        db.rollback()
        raise ConnectionError("Database connection error, please try again later")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception("Database error, please try again later")
    except Exception as e:
        db.rollback()
        raise e


def get_all_users(db: Session, limit : int = 100, offset: int = 0):
    try:
        safe_limit = min(limit, 1000)
        return (
            db.query(models.Usuario)
            .offset(offset)
            .limit(safe_limit)
            .all()
        )
    except OperationalError as e:
        raise ConnectionError("Database connection error, please try again later")
    except Exception as e:
        raise e
    
def get_active_users(db: Session, limit, offset):
    try:
        safe_limit = min (limit, 1000)
        return db.query(models.Usuario).filter(models.Usuario.is_active == True).offset(offset).limit(safe_limit).all()
    except OperationalError as e:
        raise ConnectionError("Database connection error, please try again later")
    except Exception as e:
        raise e


def count_active_admins(db: Session) -> int:
    return db.query(models.Usuario).filter(
        models.Usuario.is_admin == True, models.Usuario.is_active == True
    ).count()


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    try:
        db_user = get_user_by_id(db, user_id)
        if not db_user:
            return None

        # Solo actualiza los campos que fueron enviados
        if user_update.nombre is not None:
            db_user.nombre = user_update.nombre

        if user_update.correo is not None:
            db_user.correo = user_update.correo

        if user_update.password is not None:
            db_user.password = get_password_hash(user_update.password)
        
        if user_update.telefono is not None:
            db_user.telefono = user_update.telefono

        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        raise ValueError("El correo o el teléfono ya están registrados por otro usuario")
    except OperationalError as e:
        raise ConnectionError("Database connection error, please try again later")
    except Exception as e:
        raise e


def update_user_admin(db: Session, user_id: int, user_update: schemas.UserUpdate):
    try:
        db_user = get_user_by_id(db, user_id)
        if not db_user:
            return None

        # Solo actualiza los campos que fueron enviados
        if user_update.nombre is not None:
            db_user.nombre = user_update.nombre

        if user_update.correo is not None:
            db_user.correo = user_update.correo

        if user_update.password is not None:
            db_user.password = get_password_hash(user_update.password)
        
        if user_update.telefono is not None:
            db_user.telefono = user_update.telefono

        if user_update.is_active is not None:
            db_user.is_active = user_update.is_active

        if user_update.is_admin is not None:
            db_user.is_admin = user_update.is_admin

        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        raise ValueError("El correo o el teléfono ya están registrados por otro usuario")
    except OperationalError as e:
        raise ConnectionError("Database connection error, please try again later")
    except Exception as e:
        raise e


def search_users(db: Session, query: str):
    try:
        if not query:
            return []
        
        filters = [
            models.Usuario.nombre.ilike(f"%{query}%"),
            models.Usuario.correo.ilike(f"%{query}%"),
            models.Usuario.telefono.ilike(f"%{query}%"),
        ]

        q = db.query(models.Usuario).filter(or_(*filters))

        return q.all()
    except OperationalError as e:
        raise ConnectionError("Database connection error, please try again later")
    except Exception as e:
        raise e


def deactivate_user(db: Session, user_id: int):
    try:
        user = db.query(models.Usuario)\
            .filter(models.Usuario.id == user_id)\
            .first()

        if not user:
            return None

        user.is_active = False
        db.commit()
        db.refresh(user)

        return user

    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )

def activate_user(db: Session, user_id: int):
    try:
        user = db.query(models.Usuario)\
            .filter(models.Usuario.id == user_id)\
            .first()

        if not user:
            return None

        user.is_active = True
        db.commit()
        db.refresh(user)

        return user
    
    except OperationalError:
        db.rollback()
        raise ConnectionError(
            "Database connection error, please try again later"
        )

    except SQLAlchemyError:
        db.rollback()
        raise Exception(
            "Database error, please try again later"
        )


#---------------------------------
#--------ESTADO VISITAS-----------
#---------------------------------

def get_state_by_id(db:Session, state_id:int):
    return db.query(models.EstadoVisita).filter(models.EstadoVisita.id == state_id).first()

def get_all_states(db:Session):
    return db.query(models.EstadoVisita).all()

#---------------------------------
#----------VISITAS---------------- 
#---------------------------------

def get_visit_by_id(db: Session, visit_id: int):
    return db.query(models.Visita).filter(models.Visita.id == visit_id).first()


def get_visits_by_user(db: Session, user_id: int):
    return db.query(models.Visita).filter(models.Visita.usuario_id == user_id).all()


def get_visits_by_property(db: Session, property_id: int):
    return db.query(models.Visita).filter(models.Visita.inmueble_id == property_id).all()


CONFLICT_MSG = (
    "El inmueble ya tiene una visita agendada para esa fecha y hora. "
    "Elige otro horario."
)


def _estados_activos_ids(db: Session):
    """Ids de estados que ocupan un horario (programada, confirmada)."""
    filas = (
        db.query(models.EstadoVisita.id)
        .filter(models.EstadoVisita.valor.in_(["programada", "confirmada"]))
        .all()
    )
    return [f[0] for f in filas]


def _hay_conflicto_visita(db: Session, inmueble_id, fecha, estado_id, exclude_id=None):
    """True si ya existe una visita ACTIVA para ese inmueble en esa fecha/hora."""
    activos = _estados_activos_ids(db)
    # Solo las visitas activas ocupan el horario; las canceladas/realizadas no.
    if estado_id not in activos:
        return False
    q = (
        db.query(models.Visita)
        .filter(
            models.Visita.inmueble_id == inmueble_id,
            models.Visita.fecha == fecha,
            models.Visita.estado_id.in_(activos),
        )
    )
    if exclude_id is not None:
        q = q.filter(models.Visita.id != exclude_id)
    return db.query(q.exists()).scalar()


def create_visit(db: Session, visit: schemas.VisitaCreate):
    # Validación a nivel de aplicación
    if _hay_conflicto_visita(db, visit.inmueble_id, visit.fecha, visit.estado_id):
        raise ValueError(CONFLICT_MSG)

    db_visit = models.Visita(
        fecha=visit.fecha,
        estado_id=visit.estado_id,
        usuario_id=visit.usuario_id,
        inmueble_id=visit.inmueble_id,
    )
    db.add(db_visit)
    try:
        db.commit()
    except IntegrityError:
        # Red de seguridad: el índice único parcial de la BD detectó el conflicto.
        db.rollback()
        raise ValueError(CONFLICT_MSG)
    db.refresh(db_visit)
    return db_visit


def update_visit(db: Session, visit_id: int, visit_update: schemas.VisitaUpdate):
    db_visit = get_visit_by_id(db, visit_id)
    if not db_visit:
        return None

    # Valores efectivos tras la actualización (para validar el conflicto)
    nuevo_inmueble = visit_update.inmueble_id if visit_update.inmueble_id is not None else db_visit.inmueble_id
    nuevo_estado = visit_update.estado_id if visit_update.estado_id is not None else db_visit.estado_id
    nueva_fecha = visit_update.fecha if visit_update.fecha is not None else db_visit.fecha

    if _hay_conflicto_visita(db, nuevo_inmueble, nueva_fecha, nuevo_estado, exclude_id=visit_id):
        raise ValueError(CONFLICT_MSG)

    db_visit.inmueble_id = nuevo_inmueble
    db_visit.estado_id = nuevo_estado
    db_visit.fecha = nueva_fecha
    if visit_update.usuario_id is not None:
        db_visit.usuario_id = visit_update.usuario_id

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError(CONFLICT_MSG)
    db.refresh(db_visit)
    return db_visit


def get_all_visits(db: Session):
    return db.query(models.Visita).all()


def get_visits_by_estado_id(
    db: Session,
    estado_id: int
):
    return (
        db.query(models.Visita)
        .join(models.EstadoVisita)
        .filter(models.EstadoVisita.id == estado_id)
        .all()
    )

def get_visits_by_estado(
    db: Session,
    estado: str
):
    return (
        db.query(models.Visita)
        .join(models.EstadoVisita)
        .filter(models.EstadoVisita.valor == estado)
        .all()
    )
