"""Configuration: constructor arguments, the JSON config file, and how the two merge."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import pytest

from spectra_assure_api_client import SpectraAssureApiOperations, SpectraAssureInvalidAction

from .support import GROUP, HOST, ORGANIZATION, TOKEN, Recorder, install, make_client

SECTION = "SpectraAssureApi"


def write_config(directory: Path, settings: dict[str, Any], *, name: str = "config.json") -> str:
    """Write a config file with `settings` under the `SpectraAssureApi` key."""
    path = directory / name
    path.write_text(json.dumps({SECTION: settings}), encoding="utf-8")
    return str(path)


def mandatory() -> dict[str, Any]:
    return {"host": HOST, "organization": ORGANIZATION, "group": GROUP, "token": TOKEN}


def test_config_file_must_end_in_json(tmp_path: Path) -> None:
    """README, 'Changes in 1.1.0': any other extension raises."""
    path = write_config(tmp_path, mandatory(), name="config.txt")

    with pytest.raises(SpectraAssureInvalidAction, match=r"must end in '\.json'"):
        SpectraAssureApiOperations(config_file=path)


def test_json_extension_check_is_case_insensitive(tmp_path: Path) -> None:
    path = write_config(tmp_path, mandatory(), name="CONFIG.JSON")

    client = SpectraAssureApiOperations(config_file=path)

    assert client.organization == ORGANIZATION


def test_config_file_without_the_section_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"Other": {}}), encoding="utf-8")

    with pytest.raises(SpectraAssureInvalidAction, match=SECTION):
        SpectraAssureApiOperations(config_file=str(path))


def test_timeouts_default_when_nothing_is_given() -> None:
    client = SpectraAssureApiOperations(host=HOST, organization=ORGANIZATION, group=GROUP, token=TOKEN)

    assert client.read_timeout == 3600
    assert client.connect_timeout == 10


def test_timeouts_from_the_config_file_are_applied(tmp_path: Path) -> None:
    """The README's own example file sets `timeout`; it must not be ignored."""
    settings = {**mandatory(), "timeout": 60, "connect_timeout": 3, "read_timeout": 7}

    client = SpectraAssureApiOperations(config_file=write_config(tmp_path, settings))

    assert client.connect_timeout == 3
    # `timeout` is an alias of `read_timeout`; given both, `read_timeout` wins.
    assert client.read_timeout == 7
    assert client.timeout == 7


def test_constructor_timeouts_override_the_config_file(tmp_path: Path) -> None:
    settings = {**mandatory(), "connect_timeout": 3, "read_timeout": 7}

    client = SpectraAssureApiOperations(
        config_file=write_config(tmp_path, settings),
        connect_timeout=4,
        read_timeout=8,
    )

    assert client.connect_timeout == 4
    assert client.read_timeout == 8


def test_timeouts_missing_from_a_config_file_take_the_defaults(tmp_path: Path) -> None:
    client = SpectraAssureApiOperations(config_file=write_config(tmp_path, mandatory()))

    assert client.read_timeout == 3600
    assert client.connect_timeout == 10


def sent_timeout(monkeypatch: pytest.MonkeyPatch, client: SpectraAssureApiOperations) -> Any:
    """The `timeout` value that actually reaches `requests` for one call."""
    recorder = install(monkeypatch, "get", Recorder())
    client.list(project="pr")
    return recorder.calls[0]["timeout"]


def test_timeout_is_an_alias_of_read_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """README and the example use `timeout=60`; it must reach the request."""
    client = make_client(timeout=60)

    assert client.read_timeout == 60
    assert client.timeout == 60
    assert sent_timeout(monkeypatch, client) == (10, 60)


def test_read_timeout_reaches_the_request(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(read_timeout=45, connect_timeout=5)

    assert sent_timeout(monkeypatch, client) == (5, 45)


def test_read_timeout_wins_over_its_alias_in_the_same_source() -> None:
    client = make_client(timeout=60, read_timeout=45)

    assert client.read_timeout == 45
    assert client.timeout == 45


def test_config_file_timeout_alone_sets_the_read_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = SpectraAssureApiOperations(config_file=write_config(tmp_path, {**mandatory(), "timeout": 60}))

    assert sent_timeout(monkeypatch, client) == (10, 60)


def test_constructor_timeout_overrides_a_config_file_read_timeout(tmp_path: Path) -> None:
    """Arguments beat the file whichever of the two names either one uses."""
    path = write_config(tmp_path, {**mandatory(), "read_timeout": 7})

    client = SpectraAssureApiOperations(config_file=path, timeout=60)

    assert client.read_timeout == 60


def test_no_timeout_argument_leaves_the_default_of_an_hour(monkeypatch: pytest.MonkeyPatch) -> None:
    assert sent_timeout(monkeypatch, make_client()) == (10, 3600)


def test_unknown_keyword_warns_and_suggests_the_real_name() -> None:
    """README used `no_verify_ssl` and `configFile`; both were silently ignored."""
    with pytest.warns(UserWarning, match=r"unknown setting 'no_verify_ssl'.*did you mean 'no_ssl_verify'") as caught:
        client = SpectraAssureApiOperations(
            host=HOST,
            organization=ORGANIZATION,
            group=GROUP,
            token=TOKEN,
            no_verify_ssl=True,
        )

    assert len(caught) == 1
    assert caught[0].filename == __file__  # points at the caller, not at SDK internals
    assert client.no_ssl_verify is None  # the misspelt setting really was not applied


def test_misspelt_config_file_keyword_warns() -> None:
    with (
        pytest.warns(UserWarning, match=r"'configFile'.*did you mean 'config_file'"),
        pytest.raises(SpectraAssureInvalidAction),  # no file was read, so nothing is configured
    ):
        SpectraAssureApiOperations(configFile="whatever.json", token=TOKEN)


def test_unknown_keyword_without_a_close_match_gets_no_suggestion() -> None:
    with pytest.warns(UserWarning, match=r"unknown setting 'flavour' in the arguments is ignored$"):
        SpectraAssureApiOperations(host=HOST, organization=ORGANIZATION, group=GROUP, token=TOKEN, flavour="x")


def test_additional_args_passes_through_without_a_warning(recwarn: pytest.WarningsRecorder) -> None:
    client = SpectraAssureApiOperations(
        host=HOST,
        organization=ORGANIZATION,
        group=GROUP,
        token=TOKEN,
        additional_args={"anything": 1},
    )

    assert client.get_additional_args() == {"anything": 1}
    assert not [w for w in recwarn if issubclass(w.category, UserWarning)]


def test_known_settings_do_not_warn(recwarn: pytest.WarningsRecorder) -> None:
    make_client(timeout=30, no_ssl_verify=True, auto_adapt_to_throttle=True)

    assert not [w for w in recwarn if issubclass(w.category, UserWarning)]


def test_unknown_key_in_the_config_file_section_warns(tmp_path: Path) -> None:
    """The sample configs shipped `autoAdaptToThrottle`, which was ignored."""
    path = write_config(tmp_path, {**mandatory(), "autoAdaptToThrottle": True})

    with pytest.warns(UserWarning, match=r"'autoAdaptToThrottle'.*did you mean 'auto_adapt_to_throttle'") as caught:
        client = SpectraAssureApiOperations(config_file=path)

    assert caught[0].filename == __file__
    assert client.auto_adapt_to_throttle is False  # ignored, as the warning says


def test_keys_outside_the_config_section_are_not_reported(tmp_path: Path, recwarn: pytest.WarningsRecorder) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({SECTION: mandatory(), "somethingElse": True}), encoding="utf-8")

    SpectraAssureApiOperations(config_file=str(path))

    assert not [w for w in recwarn if issubclass(w.category, UserWarning)]


# ------------------------------------------------------------------ api_version, api_domain, api_proto (I-35)


def api_settings(**override: object) -> dict[str, object]:
    return {"api_version": "v1", "api_domain": "secure.software", "api_proto": "https", **override}


@pytest.mark.parametrize("name", ["api_version", "api_domain", "api_proto"])
@pytest.mark.parametrize("value", [None, ""])
def test_an_unset_api_setting_is_refused(name: str, value: object) -> None:
    """None used to pass: str(None) is "None", so the base URL ended in /api/public/None."""
    with pytest.raises(SpectraAssureInvalidAction, match=f"Fatal: the {name} is not set"):
        SpectraAssureApiOperations(
            host=HOST,
            organization=ORGANIZATION,
            group=GROUP,
            token=TOKEN,
            **api_settings(**{name: value}),  # type: ignore[arg-type]
        )


def test_the_api_settings_build_the_base_url() -> None:
    client = SpectraAssureApiOperations(host=HOST, organization=ORGANIZATION, group=GROUP, token=TOKEN)

    assert client.base_url == f"https://{HOST}/api/public/v1"


def test_a_non_string_api_version_is_still_accepted_as_before() -> None:
    """Only None and the empty string are refused; other values behave as they always did."""
    client = SpectraAssureApiOperations(
        host=HOST,
        organization=ORGANIZATION,
        group=GROUP,
        token=TOKEN,
        api_version=2,  # type: ignore[arg-type]
    )

    assert client.base_url.endswith("/api/public/2")


# ------------------------------------------------------------------ config-file errors (I-20)


def expect_config_error(path: Path, match: str) -> SpectraAssureInvalidAction:
    with pytest.raises(SpectraAssureInvalidAction, match=match) as caught:
        SpectraAssureApiOperations(config_file=str(path))
    return caught.value


def test_a_missing_config_file_is_an_sdk_error(tmp_path: Path) -> None:
    """It used to escape as FileNotFoundError; the original stays available as the cause."""
    error = expect_config_error(tmp_path / "absent.json", r"absent\.json cannot be read")

    assert isinstance(error.__cause__, FileNotFoundError)


def test_a_directory_named_like_a_config_file_is_an_sdk_error(tmp_path: Path) -> None:
    directory = tmp_path / "config.json"
    directory.mkdir()

    error = expect_config_error(directory, "cannot be read")

    assert isinstance(error.__cause__, IsADirectoryError)


def test_invalid_json_is_an_sdk_error_that_says_where(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"SpectraAssureApi": {"host": "h",}}', encoding="utf-8")

    error = expect_config_error(path, r"is not valid JSON: .*\(line 1, column \d+\)")

    assert isinstance(error.__cause__, json.JSONDecodeError)


def test_a_file_that_is_not_utf8_is_an_sdk_error(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_bytes(b'{"SpectraAssureApi": {"host": "h\xff"}}')

    error = expect_config_error(path, "is not UTF-8 text")

    assert isinstance(error.__cause__, UnicodeDecodeError)


@pytest.mark.parametrize(
    ("content", "kind"),
    [("[]", "an array"), ('"text"', "a string"), ("42", "a number"), ("null", "null"), ("true", "a boolean")],
)
def test_a_config_file_that_is_not_a_json_object_is_an_sdk_error(tmp_path: Path, content: str, kind: str) -> None:
    """A list used to fail inside the SDK with AttributeError: 'list' object has no attribute 'get'."""
    path = tmp_path / "config.json"
    path.write_text(content, encoding="utf-8")

    expect_config_error(path, f"must contain a JSON object, not {kind}")


@pytest.mark.parametrize(("section", "kind"), [("5", "a number"), ('"host=h"', "a string"), ("[1]", "an array")])
def test_a_section_that_is_not_a_json_object_is_an_sdk_error(tmp_path: Path, section: str, kind: str) -> None:
    path = tmp_path / "config.json"
    path.write_text(f'{{"{SECTION}": {section}}}', encoding="utf-8")

    expect_config_error(path, f"'{SECTION}' section .* must be a JSON object, not {kind}")


# ------------------------------------------------------------------ one exception root (I-20)


def test_every_exported_exception_derives_from_spectra_assure_exceptions() -> None:
    import spectra_assure_api_client as sdk

    exported = [getattr(sdk, name) for name in sdk.__all__]
    exceptions = [e for e in exported if isinstance(e, type) and issubclass(e, BaseException)]

    assert len(exceptions) == 14  # 8 SpectraAssure* (with SpectraAssureSpecError) and 6 UrlDownloader*
    assert all(issubclass(e, sdk.SpectraAssureExceptions) for e in exceptions)


def test_one_except_catches_a_downloader_error(tmp_path: Path) -> None:
    from spectra_assure_api_client import SpectraAssureExceptions, UrlDownloader, UrlDownloaderTargetDirectoryIssue

    with pytest.raises(SpectraAssureExceptions) as caught:
        UrlDownloader(target_dir=str(tmp_path / "absent"))

    assert isinstance(caught.value, UrlDownloaderTargetDirectoryIssue)


def test_the_spec_error_is_exported() -> None:
    from spectra_assure_api_client import SpectraAssureExceptions, SpectraAssureSpecError

    assert issubclass(SpectraAssureSpecError, SpectraAssureExceptions)


def test_the_readme_lists_every_exported_exception() -> None:
    import spectra_assure_api_client as sdk

    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    section = readme[readme.index("### Exceptions") : readme.index("## Examples")]
    names = [n for n in sdk.__all__ if isinstance(getattr(sdk, n), type) and issubclass(getattr(sdk, n), BaseException)]

    assert [n for n in names if f"`{n}`" not in section] == []


# ------------------------------------------------------------------ the message for missing settings


SETTINGS: dict[str, Any] = {
    "host": "portal.example.com",
    "organization": "Org",
    "group": "Grp",
    "token": "TOKEN-SECRET-4711",
}
NAMES = {"host": "host or server", "organization": "organization", "group": "group", "token": "token"}


def without(*left_out: str) -> dict[str, Any]:
    return {name: value for name, value in SETTINGS.items() if name not in left_out}


@pytest.mark.parametrize(
    "left_out",
    [combination for size in range(1, 5) for combination in itertools.combinations(SETTINGS, size)],
    ids=lambda combination: "+".join(combination),
)
def test_the_message_names_exactly_the_missing_settings(left_out: tuple[str, ...]) -> None:
    """It used to list all four, missing or not: "TOKEN is None, mandatory: True; cannot be True"."""
    expected = ", ".join(NAMES[name] for name in SETTINGS if name in left_out)

    with pytest.raises(SpectraAssureInvalidAction) as caught:
        SpectraAssureApiOperations(**without(*left_out))

    message = str(caught.value)
    assert message == (
        f"minimal required settings are missing or empty: {expected}; "
        "give them as named arguments or in the configuration file"
    )
    assert SETTINGS["token"] not in message


def test_an_empty_setting_counts_as_missing() -> None:
    with pytest.raises(SpectraAssureInvalidAction, match=r"missing or empty: group;"):
        SpectraAssureApiOperations(**{**SETTINGS, "group": ""})


def test_the_message_is_the_same_for_settings_from_a_configuration_file(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({SECTION: without("organization", "token")}), encoding="utf-8")

    with pytest.raises(SpectraAssureInvalidAction, match=r"missing or empty: organization, token;"):
        SpectraAssureApiOperations(config_file=str(config))
