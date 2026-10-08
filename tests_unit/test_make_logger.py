"""`make_logger`: what it sets up, and that calling it again does not stack handlers (I-28)."""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations


@pytest.fixture
def subject(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[logging.Logger]:
    """A fresh logger, run as a program called `myscript.py` from an empty directory."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(tmp_path / "myscript.py")])
    for name in ("LOG_LEVEL", "ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)
    log = logging.getLogger(f"test-make-logger-{tmp_path.name}")
    yield log
    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()


def file_handler(log: logging.Logger) -> logging.FileHandler:
    return next(h for h in log.handlers if isinstance(h, logging.FileHandler))


def console_handler(log: logging.Logger) -> logging.Handler:
    return next(h for h in log.handlers if not isinstance(h, logging.FileHandler))


def test_it_adds_a_console_and_a_file_handler(subject: logging.Logger, tmp_path: Path) -> None:
    SpectraAssureApiOperations.make_logger(my_logger=subject)

    kinds = sorted(type(h).__name__ for h in subject.handlers)
    assert kinds == ["FileHandler", "StreamHandler"]
    assert subject.level == logging.DEBUG
    assert (tmp_path / "myscript.log").exists()


def test_calling_it_again_does_not_stack_handlers(subject: logging.Logger) -> None:
    """Every call used to add two more handlers, so each line was logged once more."""
    for _ in range(3):
        SpectraAssureApiOperations.make_logger(my_logger=subject)

    assert len(subject.handlers) == 2


def test_each_line_is_written_once_after_repeated_calls(subject: logging.Logger, tmp_path: Path) -> None:
    for _ in range(3):
        SpectraAssureApiOperations.make_logger(my_logger=subject)

    subject.info("hello once")
    for handler in subject.handlers:
        handler.flush()

    assert (tmp_path / "myscript.log").read_text().count("hello once") == 1


def test_a_replaced_log_file_is_closed(subject: logging.Logger) -> None:
    SpectraAssureApiOperations.make_logger(my_logger=subject)
    first = file_handler(subject)

    SpectraAssureApiOperations.make_logger(my_logger=subject)

    assert first not in subject.handlers
    assert first.stream is None  # FileHandler.close() drops its stream


def test_handlers_the_caller_added_are_left_alone(subject: logging.Logger) -> None:
    own = logging.NullHandler()
    subject.addHandler(own)

    SpectraAssureApiOperations.make_logger(my_logger=subject)
    SpectraAssureApiOperations.make_logger(my_logger=subject)

    assert own in subject.handlers
    assert len(subject.handlers) == 3


def test_the_console_level_comes_from_log_level(monkeypatch: pytest.MonkeyPatch, subject: logging.Logger) -> None:
    monkeypatch.setenv("LOG_LEVEL", "ERROR")

    SpectraAssureApiOperations.make_logger(my_logger=subject)

    assert console_handler(subject).level == logging.ERROR


@pytest.mark.parametrize(("environment", "level"), [("PRODUCTION", logging.INFO), ("development", logging.DEBUG)])
def test_the_file_level_depends_on_the_environment(
    monkeypatch: pytest.MonkeyPatch, subject: logging.Logger, environment: str, level: int
) -> None:
    monkeypatch.setenv("ENVIRONMENT", environment)

    SpectraAssureApiOperations.make_logger(my_logger=subject)

    assert file_handler(subject).level == level
