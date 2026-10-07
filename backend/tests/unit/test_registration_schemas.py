from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.domain.iam.organizations.registration_schemas import (
    OrganizationRegistrationInput,
    UserRegistrationInput,
    validate_password_policy,
)

pytestmark = pytest.mark.test_unit


def test_password_policy_accepts_strong_password() -> None:
    assert validate_password_policy("PasswordSeguro123!") == "PasswordSeguro123!"


@pytest.mark.parametrize(
    "password",
    [
        "short1!A",
        "passwordseguro123!",
        "PASSWORDSEGURO123!",
        "PasswordSeguro!",
        "PasswordSeguro123",
        "            ",
    ],
)
def test_password_policy_rejects_weak_passwords(password: str) -> None:
    with pytest.raises(ValueError, match="contraseña"):
        validate_password_policy(password)


def test_password_confirmation_mismatch_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UserRegistrationInput(
            first_name="Ana",
            last_name="García",
            email="ana@empresa.com",
            birth_date=date(1990, 1, 1),
            **{
                "password": "PasswordSeguro123!",
                "password_confirm": "PasswordSeguro123?",
            },
            country="España",
            state="Catalunya",
            city="Barcelona",
            address="Calle Mayor 10",
            postal_code="08001",
        )


def test_future_birth_date_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UserRegistrationInput(
            first_name="Ana",
            last_name="García",
            email="ana@empresa.com",
            birth_date=date.today() + timedelta(days=1),
            **{
                "password": "PasswordSeguro123!",
                "password_confirm": "PasswordSeguro123!",
            },
            country="España",
            state="Catalunya",
            city="Barcelona",
            address="Calle Mayor 10",
            postal_code="08001",
        )


def test_slug_is_normalized_and_validated() -> None:
    organization = OrganizationRegistrationInput(
        name="Mi Empresa",
        slug="MI-EMPRESA",
        legal_name="Mi Empresa S.L.",
        tax_id="B12345678",
        country="España",
        state="Catalunya",
        city="Barcelona",
        address="Calle Mayor 10",
        postal_code="08001",
    )

    assert organization.slug == "mi-empresa"

    with pytest.raises(ValidationError):
        OrganizationRegistrationInput(
            name="Mi Empresa",
            slug="mi empresa",
            legal_name="Mi Empresa S.L.",
            tax_id="B12345678",
            country="España",
            state="Catalunya",
            city="Barcelona",
            address="Calle Mayor 10",
            postal_code="08001",
        )
