from enum import Enum

class BaseEnumDefinitionRegistry(Enum):
    _id_field : str = "key"
    _model = None
    
    
    