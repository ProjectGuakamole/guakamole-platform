"""Excepciones controladas para protección CSRF."""


class InvalidCsrfTokenError(Exception):
    """El token CSRF no es válido para el access token actual."""
