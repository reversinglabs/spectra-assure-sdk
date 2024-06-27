# python3

from typing import (
    Any,
)


def standardReturn(action: str, data: Any) -> bool:
    if data.status_code < 200 or data.status_code >= 300:
        print(action, data.status_code, data.text)
        return False

    print(action, data.text)
    return True
