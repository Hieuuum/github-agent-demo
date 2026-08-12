import pytest

from task_manager.validation import validate_priority, validate_title


def test_validate_title_accepts_normal_title():
    validate_title("Buy milk")


def test_validate_title_rejects_empty_string():
    with pytest.raises(ValueError):
        validate_title("")


def test_validate_title_rejects_non_string():
    with pytest.raises(ValueError):
        validate_title(123)


def test_validate_title_rejects_whitespace_only():
    with pytest.raises(ValueError):
        validate_title("   ")


def test_validate_priority_accepts_zero_and_positive():
    validate_priority(0)
    validate_priority(5)


def test_validate_priority_rejects_non_integer():
    with pytest.raises(ValueError):
        validate_priority("high")
