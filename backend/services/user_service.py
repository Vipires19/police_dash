from sqlalchemy import func, select
from sqlalchemy.orm import Session

from auth.password import hash_password, verify_password
from core.ranks import patente_sort_key
from models.user import User, UserRole, UserStatus
from schemas.user import UserProfileUpdate, UserRegister


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalars(select(User).where(User.id == user_id)).first()


def _next_display_order(db: Session, patente: str, exclude_user_id: int | None = None) -> int:
    key = patente.strip().lower()
    stmt = select(func.coalesce(func.max(User.display_order), -1)).where(
        User.status == UserStatus.APPROVED,
        func.lower(func.trim(User.patente)) == key,
    )
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    m = db.execute(stmt).scalar_one()
    return int(m) + 1


def create_pending_user(db: Session, data: UserRegister) -> User:
    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        patente=data.patente.strip(),
        nome_guerra=data.nome_guerra.strip(),
        role=UserRole.ESTAGIO,
        status=UserStatus.PENDING,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email.lower())
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def list_pending_users(db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User).where(User.status == UserStatus.PENDING).order_by(User.created_at.asc())
        ).all()
    )


def list_efetivo(db: Session) -> list[User]:
    users = list(
        db.scalars(select(User).where(User.status == UserStatus.APPROVED)).all()
    )
    users.sort(
        key=lambda u: (
            patente_sort_key(u.patente)[0],
            u.display_order,
            u.nome_guerra.lower(),
        )
    )
    return users


def approve_or_reject(db: Session, target: User, decision: str, role: UserRole | None) -> User:
    if decision == "approve":
        target.display_order = _next_display_order(db, target.patente, exclude_user_id=target.id)
        target.status = UserStatus.APPROVED
        if role is not None:
            target.role = role
    else:
        target.status = UserStatus.REJECTED
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def update_user_profile(
    db: Session,
    actor: User,
    target: User,
    data: UserProfileUpdate,
) -> User:
    staff_editors = {UserRole.ADMIN, UserRole.N90, UserRole.TAT_CMD}
    is_staff = actor.role in staff_editors
    if not is_staff and target.id != actor.id:
        msg = "Sem permissão para editar este perfil"
        raise PermissionError(msg)
    payload = data.model_dump(exclude_unset=True)
    if not is_staff:
        payload.pop("is_active", None)
    if not payload:
        return target
    for field, value in payload.items():
        setattr(target, field, value)
    if "patente" in payload:
        target.display_order = _next_display_order(db, target.patente, exclude_user_id=target.id)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def reorder_efetivo_patente(db: Session, patente: str, ordered_user_ids: list[int]) -> None:
    key = patente.strip().lower()
    expected = list(
        db.scalars(
            select(User).where(
                User.status == UserStatus.APPROVED,
                func.lower(func.trim(User.patente)) == key,
            )
        ).all()
    )
    expected_ids = {u.id for u in expected}
    if expected_ids != set(ordered_user_ids):
        msg = "Lista de IDs não corresponde ao efetivo desta patente"
        raise ValueError(msg)
    by_id = {u.id: u for u in expected}
    for i, uid in enumerate(ordered_user_ids):
        by_id[uid].display_order = i
    db.add_all(expected)
    db.commit()


def ensure_bootstrap_admin(db: Session, email: str, password: str, patente: str, nome_guerra: str) -> None:
    if get_user_by_email(db, email.lower()):
        return
    admin = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        patente=patente,
        nome_guerra=nome_guerra,
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED,
        display_order=0,
        is_active=True,
    )
    db.add(admin)
    db.commit()
