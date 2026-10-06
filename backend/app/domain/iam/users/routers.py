"""Router HTTP para el piloto IAM/users."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.iam.access.tenant_context import TenantContext, TenantContextError
from app.domain.iam.users.dependencies import (
    get_list_organization_users_service,
    get_tenant_context,
    get_user_list_query,
)
from app.domain.iam.users.schemas import OrganizationUserListResponse, UserListQuery
from app.domain.iam.users.services import ListOrganizationUsersService

router = APIRouter()


@router.get(
    "/organizations/{organization_id}/users",
    response_model=OrganizationUserListResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Acceso denegado por tenant o RBAC."
        },
        422: {"description": "Error de validación de path o query params."},
        status.HTTP_501_NOT_IMPLEMENTED: {
            "description": "Autenticación provisional no integrada."
        },
    },
)
def list_organization_users(
    context: Annotated[TenantContext, Depends(get_tenant_context)],
    query: Annotated[UserListQuery, Depends(get_user_list_query)],
    service: Annotated[
        ListOrganizationUsersService,
        Depends(get_list_organization_users_service),
    ],
) -> OrganizationUserListResponse:
    """Lista usuarios visibles de una organización validada por TenantContext."""

    try:
        return service.list_users(context=context, query=query)
    except TenantContextError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para listar usuarios de la organización solicitada.",
        ) from error


__all__ = ("router",)
