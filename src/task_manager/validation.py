"""Validation helpers for task fields."""


def validate_title(title: str) -> None:
    """Raise ValueError if the title is not a usable string."""
    if not isinstance(title, str):
        raise ValueError("Title must be a string")
    if not title.strip():
        raise ValueError("Title must not be empty or whitespace-only")


def validate_priority(priority: int) -> None:
    """Raise ValueError if the priority is not a usable integer."""
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise ValueError("Priority must be an integer")
