"""Unit tests for the specification-driven rebuild.

Deliberately NOT in `tests/`: that directory holds the repository's integration
tests, which are type-checked by running `mypy *.py integration` from inside it.
Adding an `__init__.py` there makes every module resolve under two names at once
(`sweep` and `tests.sweep`) and mypy rejects it.

This directory is a package so the test modules can share `support.py`.
"""
