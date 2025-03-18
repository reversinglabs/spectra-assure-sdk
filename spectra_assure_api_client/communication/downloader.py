import hashlib
import logging
import os
import re
import urllib.parse
import uuid
from pathlib import Path
from typing import (
    Dict,
    Tuple,
)

import requests

from .downloader_exceptions import (
    UrlDownloaderUnknownHashKey,
    UrlDownloaderTargetDirectoryIssue,
    UrlDownloaderTargetFileIssue,
    UrlDownloaderTempFileIssue,
    UrlDownloaderFileVerifyIssue,
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
        chunk_size: int = (16 * 1024),  # 16KByte
        timeout: int = (60 * 60),  # in seconds 1H
        block_size: int = 2**16,
        #
        with_overwrite_existing_files: bool = False,
        with_verify_after_download: bool = True,
        with_verify_existing_files: bool = True,
    ) -> None:
        """
        Actions:
            Initialize a 'UrlDownloader'.

        Args:
         - target_dir: str, mandatory;
            Where to download the file; the directory MUST exist.

         - hash_key: str, default: "sha256", optional;
            By default, we verify against 'sha256';
            alternatively, we can verify against 'sha1'.

         - chunk_size: int, default: 16k, optional;
            By default, the file is transferred in chunks of 16k.

         - timeout: int, default (60 * 60), optional;
            When downloading the file, the HTTPS request timeout is set to 1 hour.

         - block_size: int, default 64k, optional;
            When validating the hash of the downloaded or existing file, we read data in blocks of 64k.

         - with_overwrite_existing_files: bool = False, optional;
            If the file exists in target directory, we can choose to overwrite it
            or skip the download (if the hash verification passes when requested).

         - with_verify_after_download: bool = True, optional;
            After a successful download, we verify against the provided hash.

         - with_verify_existing_files: bool = True, optional;
            If the file already exists in target directory, we can verify against the provided hash.

        Raises:
         - UrlDownloaderTargetDirectoryIssue:
            If the target file path does not exist or is not a directory, we raise an exception.

        Notes:
            The specified target directory must exist.
            Internally, all paths are converted to POSIX paths.
        """

        self.with_overwrite_existing_files = with_overwrite_existing_files
        self.with_verify_after_download = with_verify_after_download
        self.with_verify_existing_files = with_verify_existing_files

        self._validate_target_dir(target_dir)
        self._validate_hash_key(hash_key)
        self._validate_chunk_size(chunk_size)
        self._validate_timeout(timeout)
        self._validate_block_size(block_size)

    def _validate_block_size(self, block_size: int) -> None:
        min_block_size = 4 * 1024
        max_block_size = 2**16  # 64k

        if block_size < min_block_size or block_size > 2**16:
            block_size = max_block_size

        self.block_size = block_size

    def _validate_hash_key(self, hash_key: str) -> None:
        known_sha_list = [
            "sha1",
            "sha256",
        ]

        if hash_key not in known_sha_list:
            msg = f"The hash key you provided is not supported; it must be one of {known_sha_list}"
            logger.exception(msg)
            raise UrlDownloaderUnknownHashKey(msg)

        self.hash_key = hash_key

    def _validate_timeout(self, timeout: int) -> None:
        min_timeout = 10
        max_timeout = 3600

        timeout = max(timeout, min_timeout)
        timeout = min(max_timeout, timeout)

        self.timeout = timeout
        logger.info("set HTTP request timeout to: %s seconds", timeout)

    def _validate_chunk_size(self, chunk_size: int) -> None:
        min_chunk = 4 * 1024  # 4k
        max_chunk = 64 * 1024  # 64k

        chunk_size = min(max_chunk, chunk_size)
        chunk_size = max(chunk_size, min_chunk)

        self.chunk_size = chunk_size
        logger.info("set chunk size to: %s bytes", chunk_size)

    def _validate_target_dir(self, target_dir: str) -> None:
        target_dir_posix = self._simple_path_to_posix(target_dir)
        exists, what = self._exists_path(
            item_path=target_dir_posix,
        )
        if exists is False:
            msg = f"the specified target path does not exist; {target_dir_posix}"
            logger.exception(msg)
            raise UrlDownloaderTargetDirectoryIssue(msg)

        if what != "D":
            msg = f"the specified target path exists but is not a directory; {target_dir_posix}"
            logger.exception(msg)
            raise UrlDownloaderTargetDirectoryIssue(msg)

        self.target_dir_posix = target_dir_posix
        logger.info("set target path to: %s", self.target_dir_posix)

    def _get_hex_digest(
        self,
        *,
        file_path: str,
    ) -> str | None:
        assert self.hash_key in ["sha1", "sha256"]

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
            logger.error(msg)
            raise UrlDownloaderFileVerifyIssue(msg) from e

    @staticmethod
    def _exists_path(
        *,
        item_path: str,
    ) -> Tuple[bool, str]:
        fp = Path(item_path)
        exists = fp.exists()
        what = ""
        if exists:
            if fp.is_dir():
                what = "D"
            elif fp.is_file():
                what = "F"

        return fp.exists(), what

    def _make_temp_file_name_and_check_exists(
        self,
        *,
        url: str,
        dir_path: str,
    ) -> Tuple[str, bool]:
        uuid_name = uuid.uuid5(
            uuid.NAMESPACE_URL,
            url,
        )
        tmp_name = f".{uuid_name}.tmp"
        file_path = f"{dir_path}/{tmp_name}"
        exists, _ = self._exists_path(
            item_path=file_path
        )  # we are not interested in 'file' or 'dir' as we expect it not to exist

        return file_path, exists

    def _verify_existing_file(
        self,
        *,
        file_path: str,
        hashes: Dict[str, str],
    ) -> None:
        """
        Args:
         - file_path: str,
         - hashes: Dict[str, str],

        Return:
           None if successful.

        Raises:
         - UrlDownloaderUnknownHashKey: if we cannot find the proper key we support
         - UrlDownloaderFileVerifyIssue: if the verification fails
        """

        digest = hashes.get(self.hash_key)
        if digest is None:
            msg = f"no digest found for '{self.hash_key}' in: {hashes}"
            logger.exception(msg)
            raise UrlDownloaderUnknownHashKey(message=msg)

        my_hex_digest = self._get_hex_digest(file_path=file_path)

        if digest != my_hex_digest:
            msg = f"verify of '{file_path}' fails, expected: '{self.hash_key}:{digest}' but got: '{my_hex_digest}'"
            logger.error(msg)
            raise UrlDownloaderFileVerifyIssue(msg)

        logger.info("verify of '%s' ok: '%s:%s'", file_path, self.hash_key, digest)

    @staticmethod
    def _remove_temp_file_if_exists(file_path: str) -> None:
        fp = Path(file_path)
        fp.unlink(missing_ok=True)  # UNLINK THE temp file
        logger.info("temp file removed: %s", file_path)

    def _download_with_optional_verify(  # pylint: disable=too-many-arguments
        self,
        *,
        download_url: str,
        file_path: str,
        hashes: Dict[str, str],
    ) -> None:
        """
        Args:
         - download_url: str;    The actual URL from which the file will be downloaded. Valid for a short interval only
         - file_path: str;       The target file path
         - hashes: Dict[str, str]; The current dict of hashes (sha1 and sha256 are supported for verification)

        Return:
            None if successful.

        Raises:
            Whatever the GET request raises on HTTPS errors

        Notes:
        """
        try:
            logger.debug("%s %s", download_url, file_path)

            response = requests.get(
                download_url,
                stream=True,
                timeout=self.timeout,
            )
            with open(file_path, mode="wb") as file:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    file.write(chunk)
                logger.info("file downloaded: %s, size: %d", file_path, file.tell())

        except Exception as e:  # pylint:disable=broad-exception-caught
            msg = f"cannot download to {file_path}; {e}"
            logger.exception(msg)
            self._remove_temp_file_if_exists(file_path)
            raise e

        if self.with_verify_after_download is True:
            self._verify_existing_file(  # raises error on verify fail
                file_path=file_path,
                hashes=hashes,
            )

    def _check_target_path(
        self,
        *,
        target_file_name: str,
        hashes: Dict[str, str],
    ) -> Tuple[bool, str]:
        """

        Args:
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
        exists, _ = self._exists_path(item_path=target_file_path)
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
        """
        After verification, we must rename the temp file.

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
            fp = Path(file_path)
            fp.rename(target_path)
            # On Unix, if target exists and is a file, it will be replaced silently if the user has permission.
            # On Windows, if target exists, FileExistsError will be raised.
            logger.info("rename ok: %s -> %s", file_path, target_path)
            return

        except FileExistsError as e:
            logger.exception("Cannot rename file %s to %s; %s", file_path, target_path, e)
            self._remove_temp_file_if_exists(file_path)
            raise e

        except Exception as e:
            logger.exception("Cannot rename file %s to %s; %s", file_path, target_path, e)
            self._remove_temp_file_if_exists(file_path)
            raise e

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

    def _check_temp_path(
        self,
        *,
        temp_dir: str,
        download_url: str,
    ) -> str:
        """
        Args:
         - temp_dir: str; The location of the temp directory (must exist)
         - download_url: str; The URL we use to get the file name

        Returns:
            temp_file_path if we reach the end

        Raises:
         - UrlDownloaderTempFileIssue: if the temp file exists

        """
        temp_file_path, exists = self._make_temp_file_name_and_check_exists(
            url=download_url,
            dir_path=temp_dir,
        )
        if exists:
            msg = f"temp file exists; {temp_file_path}"
            logger.exception(msg)
            raise UrlDownloaderTempFileIssue(msg)

        return temp_file_path

    def _validate_hashes(self, hashes: Dict[str, str]) -> None:
        if len(hashes) == 0:
            return

        if self.hash_key not in hashes:
            msg = "the hash key {hash_key} is not present in the hashes dict {hashes}"
            logger.exception(msg)
            raise UrlDownloaderUnknownHashKey(msg)

    def _get_target_file_name(self, download_url: str) -> str:
        target_file_name = self._extract_target_file_name(
            download_url=download_url,
        )

        if target_file_name is None:
            msg = f"the target file name cannot be extracted from the download URL; {download_url}"
            logger.exception(msg)
            raise UrlDownloaderTargetFileIssue(msg)

        target_file_name_posix = self._simple_path_to_posix(target_file_name)
        if "/" in target_file_name_posix:
            target_file_name_posix = os.path.basename(target_file_name_posix)

        return target_file_name_posix

    @staticmethod
    def _simple_path_to_posix(target_path: str) -> str:
        """return a path with more POSIX-like separators, path does not need to exist"""
        return target_path.replace("\\", "/")

    # PUBLIC

    def download_file_from_url(
        self,
        *,
        download_url: str,
        hashes: Dict[str, str],
    ) -> Tuple[bool, str]:
        """
        Action:
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
            If there are problems with the temp file.
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
