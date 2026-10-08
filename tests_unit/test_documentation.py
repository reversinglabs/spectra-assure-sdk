"""The README and the reference pages say what the code does.

Each check compares a statement in the documentation with the code it
describes, so the two cannot drift apart unnoticed.
"""

from __future__ import annotations

import inspect
import logging
import re
from pathlib import Path
from typing import Any

import pytest
import requests

from spectra_assure_api_client import SpectraAssureApiOperations

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def returns_something_else(name: str) -> bool:
    annotation = inspect.signature(getattr(SpectraAssureApiOperations, name), eval_str=True).return_annotation
    return annotation is not requests.Response


# ------------------------------------------------------------------ return values (I-41)


def test_the_readme_names_exactly_the_calls_that_do_not_return_the_response() -> None:
    from spectra_assure_api_client.spectra_assure_api_operations import (
        DEPRECATED_INTERNAL_NAMES,
        DEPRECATED_RENAMED,
    )

    skip = set(DEPRECATED_INTERNAL_NAMES) | set(DEPRECATED_RENAMED) | {"close", "make_logger", "get_additional_args"}
    others = sorted(
        name
        for name, _ in inspect.getmembers(SpectraAssureApiOperations, inspect.isroutine)
        if not name.startswith("_")
        and name not in skip
        and not name.endswith("_report_types")
        and returns_something_else(name)
    )
    statement = README[README.index("### Exceptions") : README.index("Every exception the SDK raises")]

    assert others == ["download", "filestream_download", "filestream_rl_safe_download", "rl_safe_download"]
    assert all(f"`{name}`" in statement for name in others)
    assert "All operations return a `requests.Response`" not in README


def test_the_readme_does_not_claim_filestream_scan_returns_the_file_id() -> None:
    entry = README[README.index("[`filestream_scan`]") : README.index("[`filestream_url_import`]")]

    assert "Returns the new `file_id`." not in entry
    assert 'response.json()["id"]' in entry


# ------------------------------------------------------------------ operation tables (I-42)
#
# Each operation in the README has a table of where it works. The marks are
# derived here from the code and the specification, and the README must match
# them, so the tables cannot drift from the routes again.

TICK = "&#10003;"
PROJECT_LEVELS = ("Organization", "Group", "Project", "Package", "Version")

#: Calls with no route of their own. A string names the routed operation whose
#: marks they share; a dict gives their marks directly.
PSEUDO: dict[str, str | dict[str, set[str]]] = {
    # download accepts a package or a version, and forwards `build` to status.
    "download": {"Targets": {"Package", "Version"}, "Query parameters": {"Package", "Version"}, "Body fields": set()},
    "rl_safe_download": "rl_safe",
    # filestream_download takes named arguments only.
    "filestream_download": {"Targets": {"File Stream file"}, "Query parameters": set(), "Body fields": set()},
    "filestream_rl_safe_download": "filestream_rl_safe",
}

#: Public methods of the operation classes that are helpers, not operations.
NOT_OPERATIONS = {"filestream_report_types"}


def level_of(path: str) -> str:
    """The column an API path belongs in: what the call addresses."""
    if "/filestream" in path:
        return "File Stream file"
    if "/community/" in path:
        return "Community"
    if "pkg:rl/" in path:
        if "@{version}" in path:
            return "Version"
        return "Package" if "{package}" in path else "Project"
    return "Group" if "{group}" in path else "Organization"


def marks_for(method: str) -> dict[str, set[str]]:
    """Targets, Query parameters and Body fields: the levels each applies at."""
    from spectra_assure_api_client.spec import ROUTES, get_operation
    from spectra_assure_api_client.spec.routes import FILESTREAM_REPORT_OPERATIONS

    rows: dict[str, set[str]] = {"Targets": set(), "Query parameters": set(), "Body fields": set()}
    pseudo = PSEUDO.get(method)
    if isinstance(pseudo, dict):
        return {row: set(levels) for row, levels in pseudo.items()}
    action = pseudo or method
    if action == "filestream_report":  # one operation per report type, outside ROUTES
        operation_ids = list(FILESTREAM_REPORT_OPERATIONS.values())
    else:
        operation_ids = [operation_id for (routed, _), operation_id in ROUTES.items() if routed == action]
    for operation_id in operation_ids:
        operation = get_operation(operation_id)
        level = level_of(operation.path)
        rows["Targets"].add(level)
        if operation.query_params:
            rows["Query parameters"].add(level)
        if operation.body_properties or operation.form_properties:
            rows["Body fields"].add(level)
    return rows


def operations_by_class() -> dict[str, list[str]]:
    """Each operation class of the client and the public methods it defines itself."""
    from spectra_assure_api_client.spectra_assure_api_operations import DEPRECATED_RENAMED

    found: dict[str, list[str]] = {}
    for cls in SpectraAssureApiOperations.__mro__[1:]:
        if (
            not cls.__name__.startswith("SpectraAssureApiOperations")
            or cls.__name__ == "SpectraAssureApiOperationsBase"
        ):
            continue
        own = sorted(
            n for n in vars(cls) if not n.startswith("_") and callable(vars(cls)[n]) and n not in DEPRECATED_RENAMED
        )
        if own:
            found[cls.__name__] = own
    return found


def readme_sections() -> dict[str, tuple[str, list[str]]]:
    """method -> (heading line, table lines), for every operation entry in the README."""
    lines = README.splitlines()
    found: dict[str, tuple[str, list[str]]] = {}
    i = 0
    while i < len(lines):
        if re.match(r"\[`[a-z_]+`", lines[i]):
            heading = lines[i]
            j = i + 1
            table: list[str] = []
            while j < len(lines) and not re.match(r"\[`[a-z_]+`", lines[j]) and not lines[j].startswith("#"):
                if lines[j].startswith("|"):
                    table.append(lines[j])
                j += 1
            for method in re.findall(r"`([a-z_]+)`", heading.split("](")[0]):
                found[method] = (heading, table)
            i = j
        else:
            i += 1
    return found


def parse_table(table: list[str]) -> tuple[list[str], dict[str, set[str]]]:
    header = [c.strip() for c in table[0].strip().strip("|").split("|")][1:]
    rows = {}
    for line in table[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows[cells[0]] = {header[k] for k, cell in enumerate(cells[1:]) if TICK in cell}
    return header, rows


def public_operations() -> list[str]:
    return sorted(m for methods in operations_by_class().values() for m in methods if m not in NOT_OPERATIONS)


def test_every_operation_is_named_in_the_readme() -> None:
    """The README introduced twelve operations by class name only, so their method names appeared nowhere."""
    assert [m for m in public_operations() if m not in readme_sections()] == []


def test_every_operation_table_matches_the_routes() -> None:
    wrong: dict[str, object] = {}
    for method in public_operations():
        _heading, table = readme_sections()[method]
        if not table:
            wrong[method] = "no table"
            continue
        _header, rows = parse_table(table)
        if rows != marks_for(method):
            wrong[method] = {"README": rows, "routes": marks_for(method)}

    assert wrong == {}


def test_the_project_tables_use_one_column_layout() -> None:
    """Some tables dropped the Project column, so their marks sat under other headings."""
    layouts = set()
    for method in public_operations():
        _heading, table = readme_sections()[method]
        header, _rows = parse_table(table)
        if header not in (["File Stream file"], ["Community"]):
            layouts.add(tuple(header))

    assert layouts == {PROJECT_LEVELS}


# ------------------------------------------------------------------ reference pages (I-43)


def page_of(method: str) -> Path:
    heading, _table = readme_sections()[method]
    link = re.search(r"\]\((\./doc/[^)]+)\)", heading)
    assert link, heading
    return ROOT / link.group(1)


def primary_methods() -> list[str]:
    """For each reference page, the method its first argument list describes: the first in its heading."""
    seen: set[str] = set()
    methods = []
    for method in public_operations():
        heading, _table = readme_sections()[method]
        first = re.findall(r"`([a-z_]+)`", heading.split("](")[0])[0]
        if first not in seen:
            seen.add(first)
            methods.append(first)
    return sorted(methods)


def documented_arguments(page: Path) -> dict[str, str]:
    """name -> description, from the first `## Arguments` list of a page."""
    text = page.read_text(encoding="utf-8")
    block = re.search(r"## Arguments\s*\n(.*?)(?:\n## |\Z)", text, re.S)
    assert block, f"{page.name} has no Arguments section"
    return dict(re.findall(r"^\s*-\s*(\w+)\s*:\s*(.*)$", block.group(1), re.M))


def spec_declared(method: str) -> set[str]:
    """Names the specification declares for the call: carried in **qp, so not in the signature."""
    from spectra_assure_api_client.spec import ROUTES, get_operation

    return {
        name
        for (action, _), operation_id in ROUTES.items()
        if action == method
        for name in get_operation(operation_id).accepted_parameters
    }


def test_every_reference_page_documents_the_real_arguments() -> None:
    problems = []
    for method in primary_methods():
        page = page_of(method)
        documented = documented_arguments(page)
        signature = {
            name: parameter
            for name, parameter in inspect.signature(getattr(SpectraAssureApiOperations, method)).parameters.items()
            if name != "self" and parameter.kind is not inspect.Parameter.VAR_KEYWORD
        }
        for name, description in documented.items():
            if name == "qp":
                continue
            if name not in signature:
                if name not in spec_declared(method):
                    problems.append(f"{page.name}: documents `{name}`, which {method}() does not take")
                continue
            says_mandatory = "mandatory" in description.lower()
            is_mandatory = signature[name].default is inspect.Parameter.empty
            if says_mandatory != is_mandatory:
                problems.append(f"{page.name}: `{name}` documented as {'mandatory' if says_mandatory else 'optional'}")
        problems += [f"{page.name}: does not document `{name}`" for name in signature if name not in documented]

    assert problems == []


def test_every_reference_page_says_which_call_it_returns() -> None:
    """Both audit-log pages said they returned the result of community_user_account()."""
    wrong = []
    for method in primary_methods():
        page = page_of(method)
        named = re.findall(r"of the (\w+)\(\) API call", page.read_text(encoding="utf-8"))
        heading, _table = readme_sections()[method]
        own = set(re.findall(r"`([a-z_]+)`", heading.split("](")[0])) | {"listGroups"}
        wrong += [f"{page.name}: {name}()" for name in named if name not in own]

    assert wrong == []


def test_the_scan_page_names_the_real_exception() -> None:
    text = (ROOT / "doc" / "scan.md").read_text(encoding="utf-8")

    assert "`InvalidAction`" not in text
    assert "`SpectraAssureInvalidAction`" in text


# ------------------------------------------------------------------ wording and links (I-29)


def test_every_relative_link_in_the_readme_points_at_a_file() -> None:
    """The license link pointed at LICENSE.MD; the file is LICENSE."""
    targets = re.findall(r"\]\((\./[^)#]+)", README)
    missing = sorted({t for t in targets if not (ROOT / t).exists()})

    assert targets
    assert missing == []


def test_known_typos_are_gone() -> None:
    for typo in ("notend", "waite timout", "audir_log_status", "the provides file"):
        assert typo not in README, typo


def test_the_sessions_section_describes_the_present() -> None:
    """It read as a change note ("Before this change ... Now it does not")."""
    section = README[README.index("## Sessions") : README.index("## Support")]

    assert "Before this change" not in section
    assert "Now it does not" not in section
    assert "with SpectraAssureApiOperations(...) as client" in section


def test_each_operation_has_its_own_description() -> None:
    """The community report-package entry repeated the find-packages description."""
    descriptions: dict[str, str] = {}
    for method in public_operations():
        heading, _table = readme_sections()[method]
        entry = README[README.index(heading) :]
        match = re.search(r"\n\*\*(.+?)\*\*", entry)
        assert match, method
        descriptions.setdefault(match.group(1), heading)
    entries = {readme_sections()[m][0] for m in public_operations()}

    assert len(descriptions) == len(entries)


# ------------------------------------------------------------------ README corrections


def code_blocks(language: str) -> list[str]:
    """The README's fenced code blocks with this language tag; "" means every block, tagged or not."""
    tag = re.escape(language) if language else r"\w*"
    return re.findall(rf"```{tag}\n(.*?)```", README, re.S)


def test_the_readme_claims_no_default_host() -> None:
    """There is none: without host or server the client cannot be created."""
    assert "this the default if `host` is not specified" not in README
    assert "The default host and API version must not be modified" not in README
    assert "| `host` and `server` | `https://<host>/<server>/api/public/v1` |" in README


def test_the_readme_examples_do_not_turn_a_missing_variable_into_none() -> None:
    """str(os.getenv(...)) passes the text "None" on, which the SDK accepts as a name."""
    code = [line for block in code_blocks("") for line in block.splitlines() if not line.strip().startswith("#")]

    assert [line for line in code if "str(os.getenv(" in line] == []


def test_every_python_example_in_the_readme_compiles() -> None:
    blocks = code_blocks("python")

    assert len(blocks) >= 4
    for number, block in enumerate(blocks):
        compile(block, f"README python block {number}", "exec")


def test_the_logging_section_names_the_logger_and_uses_the_sdk_helper() -> None:
    section = README[README.index("## Logging") : README.index("## Usage")]

    assert 'logging.getLogger("spectra_assure_api_client")' in section
    assert "SpectraAssureApiOperations.make_logger(my_logger=" in section
    assert "def make_logger(" not in section  # its own copy stacked handlers on every call


def test_the_readme_logging_claim_holds_the_token_and_proxy_password_are_never_logged(
    tmp_path: Path, caplog: Any, monkeypatch: Any
) -> None:
    import json as json_module

    from .support import Recorder, install

    token, password = "TOKEN-SECRET-4711", "PROXY-PW-0815"
    config = tmp_path / "config.json"
    settings: dict[str, Any] = {"host": "h", "organization": "o", "group": "g", "token": token}
    settings |= {"proxy_server": "proxy.local", "proxy_port": 3128, "proxy_user": "u", "proxy_password": password}
    config.write_text(json_module.dumps({"SpectraAssureApi": settings}), encoding="utf-8")
    install(monkeypatch, "any", Recorder())

    with caplog.at_level(logging.DEBUG):
        client = SpectraAssureApiOperations(config_file=str(config))
        client.list_groups()
        client.status(project="p", package="k", version="1.0")

    assert caplog.text
    assert token not in caplog.text
    assert password not in caplog.text


def test_operation_descriptions_say_what_the_call_does() -> None:
    assert "List all groups, projects, packages, and versions" not in README  # groups come from list_groups
    assert "**Sync a version.**" not in README
    assert "**Rescan a version**" in README
    assert "The file name is arbitrary." not in README  # it must end in .json


# ------------------------------------------------------------------ README completeness


def heading_anchor(title: str) -> str:
    return re.sub(r"[^a-z0-9 -]", "", title.strip().lower()).replace(" ", "-")


def test_the_table_of_contents_lists_every_section_in_order() -> None:
    toc = README[README.index("## Table of contents") : README.index("## Requirements and dependencies")]
    listed = re.findall(r"^- \[[^\]]+\]\(#([^)]+)\)", toc, re.M)
    sections = [heading_anchor(t) for t in re.findall(r"^## (.+)$", README, re.M) if t != "Table of contents"]

    assert listed == sections


def test_every_fenced_code_block_says_its_language() -> None:
    """Fences come in pairs; every opening one must name the language, for highlighting."""
    fences = re.findall(r"^```(\w*)$", README, re.M)
    openings = fences[0::2]

    assert len(fences) % 2 == 0
    assert [tag for tag in openings if not tag] == []


def test_every_constructor_argument_is_documented_before_the_operations() -> None:
    usage = README[: README.index("## Operations")]
    arguments = [name for name in inspect.signature(SpectraAssureApiOperations.__init__).parameters if name != "self"]

    assert [name for name in arguments if f"**{name}**" not in usage and f"`{name}`" not in usage] == []


def test_the_rate_limiting_section_says_what_the_sdk_does() -> None:
    section = README[README.index("### Rate limiting") : README.index("### Configuration")]

    from spectra_assure_api_client.communication.constants import FALLBACK_THROTTLE_DELAY, MAX_THROTTLE_ATTEMPTS

    assert "`Retry-After`" in section
    assert f"{MAX_THROTTLE_ATTEMPTS} attempts" in section
    assert f"{FALLBACK_THROTTLE_DELAY} seconds" in section
    assert re.search(r"Download[- ]link requests are the exception", section)


def test_the_community_repositories_are_the_ones_the_api_accepts() -> None:
    yaml = pytest.importorskip("yaml")

    spec = yaml.safe_load((ROOT / "etc" / "spectra-assure-portal-public-api.yaml").read_text(encoding="utf-8"))
    accepted = set(spec["components"]["schemas"]["communities"]["enum"])  # the purl_community parameter's schema
    section = README[README.index("## Community repositories") : README.index("## Sessions")]

    assert set(re.findall(r"^- `([a-z]+)`$", section, re.M)) == accepted
    assert "Dec. 2025" not in section


CHANGES = (ROOT / "CHANGES.md").read_text(encoding="utf-8")


def test_the_changes_since_the_last_release_are_listed() -> None:
    """The release notes, in CHANGES.md, compare the version about to be published with the previous one."""
    assert "## Changes in 1.1.0" in CHANGES
    assert "Compared with 1.0.14, the previous published version." in CHANGES
    # 1.1.0 is not published yet, so nothing may describe changes "since" it.
    assert "## Changes since 1.1.0" not in CHANGES
    # the timeouts the notes give are the SDK's real defaults
    from spectra_assure_api_client.communication.constants import DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT

    notes = CHANGES[CHANGES.index("## Changes in 1.1.0") : CHANGES.index("## Deprecations")]
    assert f"a connect timeout of {DEFAULT_CONNECT_TIMEOUT} seconds" in notes
    assert f"a read timeout of {DEFAULT_READ_TIMEOUT} seconds by default" in notes
    # the README points to them, and keeps the version history
    assert "](./CHANGES.md)" in README
    assert "| v1.1.0  |" in README


def test_the_target_rule_is_a_table_not_prose_in_a_code_block() -> None:
    assert "The first value of 'None' decides" not in README
    assert "| given | given | given | the version |" in README
    assert "alllways" not in README


# ------------------------------------------------------------------ parameter tables on the reference pages


def table_names(section: str) -> set[str]:
    """The names in the first column of every table in a page section."""
    # Lower case only: the header cell is "Name", while `name` is a real field of edit.
    return set(re.findall(r"^\|\s*`?([a-z_]+)`?\s*\|", section, re.M))


def page_sections(text: str, heading: str) -> str:
    match = re.search(rf"^## {heading}\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def declared_for(method: str) -> tuple[set[str], set[str]]:
    """(query parameters, body fields) the specification declares for the call's routes."""
    from spectra_assure_api_client.spec import ROUTES, get_operation

    routed = PSEUDO.get(method)
    action = (
        routed
        if isinstance(routed, str)
        else {"download": "status", "filestream_download": "filestream_status"}.get(method, method)
    )
    query: set[str] = set()
    body: set[str] = set()
    for (name, _), operation_id in ROUTES.items():
        if name == action:
            operation = get_operation(operation_id)
            query |= set(operation.query_params)
            body |= set(operation.body_properties) | set(operation.form_properties)
    return query, body


def test_every_parameter_table_on_a_reference_page_matches_the_specification() -> None:
    """A query table listed body fields (create, edit), and one name was misspelt (offset_integer)."""
    wrong = []
    for method in primary_methods():
        page = page_of(method)
        text = page.read_text(encoding="utf-8")
        query, body = declared_for(method)
        for name in sorted(table_names(page_sections(text, "Query parameters")) - query):
            where = "a body field" if name in body else "not declared"
            wrong.append(f"{page.name}: query table lists `{name}`, {where}")
        wrong += [
            f"{page.name}: body table lists `{name}`, not a body field"
            for name in sorted(table_names(page_sections(text, "Body fields")) - body)
        ]

    assert wrong == []


# ------------------------------------------------------------------ links that must lead somewhere


def headings_of(path: Path) -> set[str]:
    return {heading_anchor(title) for title in re.findall(r"^#{1,4} (.+)$", path.read_text(encoding="utf-8"), re.M)}


@pytest.mark.parametrize("name", ["README.md", "CHANGES.md"])
def test_every_section_link_reaches_a_heading(name: str) -> None:
    """A link to #section, or to file.md#section, must name a heading that exists in that file.

    Moving the release notes to CHANGES.md left links to sections that were no
    longer in the file they pointed at.
    """
    source = ROOT / name
    broken = []
    for target in re.findall(r"\]\(([^)\s]+)\)", source.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:")) or "#" not in target:
            continue
        file_part, _, section = target.partition("#")
        destination = (source.parent / file_part) if file_part else source
        if not destination.is_file() or section not in headings_of(destination):
            broken.append(target)

    assert broken == []


def test_every_api_reference_link_on_a_reference_page_names_an_operation_of_the_api() -> None:
    """Links to docs.secure.software/api-reference/...#.../operation/<id> must name an operationId in the YAML."""
    yaml = pytest.importorskip("yaml")
    operations: set[str] = set()
    for spec_file in sorted((ROOT / "etc").glob("spectra-assure-*.yaml")):
        spec = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
        operations |= {
            str(op["operationId"])
            for item in spec["paths"].values()
            for op in item.values()
            if isinstance(op, dict) and "operationId" in op
        }

    unknown = sorted(
        f"{page.name}: {operation}"
        for page in sorted((ROOT / "doc").glob("*.md"))
        for operation in re.findall(
            r"api-reference/#[^)\s]*/operation/([A-Za-z0-9_]+)", page.read_text(encoding="utf-8")
        )
        if operation not in operations
    )

    assert unknown == []
