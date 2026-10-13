from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.rate_limit import require_registration_rate_limit
from app.domains.iam.registration.dependencies import get_registration_service
from app.domains.iam.registration.exceptions import (
    DuplicateRegistrationError,
    InvalidRegistrationReferenceError,
)
from app.domains.iam.registration.schemas import (
    RegistrationRequest,
    RegistrationResponse,
)
from app.domains.iam.registration.service import RegistrationService

router = APIRouter()


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
