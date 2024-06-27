class SpectraAssureExceptions(Exception):
    """A communication class for Spectra Assure exceptions."""

    def __init__(self, message: str = ""):
        super().__init__(message)


class SpectraAssureInvalidAction(SpectraAssureExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "This action is not allowed"):
        super().__init__(message)


class SpectraAssureInvalidPath(SpectraAssureExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The path you specified is invalid"):
        super().__init__(message)


class SpectraAssureUnexpectedNoDataFound(SpectraAssureExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "Received no data where we expected some"):
        super().__init__(message)


class SpectraAssureNoDownloadUrlInResult(SpectraAssureExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "The query returns no download URL"):
        super().__init__(message)


class SpectraAssureUnsupportedStrategy(SpectraAssureExceptions):
    """A custom exception class for Spectra Assure Api."""

    def __init__(self, message: str = "Attempted strategy is not supported"):
        super().__init__(message)
