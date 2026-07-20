"""Compatibility façade for the backend-specific permission compilers."""

from bloomerp.permissions.compilers.django_q_permission_compiler import (
    CompiledDjangoAccess,
    DjangoQPermissionCompiler,
)
from bloomerp.permissions.compilers.python_permission_compiler import (
    CompiledPythonAccess,
    PythonPermissionCompiler,
)
from bloomerp.permissions.compilers.sql_permission_compiler import (
    CompiledSqlAccess,
    SqlPermissionCompiler,
    get_physical_tables,
    get_table_names,
    get_table_references,
)
from bloomerp.permissions.definition import BloomerpPermission, PermissionMatch


class PermissionCompiler:
    """Deprecated façade retained while callers migrate to concrete compilers."""

    @classmethod
    def compile_to_django(
        cls,
        rules,
        permissions,
        match: PermissionMatch = PermissionMatch.ANY,
        *,
        user=None,
    ) -> CompiledDjangoAccess:
        return DjangoQPermissionCompiler(rules, user=user).compile(permissions, match)

    @classmethod
    def compile_to_python(
        cls,
        rules,
        permissions,
        match: PermissionMatch = PermissionMatch.ANY,
        *,
        user=None,
    ) -> CompiledPythonAccess:
        return PythonPermissionCompiler(rules, user=user).compile(permissions, match)

    @classmethod
    def compile_to_sql(
        cls,
        query,
        rules,
        permissions=BloomerpPermission.VIEW,
        match: PermissionMatch = PermissionMatch.ANY,
        *,
        user=None,
        dialect=None,
    ) -> CompiledSqlAccess:
        return SqlPermissionCompiler(rules, user=user).compile(
            query,
            permissions,
            match,
            dialect=dialect,
        )


__all__ = [
    "CompiledDjangoAccess",
    "CompiledPythonAccess",
    "CompiledSqlAccess",
    "DjangoQPermissionCompiler",
    "PermissionCompiler",
    "PythonPermissionCompiler",
    "SqlPermissionCompiler",
    "get_physical_tables",
    "get_table_names",
    "get_table_references",
]
