
from typing import Any, Callable

from django.db.models import Q
from django.forms.widgets import TextInput, Widget

from bloomerp.models.application_field import ApplicationField
from bloomerp.utils.registry import BaseRegistry
from dataclasses import dataclass


def default_q_factory(
    application_field:ApplicationField,
    expression:str,
    value:Any
) -> Q:
    try:
        value = application_field._get_model_field().to_python(value)
    except:
        pass
    
    return Q(**{expression:value})
    

@dataclass
class LookupDefinition:
    id:str|tuple[str]
    label:str
    q_factory:Callable[[ApplicationField, str, Any], Q] = default_q_factory
    widget_factory:Callable[[ApplicationField], Widget] = lambda x: TextInput()
    nested:bool = False
    
            

class LookupRegistry(BaseRegistry[LookupDefinition]):
    """
    The thing that needs to be validated on the field side is that no field can have 
    lookups with the same ID.
    """
    def get_lookup_by_id(self, id:str, field:ApplicationField) -> LookupDefinition | None:
        lookups = field.get_lookups()
        
        nested_lookup = None
        for lookup in lookups:
            if (id == lookup.id if isinstance(id, str) else id in lookup.id):
                return lookup
            if lookup.nested:
                nested_lookup = nested_lookup
        
        # If it's not in the ID, than we assume a nested lookup
        # A field can only have one nested lookup
        return nested_lookup or None
        


LOOKUP_REGISTRY = LookupRegistry(LookupDefinition)

LOOKUP_REGISTRY.register(
    "EQUALS",
    LookupDefinition(
        id=("equals", "", "eq"),
        label="Equals",
        q_factory=lambda field, value: Q(**{field:value}),
    )
)

LOOKUP_REGISTRY.register(
    "GREATER_OR_EQUAL_THEN",
    LookupDefinition(
        id="gte",
        label="Greater or equal",
        q_factory=lambda field, value: Q(**{field+"__gte":value})
    )
)

LOOKUP_REGISTRY.register(
    "JSON_EQUALS",
    LookupDefinition(
        id="",
        label="Equals",
        q_factory=lambda _, expression, value: Q(**{expression:value}),
        nested=True
    )
)


def foreign_advanced_lookup(af:ApplicationField, expr:str, value:Any):
    expr.split("__")[-1]

LOOKUP_REGISTRY.register(
    "FOREIGN_ADVANCED",
    LookupDefinition(
        id="",
        label="Equals (Advanced)",
        q_factory=foreign_advanced_lookup
    )
)
