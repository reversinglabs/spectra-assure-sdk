class SpectraAssureExceptions(Exception):
    """A base class for Spectra Assure exceptions."""

    def __init__(self, message: str = ""):
        super().__init__(message)


class InvalidAction(SpectraAssureExceptions):
    """A custom exception class for MyProject."""

    def __init__(self, message: str = "This action is not allowed"):
        super().__init__(message)
