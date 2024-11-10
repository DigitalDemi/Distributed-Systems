from enum import Enum


class ItemType(Enum):
    FLOWER = "flower"
    SUGAR = "sugar"
    POTATO = "potato"
    OIL = "oil"

    @classmethod
    def from_string(cls, value: str) -> "ItemType":
        """Convert string to ItemType, case-insensitive really annoying bug"""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid item type: {value}. Valid types are: {', '.join([t.value for t in cls])}"
            )
