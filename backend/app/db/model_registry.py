"""Registro central de modelos SQLAlchemy para metadata y Alembic."""

import app.domains.auth.shared.models as auth_models
import app.domains.iam.access.models as access_models
import app.domains.iam.departments.models as department_models
import app.domains.iam.geography.models as geography_models
import app.domains.iam.organizations.models as organization_models
import app.domains.iam.users.models as user_models

__all__ = [
    "access_models",
    "auth_models",
    "department_models",
    "geography_models",
    "organization_models",
    "user_models",
]
