import os
import json
import logging
from typing import (
    List,
    Tuple,
    Dict,
    Any,
)

from .exceptions import (
    SpectraAssureInvalidAction,
)

from .delete import SpectraAssureApiDelete
from .get import SpectraAssureApiGet
from .patch import SpectraAssureApiPatch
from .post import SpectraAssureApiPost
from .put import SpectraAssureApiPut

logger = logging.getLogger(__name__)


class SpectraAssureApi(  # pylint: disable=too-many-instance-attributes
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
        timeout: int = 10,  # in seconds
        auto_adapt_to_throttle: bool = False,
        #
        api_version: str = "v1",
        api_domain: str = "secure.software",
        api_proto: str = "https",
        #
        config_file: str | None = None,
        no_ssl_verify: bool = False,
        #
        **additional_args: Any,
    ) -> None:
        """
        Action:
          Initialize an instance of 'SpectraAssureApi'
          and validate all mandatory parameters.

        Args:
         - host: str | None = None;
         - server: str | None = None;
         - organization: str | None = None;
         - group: str | None = None;

         - token: str | None = None;

         - proxy_server: str | None = None;
         - proxy_port: int | None = None;
         - proxy_user: str | None = None;
         - proxy_password: str | None = None;

         - timeout: int = 10;
            The request timeout to be used for HTTPS requests.

         - auto_adapt_to_throttle: bool = False;
            Some requests may result in throttling and require a minimal wait time before the next request.
            With this option, you can automatically wait for the data to become available
            and for the required time to pass.
            This approach is recommended for 'batch' type processing.

         - api_version: str = "v1";
            Current default API version; do not change.

         - api_domain: str = "secure.software";
            Current default API domain; do not change.

         - api_proto: str = "https";
            Current default API proto; do not change.

         - config_file: str | None = None;
           You can define arguments in a config file instead of specifying them during init.
           Specified arguments always override arguments provided in a config file.

           The config file supports the following arguments:
            - host
            - server
            - organization
            - group

            - token

            - proxy_server
            - proxy_port
            - proxy_user
            - proxy_password

            - timeout
            - auto_adapt_to_throttle

         - additional_args: Any;
            Any additional arguments will be collected in a dictionary that can be used via:
             - getAdditionalArgs()

        Returns:
          an initiated and valid 'SpectraAssureApi'; otherwise raises an exception.

        Raises:
         - SpectraAssureInvalidAction

        Notes:
          By the time init finishes, the following values must have been defined;
          otherwise we raise an exception. See: _validateMinimalConfigComplete().
           - server or host or both: str;
           - organization: str;
           - group: str:
           - token: str:
        """

        # merge args given and args from optional config file into new_args
        old_args: Dict[str, Any] = {
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
            "auto_adapt_to_throttle": auto_adapt_to_throttle,
            "no_ssl_verify": no_ssl_verify,
        }

        self.show_debug(old_args, "old_args")
        new_args = self._get_config_file(
            config_file,
            old_args,
        )
        self.show_debug(new_args, "new_args")
        self._validate_minimal_config_complete(new_args)  # may raise exception

        self.host = new_args.get("host", None)
        self.server = new_args.get("server", None)
        self.organization = new_args.get("organization", None)
        self.group = new_args.get("group", None)

        token = new_args.get("token")
        assert token is not None

        # START: all args used
        super().__init__(
            token=token,
            #
            timeout=int(new_args.get("timeout", 10)),
            auto_adapt_to_throttle=bool(new_args.get("auto_adapt_to_throttle", False)),
            #
            proxy_server=new_args.get("proxy_server", None),
            proxy_port=new_args.get("proxy_port", None),
            proxy_user=new_args.get("proxy_user", None),
            proxy_password=new_args.get("proxy_password", None),
            #
            no_ssl_verify=new_args.get("no_ssl_verify", False),
        )

        # currently only as method args
        self.api_version = api_version
        self.api_domain = api_domain
        self.api_proto = api_proto
        # END: all args used

        self.base_url = self._set_base_url()

        self.additional_args: Dict[str, Any] = {}
        for k, v in additional_args.items():
            self.additional_args[k] = v
        logger.debug("additional args: %s", self.additional_args)

    def show_debug(
        self,
        args: Dict[str, Any],
        text: str,
    ) -> None:
        if os.getenv("LOG_LEVEL", "") == "DEBUG":
            for k, v in args.items():
                if k != "token":
                    msg = f"{text} {k}: {v}"
                    logger.debug(msg)
                else:
                    if v:
                        msg = f"{text} {k}: {len(v)}"
                        logger.debug(msg)
                    else:
                        msg = f"{text} {k}: no value"
                        logger.debug(msg)

    def _get_config_file(
        self,
        config_file: str | None,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:

        if config_file is None:
            logger.info("no config file provided; using the specified keyword args")
            return args

        if not config_file.lower().endswith(".json"):
            logger.error(f"the config file must end in '.json'; currently you have {config_file}")
            return args

        new_args: Dict[str, Any] = {}

        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

            conf_key = "SpectraAssureApi"  # we need a subsection called: "SpectraAssureApi"
            conf_data = data.get(conf_key)
            if conf_data is None:
                logger.info(f"the config file is missing the section {conf_key}")
                return args

            for k in self.keywords:
                if k in conf_data:
                    new_args[k] = conf_data.get(k)

                if k in args and args[k] is not None:
                    new_args[k] = args[k]  # args given to __init__ will overwrite the config file

        return new_args

    def _set_base_url(self) -> str:
        assert len(str(self.api_version)) > 0, "Fatal: the api_version is not set"
        assert len(str(self.api_domain)) > 0, "Fatal: the api_domain is not set"
        assert len(str(self.api_proto)) > 0, "Fatal: the api_proto is not set"

        tail = f"api/public/{self.api_version}"

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

    def _render_action_org_group_url(
        self,
        action: str,
    ) -> str:
        assert len(str(action)) > 0, "Fatal: the action cannot be empty"
        assert len(str(self.organization)) > 0, "Fatal: the organization is not set"
        assert len(str(self.group)) > 0, "Fatal: the group is not set"

        if action == "rl_safe":
            action = "pack/safe"

        return f"{self._get_base_url()}/{action}/{self.organization}/{self.group}"

    def _get_base_url(self) -> str:
        return self.base_url

    def _validate_minimal_config_complete(
        self,
        args: Dict[str, Any],
    ) -> None:
        """Validate if the minimal mandatory parameters have been provided.

        Note:
            exits the program if not all mandatory parameters have been provided
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

        # pylint: disable=too-many-boolean-expressions
        if (has_server is False and has_host is False) or has_org is False or has_group is False or has_token is False:
            ll = [
                f"HOST, optional: {host}; SERVER, optional: {server}; cannot be both empty.",
                f"ORGANIZATION, mandatory: {organization}; cannot be empty.",
                f"GROUP, mandatory: {group}; cannot be emptry.",
                f"TOKEN is None, mandatory: {token is None}; cannot be True.",
            ]
            msg = "FATAL: minimal required parameters are not set properly; " + ", ".join(ll)
            raise SpectraAssureInvalidAction(message=msg)

    # PUBLIC

    def get_customer_context(self) -> str:
        return f"{self.server}:{self.organization}:{self.group}"

    @staticmethod
    def extract_purl_components(package_url: str) -> Tuple[str, str, str]:
        # Project/Package@Version

        if "@" not in package_url:
            msg = "Package URLs must use the format 'project/package@version': missing '@'"
            raise SpectraAssureInvalidAction(message=msg)

        l1: List[str] = package_url.split("@")

        if "/" not in l1[0]:
            msg = "Package URLs must use the format 'project/package@version': missing '/'"
            raise SpectraAssureInvalidAction(message=msg)

        l2: List[str] = l1[0].split("/")

        version: str = l1[1]
        project: str = l2[0]
        package: str = l2[1]

        return project, package, version

    @staticmethod
    def make_purl(project: str, package: str, version: str) -> str:
        return f"{project}{package}@{version}"

    def get_additional_args(self) -> Any:
        if self.additional_args.get("additional_args") is not None:
            return self.additional_args.get("additional_args")

        return self.additional_args
