import logging
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Tuple,
    List,
    Dict,
    Any,
)

from spectra_assure_api_client.communication.api import SpectraAssureApi
from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

logger = logging.getLogger(__name__)


class SpectraAssureApiOperationsBase(
    ABC,
    SpectraAssureApi,
):
    @staticmethod
    def _what(
        *,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
    ) -> str:
        """
        Action:
            Determine the context of the operation we are executing.

        Args:
          - project: str | None;
            If we don't have a project name,
            we are doing something with a group.

          - package: str | None;
            If we don't have a package name,
            we are doing something with a project.

          - version: str | None;
            If we don't have a version name,
            we are doing something with a package.

          - If all args are not None,
            we are doing something with a version.

        Return:
          - what: str.

        """
        if project is None:
            return "group"

        if package is None:
            return "project"

        if version is None:
            return "package"

        return "version"

    @staticmethod
    def _extract_hashes(data: List[List[str]]) -> Dict[str, Any]:
        rr: Dict[str, Any] = {}
        for item in data:
            rr[item[0]] = item[1]
        return rr

    @staticmethod
    def _get_path(
        *,
        path: str,
        data: Any,
    ) -> Any | None:
        """
        Action:
            Perform a naive traverse of data by dict keys
            (naive as we don't support arrays).

        Args:
         - path: str, mandatory.
           A path string of steps separated by '/'.
         - data: Any.
           The data we will try to treat as a dict of dicts.

        Return:
         - If there is no path, we return None.
         - If the data we have is None, we return None.
         - If there is no '/', we try the path as-is with the default of None.
         - Otherwise we iterate over the path elements and try to walk the whole path.
        """

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
    def _flatten_list(
        data: Dict[str, Any],
        *,
        multiple: str,
        single: str,
        with_sort: bool = True,
    ) -> List[str]:
        """
        Action:
            Try to flatten a dict into a list.

        Args:
         - data: Dict[str, Any], mandatory.
            The data we work on.
         - multiple: str , mandatory.
            The name of the top-level collection.
         - single: str, mandatory:
            The name of each item to extract.
         - with_sort: bool , default True, optional.
            If True, the result is sorted,
            otherwise the result is unsorted.

        Return:
            Return the flattened list,
            optionally sorted,
            based on the provided selectors.

        Note:
            Used on the results of list() for any level lower than 'version' to find:
             - the versions in a package or
             - the packages in a project or
             - the projects in a group.
        """

        p_list = data.get(multiple)
        if not p_list:
            return []

        rr = [item[single] for item in p_list if item.get(single)]

        if with_sort:
            return sorted(rr)

        return rr

    def _make_current_url(  # pylint: disable=too-many-arguments
        self,
        *,
        action: str,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
        report_type: str | None = None,
    ) -> str:
        what = self._what(
            project=project,
            package=package,
            version=version,
        )
        # action_base + /pkg:rl/{project}/{package}@{version}

        base = self._render_action_org_group_url(action)
        if what == "group":
            return base

        assert project is not None
        base = base + "/pkg:rl/" + project
        if what == "project":
            return base

        assert package is not None
        base = base + "/" + package
        if what == "package":
            return base

        assert version is not None
        base = base + "@" + version
        if what == "version":
            if action not in ["report"]:
                return base

            # note report has the report_type in the middle of the url (not orthogonal)
            tail = f"/{report_type}/pkg:rl/{project}/{package}@{version}"
            return self._render_action_org_group_url(action) + tail

        # https://{portalUrl}/api/public/v1/pack/safe/{organization}/{group}/pkg:rl/{project}/{package}@{version}
        msg = f"'_make_current_url' {action} with unsupported parameters: {what}"
        raise SpectraAssureInvalidAction(message=msg)

    # Public

    @staticmethod
    def exists_posix_path(
        *,
        item_path: str,
    ) -> Tuple[bool, str]:
        """
        Action:
            Test if the path exists and check if it is a file or a directory.

        Args:
         - item_path: str, mandatory.
            The path to be checked.

        Return:
         - Tuple[exists: bool, type: str]
           - exists:
             - True if the path exists
             - False otherwise
           - type:
             - If the path points to a 'directory', type is "D"
             - If the path points to a 'file', type is "F"
             - Otherwise type is ""

        """
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
    def simple_path_to_posix(
        *,
        target_path: str,
    ) -> str:
        """
        Action:
            Return a path with more POSIX-like separators
            (path does not need to exist).

        Args:
         - target_path: str, mandatory.

        Return:
         - aPath: str.

        Notes:
            We simply change all occurrences of \\ into /
            Linux, Mac and Windows all support POSIX paths.
        """
        return target_path.replace("\\", "/")

    @staticmethod
    def qp_status(
        *,
        what: str,
        **qp: Any,
    ) -> Dict[str, Any]:
        """
        Action:
            Filter a query parameter dict for the status() call.

        Args:
         - what: str, mandatory: what operation are we performing.
             status only works for 'version'
         - qp: Dict[str,Any], Optional
             status supports the query parameters:
              - build
              - download

        Return:
            A new dict. All unknown or unsupported query parameters will have been removed in the returned dict.
        """
        r: Dict[str, Any] = {}
        if what in ["version"]:
            for k in ["build", "download"]:
                if k in qp:
                    r[k] = qp[k]
        return r

    @classmethod
    def make_logger(
        cls,
        *,
        my_logger: logging.Logger,
    ) -> None:
        """
        Action:
            Using the provided myLogger,
            set up a default myLogger
             - that writes to stderr
             - and to a logfile.

        Args:
            my_logger: logging.Logger, mandatory.

        Returns:
            None

        Raises
            no specific exceptions are raised by the implementation.

        Notes:
            The log file is derived from the current executing program name
            and if the program name ends with '.py' that part is stripped.

            Supports reading LOG_LEVEL from the environment for stderr .
            the file always uses DEBUG
        """
        assert my_logger is not None
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

        # add the handlers to my_logger
        my_logger.addHandler(ch)
        my_logger.addHandler(fh)

    @abstractmethod
    def status(
        self,
        *,
        project: str,
        package: str,
        version: str,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,
    ) -> Any:
        """needed here for the download operation"""

    @abstractmethod
    def list(
        self,
        *,
        project: str | None = None,
        package: str | None = None,
        version: str | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,  # not actually used in list
    ) -> Any:
        """needed here for the download operation"""
