from .constants import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    DEFAULT_TIMEOUT,
    FALLBACK_THROTTLE_DELAY,
    MAX_DATE_THROTTLE_DELAY,
    MAX_THROTTLE_ATTEMPTS,
)

# The defaults callers may want to read: the three timeouts and the throttle
# settings. Each name once, and only names imported above (I-26).
__all__ = [
    "DEFAULT_CONNECT_TIMEOUT",
    "DEFAULT_READ_TIMEOUT",
    "DEFAULT_TIMEOUT",
    "FALLBACK_THROTTLE_DELAY",
    "MAX_DATE_THROTTLE_DELAY",
    "MAX_THROTTLE_ATTEMPTS",
]
