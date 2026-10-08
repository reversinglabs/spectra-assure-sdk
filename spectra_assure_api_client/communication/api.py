import difflib
import json
import logging
import os
import re
import sys
import urllib
import warnings
from pathlib import Path
from typing import (
    Any,
)

from .constants import (
    DEFAULT_AUTO_ADAPT_TO_THROTTLE,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    DEFAULT_TIMEOUT,
)
from .delete import SpectraAssureApiDelete
from .exceptions import (
    SpectraAssureInvalidAction,
)
from .get import SpectraAssureApiGet
from .patch import SpectraAssureApiPatch
from .post import SpectraAssureApiPost
from .put import SpectraAssureApiPut

logger = logging.getLogger(__name__)

# Marks the handlers make_logger() installs, so a repeated call replaces them.
_MADE_BY_MAKE_LOGGER = "_spectra_assure_made_by_make_logger"


def _json_kind(value: Any) -> str:
    """Name a parsed JSON value the way JSON does: an array, a string, a number."""
    if isinstance(value, list):
        return "an array"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, bool):
        return "a boolean"
    if isinstance(value, (int, float)):
        return "a number"
    if value is None:
        return "null"
    return type(value).__name__


def _warn_unknown_settings(
    *,
    where: str,
    unknown: list[str],
    known: list[str],
    stacklevel: int,
) -> None:
    """Warn about settings the client does not recognise, suggesting the likely intended name.

    An unrecognised setting is not an error, because `additional_args` is a
    deliberate pass-through, but a silently ignored one hides real mistakes: a
    misspelled `no_ssl_verify` leaves verification switched on, and a misspelled
    `config_file` loads no file at all.
    """
    lowered = {name.lower(): name for name in known}
    for key in unknown:
        close = difflib.get_close_matches(key.lower(), list(lowered), n=1, cutoff=0.6)
        hint = f"; did you mean '{lowered[close[0]]}'?" if close else ""
        msg = f"unknown setting '{key}' in {where} is ignored{hint}"
        logger.warning(msg)
        warnings.warn(msg, UserWarning, stacklevel=stacklevel)


class StaticToolBox:
    @staticmethod
    def _get_path(
        *,
        path: str,
        data: Any,
    ) -> Any | None:

        if not path:
            return None

        if data is None:
            return None

        if "/" not in path:
            return data.get(path, None)

        p_list = path.split("/")

        r: Any = data
        if r is None:
            return None

        for p_item in p_list:
            r = r.get(p_item, None)
            if r is None:
                return None

        return r

    @staticmethod
    def _extract_hashes(data: list[list[str]]) -> dict[str, Any]:
        rr: dict[str, Any] = {}
        for item in data:
            rr[item[0]] = item[1]
        return rr

    @staticmethod
    def _flatten_list(
        data: dict[str, Any],
        *,
        multiple: str,
        single: str,
        with_sort: bool = True,
    ) -> list[str]:

        p_list = data.get(multiple)
        if not p_list:
            return []

        rr = [item[single] for item in p_list if item.get(single)]

        if with_sort:
            return sorted(rr)

        return rr

    # PUBLIC
    @staticmethod
    def _exists_posix_path(
        *,
        item_path: str,
    ) -> tuple[bool, str]:

        fp = Path(item_path)
        exists = fp.exists()
        what = ""
        if exists:
            if fp.is_dir():
                what = "D"
            elif fp.is_file():
                what = "F"

        return exists, what

    @staticmethod
    def _simple_path_to_posix(
        *,
        target_path: str,
    ) -> str:

        return target_path.replace("\\", "/")

    @staticmethod
    def make_logger(
        *,
        my_logger: logging.Logger,
    ) -> None:
        """Set up `my_logger` for a script: a console handler and a log file.

        - `my_logger` is set to DEBUG.
        - The console handler logs at the level in the LOG_LEVEL environment
          variable (default WARNING).
        - The file handler writes `<program>.log` in the current directory, at
          INFO, or at DEBUG when ENVIRONMENT is "development" or "testing", which
          also adds the file and line to each record.

        Calling it again replaces the two handlers an earlier call installed,
        and closes the old log file, instead of adding two more; before, every
        call duplicated each log line once more. Handlers the caller added
        themselves are left alone.
        """
        if my_logger is None:
            msg = "my_logger must not be None"
            raise SpectraAssureInvalidAction(message=msg)

        for handler in list(my_logger.handlers):
            if getattr(handler, _MADE_BY_MAKE_LOGGER, False):
                my_logger.removeHandler(handler)
                handler.close()

        my_logger.setLevel(logging.DEBUG)

        my_level = os.getenv("LOG_LEVEL", "WARNING")
        my_env = os.getenv("ENVIRONMENT", "PRODUCTION")

        prog_name = os.path.basename(sys.argv[0])
        if prog_name.lower().endswith(".py"):
            prog_name = prog_name[:-3]
        file_name = f"{prog_name}.log"

        fh = logging.FileHandler(file_name)
        fh.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        if my_env.lower() in ["development", "testing"]:
            formatter = logging.Formatter(
                "%(asctime)s - %(pathname)s:%(lineno)s - %(name)s - %(levelname)s - %(message)s"
            )
            fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(my_level)

        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        # add the handlers to my_logger, marked so that a later call can find them.
        # The list is annotated because mypy 1.10 (the minimum in pyproject.toml)
        # infers a tuple of a StreamHandler and a FileHandler as `object`.
        installed: list[logging.Handler] = [ch, fh]
        for handler in installed:
            setattr(handler, _MADE_BY_MAKE_LOGGER, True)
            my_logger.addHandler(handler)

    @staticmethod
    def _extract_purl_components(package_url: str) -> tuple[str, str, str]:
        """Split the Portal's `project/package@version` notation into its three parts.

        Despite its name this does not parse a package URL (PURL): it accepts
        `project/package@version`, which has no `pkg:` scheme, and nothing
        checks for one. The SDK itself does not call it; it is reached only
        through the deprecated `extract_purl_components` alias (I-19), and goes
        with that alias in a major release. Imports check their PURL with
        `_import_body` (I-22).
        """

        if "@" not in package_url:
            msg = "Package URLs must use the format 'project/package@version': missing '@'"
            raise SpectraAssureInvalidAction(message=msg)

        l1: list[str] = package_url.rsplit("@", 1)
        if len(l1) != 2:
            msg = "Package URLs must use the format 'project/package@version'"
            raise SpectraAssureInvalidAction(message=msg)

        if "/" not in l1[0]:
            msg = "Package URLs must use the format 'project/package@version': missing '/'"
            raise SpectraAssureInvalidAction(message=msg)

        l2: list[str] = l1[0].rsplit("/", 1)
        if len(l2) != 2:
            msg = "Package URLs must use the format 'project/package@version'"
            raise SpectraAssureInvalidAction(message=msg)

        version: str = l1[1]
        project: str = l2[0]
        package: str = l2[1]

        return project, package, version

    @staticmethod
    def _remove_temp_file_if_exists(file_path: str) -> None:
        fp = Path(file_path)
        fp.unlink(missing_ok=True)  # UNLINK THE temp file
        logger.info("temp file removed: %s", file_path)

    @staticmethod
    def _extract_target_file_name(
        *,
        download_url: str,
    ) -> str | None:
        u_info = urllib.parse.urlparse(download_url)
        u_query = urllib.parse.parse_qs(u_info.query)

        k = "response-content-disposition"
        p = u_query.get(k)
        if p is None or len(p) == 0:
            msg = f"no target filename extracted from URL {download_url} using: {k}"
            logger.error(msg)
            return None

        r = r'filename="([^"]+)"'
        zz = re.findall(r, p[0])
        if len(zz) == 0:
            msg = f"no target filename extracted from URL {download_url} using 'regex: {r}'"
            logger.error(msg)
            return None

        target_file_name = str(zz[0])

        return target_file_name


class SpectraAssureApi(  # pylint: disable=too-many-instance-attributes
    StaticToolBox,
    SpectraAssureApiDelete,
    SpectraAssureApiGet,
    SpectraAssureApiPatch,
    SpectraAssureApiPost,
    SpectraAssureApiPut,
):
    keywords = [
        "host",
        "server",
        "organization",
        "group",
        #
        "token",
        #
        "proxy_server",
        "proxy_port",
        "proxy_user",
        "proxy_password",
        #
        "timeout",
        "connect_timeout",
        "read_timeout",
        "auto_adapt_to_throttle",
        "no_ssl_verify",
    ]

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        #
        host: str | None = None,
        server: str | None = None,
        organization: str | None = None,
        group: str | None = None,
        #
        token: str | None = None,
        #
        proxy_server: str | None = None,
        proxy_port: int | None = None,
        proxy_user: str | None = None,
        proxy_password: str | None = None,
        #
        # The timeouts default to None, not to a number: a number here always
        # counts as "explicitly given" and so overrides the config file, which
        # made every timeout in the file unreachable. The defaults are applied
        # below, after the file and the arguments have been merged.
        timeout: int | None = None,  # in seconds, waiting for the response
        read_timeout: int | None = None,  # in seconds, waiting for the response
        connect_timeout: int | None = None,  # in seconds, waiting for the connection
        #
        auto_adapt_to_throttle: bool | None = None,
        #
        api_version: str = "v1",
        api_domain: str = "secure.software",
        api_proto: str = "https",
        #
        config_file: str | None = None,
        no_ssl_verify: bool | None = None,
        #
        **additional_args: Any,
    ) -> None:
        # merge args given and args from optional config file into new_args
        old_args: dict[str, Any] = {
            "host": host,
            "server": server,
            "organization": organization,
            "group": group,
            #
            "token": token,
            #
            "proxy_server": proxy_server,
            "proxy_port": proxy_port,
            "proxy_user": proxy_user,
            "proxy_password": proxy_password,
            #
            "timeout": timeout,
            "connect_timeout": connect_timeout,
            "read_timeout": read_timeout,
            "auto_adapt_to_throttle": auto_adapt_to_throttle,
            "no_ssl_verify": no_ssl_verify,
        }
        logger.debug("no_ssl_verify: %s", no_ssl_verify)

        # `timeout` is the older name for `read_timeout`; the two are one setting.
        # Folding the alias in here, before the merge, keeps "arguments beat the
        # file" true for either spelling: `timeout=60` overrides a `read_timeout`
        # in the config file just as `read_timeout=60` would.
        if read_timeout is None and timeout is not None:
            old_args["read_timeout"] = timeout

        # `additional_args` is the one keyword that is meant to be passed through.
        unexpected = [k for k in additional_args if k != "additional_args"]
        _warn_unknown_settings(
            where="the arguments",
            unknown=unexpected,
            known=[*self.keywords, "config_file", "api_version", "api_domain", "api_proto"],
            stacklevel=3,
        )

        new_args = self._get_config_file(
            config_file,
            old_args,
        )
        self._validate_minimal_config_complete(new_args)  # may raise exception

        self.host = new_args.get("host", None)
        self.server = new_args.get("server", None)
        self.organization = new_args.get("organization", None)
        self.group = new_args.get("group", None)

        # _validate_minimal_config_complete has already refused a missing or None
        # token, so it is present here; a separate None check could never fire.
        checked_token: str = new_args["token"]

        throttle = new_args.get("auto_adapt_to_throttle")
        if throttle is None:
            throttle = DEFAULT_AUTO_ADAPT_TO_THROTTLE

        # Within one source `read_timeout` wins over its alias `timeout`.
        read_seconds = int(new_args.get("read_timeout") or new_args.get("timeout") or DEFAULT_READ_TIMEOUT)

        # START: all args used
        super().__init__(
            token=checked_token,
            #
            timeout=read_seconds,
            connect_timeout=int(new_args.get("connect_timeout") or DEFAULT_CONNECT_TIMEOUT),
            read_timeout=read_seconds,
            auto_adapt_to_throttle=bool(throttle),
            #
            proxy_server=new_args.get("proxy_server", None),
            proxy_port=new_args.get("proxy_port", None),
            proxy_user=new_args.get("proxy_user", None),
            proxy_password=new_args.get("proxy_password", None),
            #
            no_ssl_verify=new_args.get("no_ssl_verify", False),
        )
        logger.debug("no_ssl_verify: %s", self.no_ssl_verify)

        # currently only as method args
        self.api_version = api_version
        self.api_domain = api_domain
        self.api_proto = api_proto
        # END: all args used

        self.base_url = self._set_base_url()

        self.additional_args: dict[str, Any] = {}
        for k, v in additional_args.items():
            self.additional_args[k] = v
        logger.debug("additional args: %s", self.additional_args)
        logger.debug("no_ssl_verify: %s", self.no_ssl_verify)

    def _get_config_file(
        self,
        config_file: str | None,
        args: dict[str, Any],
    ) -> dict[str, Any]:

        if config_file is None:
            logger.info("no config file provided; using the specified keyword args")
            return args

        if not config_file.lower().endswith(".json"):
            msg = f"the config file must end in '.json'; currently you have {config_file}"
            raise SpectraAssureInvalidAction(message=msg)

        new_args: dict[str, Any] = {}

        # Every problem with the file raises SpectraAssureInvalidAction, with the
        # original error as its __cause__. Before, a missing file or bad JSON
        # surfaced as FileNotFoundError or JSONDecodeError, and a file holding a
        # JSON list or string as an AttributeError from inside the SDK.
        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
        except OSError as e:
            msg = f"the config file {config_file} cannot be read: {e.strerror or e}"
            raise SpectraAssureInvalidAction(message=msg) from e
        except json.JSONDecodeError as e:
            msg = f"the config file {config_file} is not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})"
            raise SpectraAssureInvalidAction(message=msg) from e
        except UnicodeDecodeError as e:
            msg = f"the config file {config_file} is not UTF-8 text: {e.reason} at byte {e.start}"
            raise SpectraAssureInvalidAction(message=msg) from e

        conf_key = "SpectraAssureApi"  # we need a subsection called: "SpectraAssureApi"
        if not isinstance(data, dict):
            msg = f"the config file {config_file} must contain a JSON object, not {_json_kind(data)}"
            raise SpectraAssureInvalidAction(message=msg)

        conf_data = data.get(conf_key)
        if conf_data is None:
            msg = f"the config file is missing the section {conf_key}"
            raise SpectraAssureInvalidAction(message=msg)

        if not isinstance(conf_data, dict):
            msg = f"the '{conf_key}' section of {config_file} must be a JSON object, not {_json_kind(conf_data)}"
            raise SpectraAssureInvalidAction(message=msg)

        _warn_unknown_settings(
            where=f"the '{conf_key}' section of {config_file}",
            unknown=[k for k in conf_data if k not in self.keywords],
            known=self.keywords,
            stacklevel=4,
        )

        for k in self.keywords:
            if k in conf_data:
                new_args[k] = conf_data.get(k)

            if k in args and args[k] is not None:
                new_args[k] = args[k]  # args given to __init__ will overwrite the config file

        if new_args.get("no_ssl_verify") is None:
            new_args["no_ssl_verify"] = False
        if new_args.get("auto_adapt_to_throttle") is None:
            new_args["auto_adapt_to_throttle"] = DEFAULT_AUTO_ADAPT_TO_THROTTLE
        if new_args.get("timeout") is None:
            new_args["timeout"] = DEFAULT_TIMEOUT
        if new_args.get("connect_timeout") is None:
            new_args["connect_timeout"] = DEFAULT_CONNECT_TIMEOUT

        return new_args

    def _set_base_url(self) -> str:
        # `None` is refused as well as the empty string: str(None) is "None", so a
        # plain length check let api_version=None through and produced a base URL
        # ending in /api/public/None.
        if self.api_version is None or len(str(self.api_version)) == 0:
            msg = "Fatal: the api_version is not set"
            raise SpectraAssureInvalidAction(message=msg)

        if self.api_domain is None or len(str(self.api_domain)) == 0:
            msg = "Fatal: the api_domain is not set"
            raise SpectraAssureInvalidAction(message=msg)

        if self.api_proto is None or len(str(self.api_proto)) == 0:
            msg = "Fatal: the api_proto is not set"
            raise SpectraAssureInvalidAction(message=msg)

        tail = f"api/public/{self.api_version}"

        # https://{portalUrl}/api/public/v1/create/{organization}/{group}/pkg:rl/{project}/{package}
        # https://{portalUrl}/api/public/v1/community/...

        # first the special cases
        if self.server in ["trial", "playground"]:
            return f"{self.api_proto}://{self.server}.{self.api_domain}/{tail}"

        # then when both are set
        if self.host and self.server:
            return f"{self.api_proto}://{self.host}/{self.server}/{tail}"

        if self.host:
            return f"{self.api_proto}://{self.host}/{tail}"

        if self.server:
            return f"{self.api_proto}://my.{self.api_domain}/{self.server}/{tail}"

        raise RuntimeError("Fatal: no 'server' or 'host' specified.")

    def _validate_minimal_config_complete(
        self,
        args: dict[str, Any],
    ) -> None:
        """Validate if the minimal mandatory parameters have been provided.

        Note:
            raises an exception if not all mandatory parameters have been provided

        """
        server = args.get("server")
        host = args.get("host")
        has_server = server is not None and len(str(server)) > 0
        has_host = host is not None and len(str(host)) > 0

        organization = args.get("organization")
        has_org = organization is not None and len(str(organization)) > 0

        group = args.get("group")
        has_group = group is not None and len(str(group)) > 0

        token = args.get("token")
        has_token = token is not None and len(str(token)) > 0

        # Name only what is missing. The old message listed all four settings
        # whether missing or not ("TOKEN is None, mandatory: True; cannot be
        # True."). The token's value is never part of the message.
        missing = [
            name
            for name, present in (
                ("host or server", has_host or has_server),
                ("organization", has_org),
                ("group", has_group),
                ("token", has_token),
            )
            if not present
        ]
        if missing:
            msg = (
                f"minimal required settings are missing or empty: {', '.join(missing)}; "
                "give them as named arguments or in the configuration file"
            )
            raise SpectraAssureInvalidAction(message=msg)

    def _show_debug(
        self,
        args: dict[str, Any],
        text: str,
    ) -> None:
        if os.getenv("LOG_LEVEL", "") == "DEBUG":
            for k, v in args.items():
                if k not in ["token", "proxy_password"]:
                    msg = f"{text} {k}: {v}"
                    logger.debug(msg)
                else:
                    if v:
                        msg = f"{text} {k}: {len(v)}"
                        logger.debug(msg)
                    else:
                        msg = f"{text} {k}: no value"
                        logger.debug(msg)

    def _get_customer_context(self) -> str:
        return f"{self.server}:{self.organization}:{self.group}"

    def get_additional_args(self) -> Any:
        if self.additional_args.get("additional_args") is not None:
            return self.additional_args.get("additional_args")

        return self.additional_args
