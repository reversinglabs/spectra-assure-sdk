import hashlib
import logging
import os
import tempfile
import uuid

import requests

from spectra_assure_api_client.communication.api import SpectraAssureApi

from .constants import (
    DEFAULT_BLOCK_SIZE,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
)
from .downloader_exceptions import (
    UrlDownloaderFileVerifyIssue,
    UrlDownloaderTargetDirectoryIssue,
    UrlDownloaderTargetFileIssue,
    UrlDownloaderTempFileIssue,
    UrlDownloaderUnknownHashKey,
)

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class UrlDownloader:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        target_dir: str,
        #
        hash_key: str = "sha256",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        timeout: int | None = None,  # alias of read_timeout, kept for existing callers
        read_timeout: int | None = None,
        connect_timeout: int | None = None,
        block_size: int = DEFAULT_BLOCK_SIZE,
        #
        with_overwrite_existing_files: bool = False,
        with_verify_after_download: bool = True,
        with_verify_existing_files: bool = True,
        #
        no_ssl_verify: bool = False,
        session: requests.Session | None = None,
        proxies: dict[str, str] | None = None,
    ) -> None:
        self.with_overwrite_existing_files = with_overwrite_existing_files
        self.with_verify_after_download = with_verify_after_download
        self.with_verify_existing_files = with_verify_existing_files

        self.proxies = proxies
        self.no_ssl_verify = no_ssl_verify
        logger.debug(f"no_ssl_verify: {self.no_ssl_verify}")

        # The client's session, when it passed one: the archive host is usually the
        # same host across a multi-file download, so the connection is reused.
        # Without one, a private session is used so this class still works alone.
        self.session = session if session is not None else requests.Session()

        self._validate_target_dir(target_dir)
        self._validate_hash_key(hash_key)
        self._validate_chunk_size(chunk_size)
        # `read_timeout` wins over its alias `timeout`. Only `timeout` used to be
        # looked at, so the `read_timeout` the client passes was ignored and
        # every download ran on the default.
        self._validate_read_timeout(read_timeout or timeout or DEFAULT_READ_TIMEOUT)
        self._validate_connect_timeout(connect_timeout or DEFAULT_CONNECT_TIMEOUT)
        self._validate_block_size(block_size)

    def _validate_block_size(self, block_size: int) -> None:
        min_block_size = 4 * 1024
        max_block_size = 2**16  # 64k

        if block_size < min_block_size or block_size > max_block_size:
            block_size = max_block_size

        self.block_size = block_size

    def _validate_hash_key(self, hash_key: str) -> None:
        known_sha_list = [
            "sha1",
            "sha256",
        ]

        if hash_key not in known_sha_list:
            msg = f"The hash key you provided is not supported; it must be one of {known_sha_list}"
            logger.error(msg)
            raise UrlDownloaderUnknownHashKey(msg)

        self.hash_key = hash_key

    def _validate_read_timeout(self, r_timeout: int) -> None:
        """Clamp the read timeout to 10..3600 seconds, saying so when that changes the value."""
        min_timeout = 10
        max_timeout = 3600

        clamped = min(max_timeout, max(r_timeout, min_timeout))
        if clamped != r_timeout:
            logger.warning(
                "download read timeout of %s seconds is outside %s..%s; using %s seconds",
                r_timeout,
                min_timeout,
                max_timeout,
                clamped,
            )

        self.timeout = clamped  # alias of read_timeout
        self.read_timeout = clamped
        logger.info("set HTTP read timeout to: %s seconds", clamped)

    def _validate_connect_timeout(self, c_timeout: int) -> None:
        """Clamp the connect timeout to 1..10 seconds, saying so when that changes the value."""
        min_timeout = 1
        max_timeout = 10

        clamped = min(max_timeout, max(c_timeout, min_timeout))
        if clamped != c_timeout:
            logger.warning(
                "download connect timeout of %s seconds is outside %s..%s; using %s seconds",
                c_timeout,
                min_timeout,
                max_timeout,
                clamped,
            )

        self.connect_timeout = clamped
        logger.info("set HTTP connect timeout to: %s seconds", clamped)

    def _validate_chunk_size(self, chunk_size: int) -> None:
        min_chunk = 4 * 1024  # 4k
        max_chunk = 64 * 1024  # 64k

        chunk_size = min(max_chunk, chunk_size)
        chunk_size = max(chunk_size, min_chunk)

        self.chunk_size = chunk_size
        logger.info("set chunk size to: %s bytes", chunk_size)

    def _validate_target_dir(self, target_dir: str) -> None:
        target_dir_posix = SpectraAssureApi._simple_path_to_posix(target_path=target_dir)
        exists, what = SpectraAssureApi._exists_posix_path(
            item_path=target_dir_posix,
        )
        if exists is False:
            msg = f"the specified target path does not exist; {target_dir_posix}"
            logger.error(msg)
            raise UrlDownloaderTargetDirectoryIssue(msg)

        if what != "D":
            msg = f"the specified target path exists but is not a directory; {target_dir_posix}"
            logger.error(msg)
            raise UrlDownloaderTargetDirectoryIssue(msg)

        self.target_dir_posix = target_dir_posix
        logger.info("set target path to: %s", self.target_dir_posix)

    def _get_hex_digest(
        self,
        *,
        file_path: str,
    ) -> str | None:
        if self.hash_key not in ["sha1", "sha256"]:
            msg = f"hash_key must be one of ['sha1', 'sha256']; it is '{self.hash_key}'"
            raise UrlDownloaderUnknownHashKey(msg)

        if self.hash_key == "sha1":
            sha_sum = hashlib.sha1()
        else:
            sha_sum = hashlib.sha256()

        try:
            with open(file_path, mode="rb") as f:
                block = f.read(self.block_size)
                while len(block) != 0:
                    sha_sum.update(block)
                    block = f.read(self.block_size)
            return sha_sum.hexdigest()

        except Exception as e:  # pylint:disable=broad-exception-caught
            msg = f"cannot calculate {self.hash_key} of file: {file_path} -> {e}"
            logger.exception(msg)
            raise UrlDownloaderFileVerifyIssue(msg) from e

    def _make_temp_file(
        self,
        *,
        url: str,
        dir_path: str,
    ) -> str:
        """Create a new, empty temporary file for one download attempt and return its path.

        The name is unique per attempt: `.<uuid5 of the URL>.<random>.tmp`. It used
        to be `.<uuid5 of the URL>.tmp` only, so a file left behind by an
        interrupted run had exactly the name the next attempt wanted, and that
        attempt refused to start. Now a leftover is an inert stray file. It is
        never deleted here, because with a shared name it could belong to a
        download still running in another process.

        mkstemp creates the file exclusively, so two attempts never write to the
        same temporary file.
        """
        uuid_name = uuid.uuid5(
            uuid.NAMESPACE_URL,
            url,
        )
        handle, file_path = tempfile.mkstemp(prefix=f".{uuid_name}.", suffix=".tmp", dir=dir_path)
        os.close(handle)
        return file_path

    def _verify_existing_file(
        self,
        *,
        file_path: str,
        hashes: dict[str, str],
    ) -> None:
        digest = hashes.get(self.hash_key)
        if digest is None:
            msg = f"no digest found for '{self.hash_key}' in: {hashes}"
            logger.error(msg)
            raise UrlDownloaderUnknownHashKey(message=msg)

        my_hex_digest = self._get_hex_digest(file_path=file_path)

        if digest != my_hex_digest:
            msg = f"verify of '{file_path}' fails, expected: '{self.hash_key}:{digest}' but got: '{my_hex_digest}'"
            logger.error(msg)
            raise UrlDownloaderFileVerifyIssue(msg)

        logger.info("verify of '%s' ok: '%s:%s'", file_path, self.hash_key, digest)

    def _download_with_optional_verify(  # pylint: disable=too-many-arguments
        self,
        *,
        download_url: str,
        file_path: str,
        hashes: dict[str, str],
    ) -> None:
        """Args:
         - download_url: str;
           The actual URL from which the file will be downloaded.
           Valid for a short interval only
         - file_path: str;
           The target file path.
         - hashes: Dict[str, str];
           The current dict of hashes (sha1 and sha256 are supported for verification).

        Return:
            None if successful.

        Raises:
            Whatever the GET request raises on HTTPS errors

        Notes:

        """
        # Bound before the try: when the request itself fails (DNS, connect, TLS)
        # there is no response, and the handler below must not trip over that
        # and replace the real error with an UnboundLocalError.
        response: requests.Response | None = None

        try:
            logger.debug("%s %s", download_url, file_path)

            response = self.session.get(
                download_url,
                stream=True,
                timeout=(self.connect_timeout, self.read_timeout),
                verify=not self.no_ssl_verify,
                proxies=self.proxies,
            )
            response.raise_for_status()  # check before starting the download
            h = response.headers
            cl = h.get("Content-Length")
            if cl:
                cl_int = int(cl)

            with open(file_path, mode="wb") as file:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    file.write(chunk)

                size = file.tell()
                if cl and size != cl_int:
                    msg = f"file downloaded: size: {size} does not match Content-Length header: {cl_int}"
                    raise UrlDownloaderFileVerifyIssue(msg)
                logger.info("file downloaded: %s, size: %d", file_path, size)

            if self.with_verify_after_download is True:
                self._verify_existing_file(  # raises error on verify fail
                    file_path=file_path,
                    hashes=hashes,
                )

        except Exception as e:  # pylint:disable=broad-exception-caught
            msg = f"cannot download to {file_path}; {e}"
            logger.exception(msg)
            if response is not None:
                response.close()
            SpectraAssureApi._remove_temp_file_if_exists(file_path)
            raise

    def _check_target_path(
        self,
        *,
        target_file_name: str,
        hashes: dict[str, str],
    ) -> tuple[bool, str]:
        """Args:
         - target_file_name: str; The file name (not the file path)
         - hashes: Dict[str,str]; Supported hashes: sha1 and sha256

        Return:
            Tuple[existsStatus: bool, target_file_path: str]
            If we skip downloading this file:
                existsStatus is False and
                target_file_path is the existing file path
            If we will download this file:
                existsStatus is True and
                target_file_path is the existing file path

        Raises:
            If the target file exists
              and we requested verification
                and the verification fails:
                  we raise: 'UrlDownloaderFileVerifyIssue'

        """
        target_file_path = f"{self.target_dir_posix}/{target_file_name}"
        exists, _ = SpectraAssureApi._exists_posix_path(item_path=target_file_path)
        if exists is False:
            return True, target_file_path  # process this item

        if self.with_overwrite_existing_files is True:
            msg = f"Overwrite: target file exists and overwrite requested: '{target_file_path}'"
            logger.info(msg)
            return True, target_file_path  # process this item

        # file exists and with_overwrite_existing_files is false
        if self.with_verify_existing_files is False:
            msg = f"Skip: target file exists and verification not requested: '{target_file_path}'"
            logger.info(msg)
        else:
            self._verify_existing_file(  # raises error if verify fails
                file_path=target_file_path,
                hashes=hashes,
            )
            logger.info("Skip download of %s - verification passed", target_file_name)

        return False, target_file_path

    def _rename_temp_file_to_target(
        self,
        *,
        file_path: str,
        target_path: str,
    ) -> None:
        """After verification, we must rename the temp file.

        Args:
         - file_path: str; The temp path we downloaded the file to
         - target_path: str; The target path (that may already exist)

        Return:
            None if the rename succeeded.

        Raises:
            If the rename fails, we re-raise the exiting error

        Notes:
            If we do not overwrite the existing file,
            we never come here as the item will already have been skipped earlier

        """
        try:
            logger.debug("try rename: %s -> %s", file_path, target_path)
            # os.replace overwrites an existing target file on every platform.
            # Path.rename only does so on Unix; on Windows it raises FileExistsError,
            # so replacing an existing file (with_overwrite_existing_files) failed there.
            os.replace(file_path, target_path)
            logger.info("rename ok: %s -> %s", file_path, target_path)

        except Exception as e:
            logger.exception("Cannot rename file %s to %s; %s", file_path, target_path, e)
            SpectraAssureApi._remove_temp_file_if_exists(file_path)
            raise

    def _check_temp_path(
        self,
        *,
        temp_dir: str,
        download_url: str,
    ) -> str:
        """Args:
         - temp_dir: str; The location of the temp directory (must exist)
         - download_url: str; The URL we use to get the file name

        Returns:
            the path of a new, empty temporary file

        Raises:
         - UrlDownloaderTempFileIssue: if no temporary file can be created in temp_dir

        """
        try:
            return self._make_temp_file(
                url=download_url,
                dir_path=temp_dir,
            )
        except OSError as e:
            msg = f"cannot create a temporary file in {temp_dir}: {e}"
            logger.error(msg)
            raise UrlDownloaderTempFileIssue(msg) from e

    def _validate_hashes(self, hashes: dict[str, str]) -> None:
        if len(hashes) == 0:
            return

        if self.hash_key not in hashes:
            msg = f"the hash key {self.hash_key} is not present in the hashes dict {hashes}"
            logger.error(msg)
            raise UrlDownloaderUnknownHashKey(msg)

    def _get_target_file_name(self, download_url: str) -> str:
        target_file_name = SpectraAssureApi._extract_target_file_name(
            download_url=download_url,
        )

        if target_file_name is None:
            msg = f"the target file name cannot be extracted from the download URL; {download_url}"
            logger.error(msg)
            raise UrlDownloaderTargetFileIssue(msg)

        target_file_name_posix = SpectraAssureApi._simple_path_to_posix(target_path=target_file_name)
        if "/" in target_file_name_posix:
            target_file_name_posix = os.path.basename(target_file_name_posix)

        return target_file_name_posix

    # PUBLIC

    def download_file_from_url(
        self,
        *,
        download_url: str,
        hashes: dict[str, str],
    ) -> tuple[bool, str]:
        """Action:
            With the specified arguments,
            download the file from the URL into the provided target directory,
            and verify the downloaded file if requested to do so.

        Args:
         - download_url: str; The download URL
         - hashes: Dict[str, str]; A dict with hashes for sha1 or sha256 (key is 'sha1' or 'sha256')

        Return: Tuple[downloaded: bool, file_path: str]
            If downloaded is False, we skipped the download as the target already exist and validates ok,
            we report the existing file path
            If downloaded is True, we downloaded the file and validated it (if requested),
            we report the resulting file path

        Raises:
         - UrlDownloaderUnknownHashKey:
            If we cannot find the 'hash_key' specified during __init__().
         - UrlDownloaderTargetDirectoryIssue:
            If the target directory has problems.
         - UrlDownloaderTargetFileIssue:
            If the target file has an issue.
         - UrlDownloaderTempFileIssue:
            If no temporary file can be created in the target directory.
         - UrlDownloaderFileVerifyIssue:
            If there are problems with verifying either the downloaded file or the existing file.

        Notes:
            Spectra Assure Portal download URLs are valid for a limited time,
            so the URL must be used directly after requesting it.

        """
        self._validate_hashes(hashes)
        target_file_name = self._get_target_file_name(download_url)  # only the name not the full path

        shall_we_process, target_file_path = self._check_target_path(  # this also checks overwrite requested yes/no
            target_file_name=target_file_name,
            hashes=hashes,
        )
        if shall_we_process is False:  # skip this file
            return False, target_file_path

        # now we have a full path to the actual target file,
        # that may exist already and has been verified if it exists

        temp_file_path = self._check_temp_path(  # may raise tempfileissue
            temp_dir=self.target_dir_posix,
            download_url=download_url,
        )

        self._download_with_optional_verify(  # raises error on download or verify fail
            download_url=download_url,
            file_path=temp_file_path,
            hashes=hashes,
        )

        self._rename_temp_file_to_target(  # raises error if rename fails
            file_path=temp_file_path,
            target_path=target_file_path,
        )
        target_file_path = os.path.realpath(target_file_path)

        return True, target_file_path
