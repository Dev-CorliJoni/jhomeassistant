from re import match

from simplehomeassistant.types.units.base import BaseUnit


class MonetaryUnit(BaseUnit):
    """Holds an ISO 4217 currency code like 'EUR' or 'USD'."""
    __slots__ = ("VALUE",)

    def __init__(self, code: str):
        # Example: "EUR", "USD", "JPY"
        super().__init__()
        if code is None or not match(r"^[A-Z]{3}$", code):
            raise ValueError(
                f"Invalid unit '{code}' for device_class 'monetary'. "
                f"Allowed: 3-letter ISO 4217 currency code. See https://en.wikipedia.org/wiki/ISO_4217#Active_codes"
            )
        self.VALUE = code

    def __str__(self) -> str:
        return self.VALUE

    def __repr__(self) -> str:
        return f"MonetaryUnit(VALUE={self.VALUE!r})"
