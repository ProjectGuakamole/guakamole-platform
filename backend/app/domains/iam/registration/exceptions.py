class RegistrationError(Exception):
    """Error base controlado durante el registro público."""


class DuplicateRegistrationError(RegistrationError):
    """El registro entra en conflicto con datos ya existentes."""


class InvalidRegistrationReferenceError(RegistrationError):
    """Algún catálogo requerido para registrar no existe."""
