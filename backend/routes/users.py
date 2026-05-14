from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_approved_user, require_approver, require_staff_editor
from database.session import get_db
from models.user import User, UserRole, UserStatus
from schemas.user import ApproveUserBody, EfetivoReorderBody, UserProfileUpdate, UserPublic
from services import user_service as user_svc

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def read_me(current: User = Depends(get_current_approved_user)) -> UserPublic:
    return UserPublic.model_validate(current)


@router.get("/pending", response_model=list[UserPublic])
def list_pending(
    _: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> list[UserPublic]:
    users = user_svc.list_pending_users(db)
    return [UserPublic.model_validate(u) for u in users]


@router.get("/efetivo", response_model=list[UserPublic])
def list_efetivo(
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> list[UserPublic]:
    users = user_svc.list_efetivo(db)
    return [UserPublic.model_validate(u) for u in users]


@router.put("/efetivo/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_efetivo(
    body: EfetivoReorderBody,
    _: User = Depends(require_staff_editor),
    db: Session = Depends(get_db),
) -> Response:
    try:
        user_svc.reorder_efetivo_patente(db, body.patente, body.ordered_user_ids)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/approve/{user_id}", response_model=UserPublic)
def approve_user(
    user_id: int,
    body: ApproveUserBody,
    _: User = Depends(require_approver),
    db: Session = Depends(get_db),
) -> UserPublic:
    target = user_svc.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if target.status != UserStatus.PENDING:
        raise HTTPException(status_code=400, detail="Usuário não está pendente")
    role_model = UserRole(body.role.value) if body.role is not None else None
    updated = user_svc.approve_or_reject(db, target, body.decision, role_model)
    return UserPublic.model_validate(updated)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_profile(
    user_id: int,
    _: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    target = user_svc.get_user_by_id(db, user_id)
    if not target or target.status != UserStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Policial não encontrado")
    return UserPublic.model_validate(target)


@router.patch("/{user_id}", response_model=UserPublic)
def update_user_profile(
    user_id: int,
    body: UserProfileUpdate,
    current: User = Depends(get_current_approved_user),
    db: Session = Depends(get_db),
) -> UserPublic:
    target = user_svc.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if target.status != UserStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Perfil indisponível")
    try:
        updated = user_svc.update_user_profile(db, current, target, body)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    return UserPublic.model_validate(updated)
