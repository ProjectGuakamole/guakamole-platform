from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rate_limit import require_registration_rate_limit
from app.domains.auth.shared.config import AuthSettings
from app.domains.auth.shared.dependencies import build_auth_settings
from app.domains.auth.shared.password_hasher import PwdlibPasswordHasher
from app.domains.iam.registration.exceptions import (
    DuplicateRegistrationError,
    InvalidRegistrationReferenceError,
)
from app.domains.iam.registration.repository import SqlAlchemyRegistrationRepository
from app.domains.iam.registration.schemas import (
    RegistrationRequest,
    RegistrationResponse,
)
from app.domains.iam.registration.service import RegistrationService
from app.domains.iam.users.dependencies import get_db_session

router = APIRouter()


def get_registration_service(
    session: Annotated[Session, Depends(get_db_session)],
    auth_settings: Annotated[AuthSettings, Depends(build_auth_settings)],
) -> RegistrationService:
    return RegistrationService(
        repository=SqlAlchemyRegistrationRepository(session),
        password_hasher=PwdlibPasswordHasher(),
        auth_settings=auth_settings,
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
)
def register_organization(
    request: RegistrationRequest,
    _rate_limit: Annotated[None, Depends(require_registration_rate_limit)],
    service: Annotated[RegistrationService, Depends(get_registration_service)],
) -> RegistrationResponse:
    _ = _rate_limit
    try:
        return service.register(request)
    except DuplicateRegistrationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede completar el registro con los datos proporcionados.",
        ) from error
    except InvalidRegistrationReferenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos de registro inválidos.",
        ) from error
