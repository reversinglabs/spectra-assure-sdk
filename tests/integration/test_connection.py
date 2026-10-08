"""The three ways of giving the client its settings; each must reach the Portal (was t1, t2, t3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import expect

from spectra_assure_api_client import SpectraAssureApiOperations


def group_names(client: SpectraAssureApiOperations) -> list[str]:
    response = expect(client.list_groups(), 200)
    return [group["name"] for group in response.json()["groups"]]


def test_settings_as_arguments(client: SpectraAssureApiOperations, settings: dict[str, Any]) -> None:
    """The settings as named arguments; usage for the organization and for the group (t1)."""
    expect(client.usage())
    expect(client.usage(group=settings["group"]))


def test_settings_from_a_configuration_file(config_file: Path, settings: dict[str, Any], no_ssl_verify: bool) -> None:
    """Everything but the token from the configuration file (t2)."""
    with SpectraAssureApiOperations(
        config_file=str(config_file), token=settings["token"], no_ssl_verify=no_ssl_verify
    ) as client:
        assert settings["group"] in group_names(client)


def test_a_configuration_file_together_with_arguments(
    config_file: Path, settings: dict[str, Any], no_ssl_verify: bool
) -> None:
    """The arguments and the file together; the arguments win (t3)."""
    with SpectraAssureApiOperations(config_file=str(config_file), no_ssl_verify=no_ssl_verify, **settings) as client:
        assert settings["group"] in group_names(client)
