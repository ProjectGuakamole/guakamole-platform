from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.domain.auth.config import AuthSettings
from app.domain.auth.dependencies import build_auth_settings
from app.domain.auth.password_hasher import PwdlibPasswordHasher
from app.domain.iam.organizations.registration_exceptions import (
    DuplicateRegistrationError,
    InvalidRegistrationReferenceError,
)
from app.domain.iam.organizations.registration_repositories import (
    SqlAlchemyRegistrationRepository,
)
from app.domain.iam.organizations.registration_schemas import (
    RegistrationRequest,
    RegistrationResponse,
)
from app.domain.iam.organizations.registration_services import RegistrationService
from app.domain.iam.users.dependencies import get_db_session

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
    service: Annotated[RegistrationService, Depends(get_registration_service)],
) -> RegistrationResponse:
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
