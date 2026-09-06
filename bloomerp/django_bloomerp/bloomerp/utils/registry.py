from typing import Generic, TypeVar

RegistryItem = TypeVar("RegistryItem")

# Note: adding dataview re
class BaseRegistry(Generic[RegistryItem]):
    _id_field: str = "key"
    
    def __init__(self, registry_item_class: type[RegistryItem]) -> None:
        self.registry_item_class = registry_item_class
        self._registry: dict[str, RegistryItem] = {}
    
    def register(self, key: str, obj: RegistryItem) -> None:
        """_summary_

        Args:
            key (str): _description_
            obj (RegistryItem): _description_
        """
        if not isinstance(obj, self.registry_item_class):
            raise TypeError(f"Object must be an instance of {self.registry_item_class.__name__}")
        
        if key in self._registry:
            raise ValueError("Already registered")
    
        self._registry[key] = obj

    def unregister(self, key: str) -> RegistryItem:
        try:
            return self._registry.pop(key)
        except KeyError as error:
            raise KeyError(f"No item registered with key {key!r}") from error

    def get(self, key: str) -> RegistryItem | None:
        return self._registry.get(key)

    def __getattr__(self, key: str) -> RegistryItem:
        """Allows you to access registry items as attributes by their key."""
        try:
            return self._registry[key]
        except KeyError as error:
            raise AttributeError(f"{type(self).__name__!s} has no attribute {key!r}") from error
    
    def values(self) -> list[RegistryItem]:
        return list(self._registry.values())

    def items(self) -> list[tuple[str, RegistryItem]]:
        return list(self._registry.items())
    
