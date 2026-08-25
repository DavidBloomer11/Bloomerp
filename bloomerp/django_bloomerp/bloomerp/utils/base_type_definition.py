from enum import Enum

class BaseTypeDefinition(Enum):
    @classmethod
    def from_key(cls, key: str | None) -> "BaseTypeDefinition | None":
        if not key:
            return None

        normalized_key = key.strip().lower()
        if not normalized_key:
            return None

        for item in cls:
            if item.value.key == normalized_key:
                return item
        return None

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [
            (item.value.key, item.value.name)
            for item in cls
        ]

    @classmethod
    def keys(cls) -> list[str]:
        return [
            item.value.key
            for item in cls
        ]