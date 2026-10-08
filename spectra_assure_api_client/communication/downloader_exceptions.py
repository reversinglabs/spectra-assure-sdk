from .exceptions import SpectraAssureExceptions


class UrlDownloaderExceptions(SpectraAssureExceptions):
    """The base of the UrlDownloader exceptions.

    It derives from SpectraAssureExceptions, so `except SpectraAssureExceptions`
    catches every exception the SDK raises. Before, the two families had
    separate roots and a caller had to catch both.
    """

    def __init__(self, message: str = ""):
        super().__init__(message)


class UrlDownloaderUnknownHashKey(UrlDownloaderExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The hash key you provided is not supported"):
        super().__init__(message)


class UrlDownloaderTargetDirectoryIssue(UrlDownloaderExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The target directory has a serious issue"):
        super().__init__(message)


class UrlDownloaderTargetFileIssue(UrlDownloaderExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The target file has a serious issue"):
        super().__init__(message)


class UrlDownloaderTempFileIssue(UrlDownloaderExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The target temp_file has a serious issue"):
        super().__init__(message)


class UrlDownloaderFileVerifyIssue(UrlDownloaderExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The file does not verify with the given hash"):
        super().__init__(message)
