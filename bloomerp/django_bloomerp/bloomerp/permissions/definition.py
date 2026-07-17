from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class PermissionMatch(Enum):
    """
    Enum representing the type of match for a permission.
    """
    ALL = "all"
    ANY = "any"


class PermissionScope(Enum):
    """
    Enum representing the scope of a permission.
    """
    GLOBAL = "global"
    FIELD = "field"
    ROW = "row"


@dataclass
class BloomerpPermissionDefinition:
    """
    A class to define a permission in the Bloomerp system.
    """
    name: str
    codename: str
    description: str
    scopes : list[PermissionScope] = None
    
    
class BloomerpPermission(Enum):
    """
    Enum representing the permissions in the Bloomerp system.
    Each permission is defined with a name, codename, description, and scopes.
    """
    ADD = BloomerpPermissionDefinition(
        name="Add",
        codename="add",
        description="Permission to add new records.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.FIELD, PermissionScope.ROW]
    )
    CHANGE = BloomerpPermissionDefinition(
        name="Change",
        codename="change",
        description="Permission to change existing records.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.FIELD, PermissionScope.ROW]
    )
    DELETE = BloomerpPermissionDefinition(
        name="Delete",
        codename="delete",
        description="Permission to delete records.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.ROW]
    )
    VIEW = BloomerpPermissionDefinition(
        name="View",
        codename="view",
        description="Permission to view records.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.FIELD, PermissionScope.ROW]
    )
    EXPORT = BloomerpPermissionDefinition(
        name="Export",
        codename="export",
        description="Permission to export records.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.FIELD, PermissionScope.ROW]
    )
    IMPORT = BloomerpPermissionDefinition(
        name="Import",
        codename="import",
        description="Permission to import records.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.FIELD, PermissionScope.ROW]
    )
    BULK_CHANGE = BloomerpPermissionDefinition(
        name="Bulk Change",
        codename="bulk_change",
        description="Permission to change multiple records at once.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.FIELD, PermissionScope.ROW]
    )
    BULK_DELETE = BloomerpPermissionDefinition(
        name="Bulk Delete",
        codename="bulk_delete",
        description="Permission to delete multiple records at once.",
        scopes=[PermissionScope.GLOBAL, PermissionScope.ROW]
    )
    
    @classmethod
    def to_tuple(cls) -> tuple[str, ...]:
        """
        Returns a tuple of all permission codenames.
        """
        return tuple(permission.value.codename for permission in cls)


class RowPolicyRuleCondition(BaseModel):
    application_field_id: Optional[int | str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    field: Optional[str] = None

    @model_validator(mode="after")
    def validate_condition_shape(self):
        if self.field == "__all__" or self.application_field_id == "__all__":
            return self

        if self.application_field_id in (None, "") and self.field in (None, ""):
            raise ValueError("Missing application field id or field name in rule")
        if self.operator in (None, ""):
            raise ValueError("Missing operator")
        if self.value is None or self.value == "":
            raise ValueError("No value given")

        return self


class RowPolicyRuleContent(BaseModel):
    connector: Literal["AND", "OR"]
    conditions: list[RowPolicyRuleCondition]

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, conditions):
        if not conditions:
            raise ValueError("At least one condition is required")
        return conditions
    

class AccessRule(BaseModel):
    row_permissions: list[RowPolicyRuleContent] = Field(default_factory=list)
    field_permissions: dict[str, list[BloomerpPermission | str]] = Field(default_factory=dict)
    
    
