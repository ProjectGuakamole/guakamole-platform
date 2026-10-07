import re
from datetime import date
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_password_policy(password: str) -> str:
    if password.strip() == "":
        raise ValueError("La contraseña no puede estar vacía.")
    checks = (
        len(password) >= 12,
        any(character.islower() for character in password),
        any(character.isupper() for character in password),
        any(character.isdigit() for character in password),
        any(
            not character.isalnum() and not character.isspace()
            for character in password
        ),
    )
    if not all(checks):
        raise ValueError("La contraseña no cumple la política mínima.")
    return password


class OrganizationRegistrationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=120)
    legal_name: str = Field(min_length=1, max_length=200)
    tax_id: str = Field(min_length=1, max_length=32)
    country: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=20)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        normalized = value.lower()
        if SLUG_PATTERN.fullmatch(normalized) is None:
            raise ValueError("El slug no tiene un formato válido.")
        return normalized


class UserRegistrationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=254)
    birth_date: date
    password: str = Field(min_length=1, max_length=256)
    password_confirm: str = Field(min_length=1, max_length=256)
    country: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=255)
    postal_code: str = Field(min_length=1, max_length=20)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.lower()
        if EMAIL_PATTERN.fullmatch(normalized) is None:
            raise ValueError("El email no tiene un formato válido.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_policy(value)

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        return value

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> Self:
        if self.password != self.password_confirm:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization: OrganizationRegistrationInput
    user: UserRegistrationInput


class RegistrationResponse(BaseModel):
    organization_id: str
    user_id: str
    organization_status: str
    user_status: str
