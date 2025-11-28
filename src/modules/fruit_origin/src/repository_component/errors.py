"""Repository errors for fruit_origin module."""


class RepositoryError(Exception):
    """Base repository error."""

    pass


class DuplicateCodeError(RepositoryError):
    """Duplicate code constraint violation."""

    pass


class NotFoundError(RepositoryError):
    """Entity not found."""

    pass
