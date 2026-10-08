"""Excepciones controladas para consulta de identidad autenticada."""


class NotAuthenticatedError(Exception):
    """La identidad no ha podido verificarse de forma segura."""
