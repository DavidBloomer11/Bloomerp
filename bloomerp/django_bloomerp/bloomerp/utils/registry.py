from typing import Generic, TypeVar

from numpy import isin

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

    def get(self, key: str) -> RegistryItem | None:
        return self._registry.get(key)
    
    def values(self) -> list[RegistryItem]:
        return list(self._registry.values())
    
    