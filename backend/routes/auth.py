from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth.jwt_utils import create_access_token
from database.session import get_db
from models.user import UserStatus
from schemas.user import TokenResponse, UserLogin, UserPublic, UserRegister
from services import user_service as user_svc

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)) -> UserPublic:
    if user_svc.get_user_by_email(db, data.email.lower()):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    user = user_svc.create_pending_user(db, data)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = user_svc.authenticate(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    if user.status != UserStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta pendente de aprovação ou rejeitada",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta inativa. Contate o comando.",
        )
    token = create_access_token(str(user.id), {"role": user.role.value})
    return TokenResponse(access_token=token)
