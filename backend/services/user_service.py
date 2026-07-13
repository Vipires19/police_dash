from sqlalchemy import func, select
from sqlalchemy.orm import Session

from auth.password import hash_password, verify_password
from core.ranks import patente_sort_key
from models.user import OrganizationalUnit, User, UserRole, UserStatus
from schemas.user import UserProfileUpdate, UserRegister

STAFF_EDITOR_ROLES = {UserRole.ADMIN, UserRole.CMD_TATICO, UserRole.N90, UserRole.TAT_CMD}
COMPANY_EFETIVO_VIEW_ROLES = {UserRole.ADMIN, UserRole.CMD_TATICO}


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalars(select(User).where(User.id == user_id)).first()


def _next_display_order(db: Session, patente: str, exclude_user_id: int | None = None) -> int:
    key = patente.strip().lower()
    stmt = select(func.coalesce(func.max(User.display_order), -1)).where(
        User.status == UserStatus.APPROVED,
        User.is_active.is_(True),
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
        organizational_unit=OrganizationalUnit.FIRST_PLATOON,
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


def _efetivo_sort_key(u: User) -> tuple:
    return (
        patente_sort_key(u.patente)[0],
        u.display_order,
        u.nome_guerra.lower(),
    )


def list_efetivo(db: Session, viewer: User) -> list[User]:
    """Lista efetivo ativo aprovado, escopado pela unidade do visualizador.

    ADMIN e CMD_TATICO veem toda a Companhia. Demais roles veem apenas a própria unidade.
    Usuários inativos são excluídos das listas operacionais (histórico permanece intacto).
    """
    stmt = select(User).where(
        User.status == UserStatus.APPROVED,
        User.is_active.is_(True),
    )
    if viewer.role not in COMPANY_EFETIVO_VIEW_ROLES:
        stmt = stmt.where(User.organizational_unit == viewer.organizational_unit)
    users = list(db.scalars(stmt).all())
    users.sort(key=_efetivo_sort_key)
    return users


def approve_or_reject(
    db: Session,
    target: User,
    decision: str,
    role: UserRole | None,
    organizational_unit: OrganizationalUnit | None = None,
) -> User:
    if decision == "approve":
        target.display_order = _next_display_order(db, target.patente, exclude_user_id=target.id)
        target.status = UserStatus.APPROVED
        if role is not None:
            target.role = role
        if organizational_unit is not None:
            target.organizational_unit = organizational_unit
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
    staff_editors = STAFF_EDITOR_ROLES
    is_staff = actor.role in staff_editors
    if not is_staff and target.id != actor.id:
        msg = "Sem permissão para editar este perfil"
        raise PermissionError(msg)
    payload = data.model_dump(exclude_unset=True)
    if not is_staff:
        payload.pop("is_active", None)
        payload.pop("role", None)
        payload.pop("organizational_unit", None)
    role_value = payload.pop("role", None)
    unit_value = payload.pop("organizational_unit", None)
    if role_value is not None:
        if not is_staff:
            msg = "Sem permissão para alterar role"
            raise PermissionError(msg)
        if target.id == actor.id:
            msg = "Não é permitido alterar a própria role"
            raise PermissionError(msg)
        target.role = UserRole(role_value)
    if unit_value is not None:
        if not is_staff:
            msg = "Sem permissão para alterar unidade organizacional"
            raise PermissionError(msg)
        target.organizational_unit = OrganizationalUnit(unit_value)
    if not payload:
        if role_value is None and unit_value is None:
            return target
        db.add(target)
        db.commit()
        db.refresh(target)
        return target
    for field, value in payload.items():
        setattr(target, field, value)
    if "patente" in payload:
        target.display_order = _next_display_order(db, target.patente, exclude_user_id=target.id)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def reorder_efetivo_patente(
    db: Session,
    actor: User,
    patente: str,
    ordered_user_ids: list[int],
) -> None:
    target_rank, _ = patente_sort_key(patente)
    stmt = select(User).where(
        User.status == UserStatus.APPROVED,
        User.is_active.is_(True),
    )
    if actor.role not in COMPANY_EFETIVO_VIEW_ROLES:
        stmt = stmt.where(User.organizational_unit == actor.organizational_unit)
    approved = list(db.scalars(stmt).all())
    expected = [u for u in approved if patente_sort_key(u.patente)[0] == target_rank]
    expected_ids = {u.id for u in expected}
    submitted_ids = set(ordered_user_ids)
    if expected_ids != submitted_ids or len(ordered_user_ids) != len(expected):
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
        organizational_unit=OrganizationalUnit.COMPANY_ADMIN,
        status=UserStatus.APPROVED,
        display_order=0,
        is_active=True,
    )
    db.add(admin)
    db.commit()
