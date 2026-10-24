"""Tests for the core module."""

from essl_f22 import __version__, add


def test_add_positive() -> None:
    assert add(2, 3) == 5


def test_add_with_zero() -> None:
    assert add(0, 0) == 0


def test_version_is_semver_string() -> None:
    assert __version__ == "0.1.0"
