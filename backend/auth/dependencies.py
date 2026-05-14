from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.jwt_utils import decode_token_safe
from database.session import get_db
from models.user import User, UserRole, UserStatus
from services import user_service as user_svc

security = HTTPBearer()

APPROVER_ROLES = {UserRole.ADMIN, UserRole.N90, UserRole.TAT_CMD}

STAFF_EDITOR_ROLES = APPROVER_ROLES


def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_token),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token_safe(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = user_svc.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return user


def get_current_approved_user(current: User = Depends(get_current_user)) -> User:
    if current.status != UserStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta não aprovada ou rejeitada",
        )
    if not current.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta inativa. Contate o comando.",
        )
    return current


def require_approver(current: User = Depends(get_current_approved_user)) -> User:
    if current.role not in APPROVER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para aprovar usuários",
        )
    return current


def require_staff_editor(current: User = Depends(get_current_approved_user)) -> User:
    if current.role not in STAFF_EDITOR_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para editar efetivo ou perfis de terceiros",
        )
    return current


VEHICLE_EDITOR_ROLES = {UserRole.ADMIN, UserRole.N90, UserRole.TAT_CMD, UserRole.BRACAL}


def require_vehicle_editor(current: User = Depends(get_current_approved_user)) -> User:
    if current.role not in VEHICLE_EDITOR_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para criar ou alterar viaturas",
        )
    return current
