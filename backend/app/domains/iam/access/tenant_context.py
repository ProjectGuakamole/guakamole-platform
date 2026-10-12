"""Contexto interno mínimo de tenant para IAM.

Este módulo no depende de FastAPI, SQLAlchemy ni modelos ORM. Su responsabilidad
es representar y validar el contexto de organización efectivo antes de que las
policies o casos de uso ejecuten reglas más específicas.
"""

from dataclasses import dataclass

ACTIVE_STATUS = "ACTIVE"
PLATFORM_ADMIN_ROLE = "PLATFORM_ADMIN"


class TenantContextError(Exception):
    """Error base controlado al construir o validar un TenantContext."""


class TenantAccessDeniedError(TenantContextError):
    """El actor no puede operar sobre la organización solicitada."""


class InactiveUserError(TenantContextError):
    """El usuario autenticado no está activo."""


class InactiveOrganizationError(TenantContextError):
    """La organización solicitada no está activa."""


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Contexto mínimo de tenant compatible con el IAM simplificado actual."""

    actor_user_id: int
    requested_organization_id: int
    effective_organization_id: int
    platform_role: str
    organization_role: str
    user_status: str
    organization_status: str
    is_platform_admin: bool

    @property
    def is_same_organization(self) -> bool:
        """Indica si la organización solicitada coincide con la efectiva."""
        return self.requested_organization_id == self.effective_organization_id

    @property
    def is_active_user(self) -> bool:
        """Indica si el estado del usuario permite operaciones ordinarias."""
        return self.user_status == ACTIVE_STATUS

    @property
    def is_active_organization(self) -> bool:
        """Indica si la organización solicitada permite operaciones ordinarias."""
        return self.organization_status == ACTIVE_STATUS


def build_tenant_context(
    *,
    actor_user_id: int,
    requested_organization_id: int,
    effective_organization_id: int,
    platform_role: str,
    organization_role: str,
    user_status: str = ACTIVE_STATUS,
    organization_status: str = ACTIVE_STATUS,
    is_platform_admin: bool | None = None,
) -> TenantContext:
    """Construye un TenantContext validando reglas mínimas de tenant.

    La implementación actual de IAM todavía modela organización y roles de forma
    directa en ``User``. Por eso este builder trabaja con valores ya resueltos por
    capas superiores, sin consultar base de datos ni asumir memberships/grupos.
    """
    platform_role_is_admin = platform_role == PLATFORM_ADMIN_ROLE
    if is_platform_admin is True and not platform_role_is_admin:
        raise TenantAccessDeniedError(
            "El actor no puede declararse platform admin sin rol de plataforma."
        )
    resolved_is_platform_admin = (
        platform_role_is_admin if is_platform_admin is None else is_platform_admin
    )
    context = TenantContext(
        actor_user_id=actor_user_id,
        requested_organization_id=requested_organization_id,
        effective_organization_id=effective_organization_id,
        platform_role=platform_role,
        organization_role=organization_role,
        user_status=user_status,
        organization_status=organization_status,
        is_platform_admin=resolved_is_platform_admin,
    )
    validate_tenant_context(context)
    return context


def validate_tenant_context(context: TenantContext) -> None:
    """Valida las reglas mínimas de activación y cruce de tenant."""
    if not context.is_active_user:
        raise InactiveUserError("El usuario no está activo.")
    if not context.is_active_organization:
        raise InactiveOrganizationError("La organización no está activa.")
    if not context.is_platform_admin and not context.is_same_organization:
        raise TenantAccessDeniedError(
            "El actor no puede operar sobre la organización solicitada."
        )


__all__ = [
    "ACTIVE_STATUS",
    "PLATFORM_ADMIN_ROLE",
    "InactiveOrganizationError",
    "InactiveUserError",
    "TenantAccessDeniedError",
    "TenantContext",
    "TenantContextError",
    "build_tenant_context",
    "validate_tenant_context",
]
