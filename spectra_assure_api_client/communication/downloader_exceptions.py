class UrlDownloaderExceptions(Exception):
    """A communication class for Spectra Assure exceptions."""

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

    def __init__(self, message: str = "The target directory has a serious issue"):
        super().__init__(message)


class UrlDownloaderFileVerifyIssue(UrlDownloaderExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The file does not verify with the given hash"):
        super().__init__(message)
