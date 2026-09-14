import hashlib
import hmac
from typing import Any

SECRET = b"secret-key"

SENSITIVE_FIELDS = {
    "password",
    "confirm_password",
}


def mask(value: str) -> str:
    return hmac.new(
        SECRET,
        value.encode(),
        hashlib.sha256,
    ).hexdigest()


def mask_sensitive(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            key: (
                mask(value)
                if key in SENSITIVE_FIELDS and isinstance(value, str)
                else mask_sensitive(value)
            )
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [mask_sensitive(item) for item in data]

    return data
