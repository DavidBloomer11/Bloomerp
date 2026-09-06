"""Explicit registration of built-in field types.

Application consumers can import FIELD_TYPE_REGISTRY from bloomerp.field_types
for the populated global registry. Code importing the raw registry module must
call load_builtin_field_types() explicitly.
"""


def register_builtin_field_types(registry):
    from . import text, numeric, boolean, temporal, relations, other

    for module in (text, numeric, boolean, temporal, relations, other):
        module.register(registry)
