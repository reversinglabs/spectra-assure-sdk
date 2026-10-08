DEFAULT_TIMEOUT: int = 60 * 60
DEFAULT_READ_TIMEOUT = DEFAULT_TIMEOUT

# How long to wait for the TCP/TLS connection to be established, as opposed to
# waiting for the response. `timeout` alone covered both, so an unroutable or
# dead host took the full read timeout -- an hour by default -- to fail.
DEFAULT_CONNECT_TIMEOUT: int = 10

# Attempts, not retries: one initial try plus four more.
MAX_THROTTLE_ATTEMPTS: int = 5

# Used when the Portal signals a throttle but we cannot work out for how long.
FALLBACK_THROTTLE_DELAY: int = 60

# Ceiling on a wait derived from a `Retry-After` date, so that a clock skew
# between this machine and the Portal cannot turn into an arbitrarily long sleep.
MAX_DATE_THROTTLE_DELAY: int = 15 * 60

# Retry on 429 is opt-in, as it has always been. Turning it on by default would
# change behaviour for everyone who already handles 429 themselves: a call that
# returned immediately would start blocking for minutes first.
DEFAULT_AUTO_ADAPT_TO_THROTTLE: bool = False

HTTP_TOO_MANY_REQUESTS: int = 429

DEFAULT_CHUNK_SIZE: int = 16 * 1024
DEFAULT_BLOCK_SIZE: int = 2**16
