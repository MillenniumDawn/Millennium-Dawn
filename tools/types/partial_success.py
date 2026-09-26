from typing import Generic, TypeVar

T = TypeVar('T')

class PartialSuccess(Generic[T]):
    """Represents the outcome of an operation that can succeed despite some issues.

    Attributes:
        value (T): The value of a successful outcome.
        warning (str): The warning message, if any.
        is_success (bool): Indicates whether the outcome is a success.
    """

    def __init__(self, value: T, warning: str | list[str] = ""):
        self.value = value
        self.warning = warning if isinstance(warning, str) else ";\n".join(f"    {item}" for item in warning)

    def has_warning(self) -> bool:
        """Indicates whether there is a warning message."""
        return bool(self.warning)