import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from django.db import connection
from django.db.models import Model, Q

from bloomerp.field_types.lookups import Lookup
from bloomerp.models.application_field import ApplicationField
from bloomerp.permissions.definition import (
    AccessRule,
    BloomerpPermission,
    PermissionMatch,
    RowPolicyRuleCondition,
    RowPolicyRuleContent,
)
from sqlglot import exp, parse, parse_one
from sqlglot.optimizer.scope import traverse_scope

BOOLEAN_NORMALIZATION = {
    "true": True,
    "1": True,
    "yes": True,
    "on": True,
    "false": False,
    "0": False,
    "no": False,
    "off": False,
}


def resolve_lookup(
    application_field: ApplicationField,
    operator: str,
) -> Lookup | None:
    """Resolve an operator by lookup id, Django name, or configured alias."""
    if not application_field or not operator:
        return None

    field_type = application_field.get_field_type_enum()
    lookup = field_type.get_lookup_by_id(operator)
    if lookup is not None:
        return lookup

    for candidate in field_type.lookups:
        definition = candidate.value
        if operator == definition.django_representation:
            return candidate
        if operator in (definition.aliases or []):
            return candidate
    return None


def normalize_lookup_value(
    application_field: ApplicationField,
    lookup: Lookup | str | None,
    value: Any,
) -> Any:
    """Normalize values that Django lookups cannot consume as form strings."""
    lookup_name = (
        lookup.value.django_representation
        if isinstance(lookup, Lookup)
        else str(lookup or "")
    ).lower()

    if lookup_name == "in":
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, (tuple, set)):
            return list(value)

    if lookup_name == "isnull":
        if isinstance(value, str):
            return BOOLEAN_NORMALIZATION.get(value.strip().lower(), False)
        return bool(value)

    if application_field.field_type in {"BooleanField", "NullBooleanField"}:
        if isinstance(value, str):
            return BOOLEAN_NORMALIZATION.get(value.strip().lower(), False)
        return bool(value)

    return value


def _permission_codename(permission: str | BloomerpPermission) -> str:
    if isinstance(permission, BloomerpPermission):
        return permission.value.codename
    value = str(permission).strip()
    return value.rsplit(".", 1)[-1]


def _permission_matches(
    granted: str | BloomerpPermission,
    requested: str | BloomerpPermission,
) -> bool:
    granted_codename = _permission_codename(granted)
    requested_codename = _permission_codename(requested)
    if granted_codename == requested_codename:
        return True

    # AccessRule instances created directly may use action names while rules
    # loaded from Django use model-qualified codenames (for example, view vs
    # view_customer).
    return (
        granted_codename.startswith(f"{requested_codename}_")
        or requested_codename.startswith(f"{granted_codename}_")
    )


def _matches_requested_permissions(
    granted: list[str | BloomerpPermission],
    requested: list[str | BloomerpPermission],
    match: PermissionMatch,
) -> bool:
    if not requested:
        return bool(granted)

    matches = [
        any(_permission_matches(grant, permission) for grant in granted)
        for permission in requested
    ]
    return all(matches) if match == PermissionMatch.ALL else any(matches)


def get_table_names(sql: str, dialect: str = "postgres") -> set[str]:
    """Returns the table names of a particular query

    Args:
        sql (str): _description_
        dialect (str, optional): _description_. Defaults to "postgres".

    Returns:
        set[str]: _description_
    """
    tree = parse_one(sql, read=dialect)

    return {
        table.name
        for table in tree.find_all(exp.Table)
    }


def get_physical_tables(
    sql: str,
    dialect: str = "postgres",
) -> list[exp.Table]:
    tree = parse_one(sql, read=dialect)
    tables: list[exp.Table] = []

    for scope in traverse_scope(tree):
        for table in scope.tables:
            if (
                isinstance(table, exp.Table)
                and table.name
                and table.name not in scope.cte_sources
            ):
                tables.append(table)

    return tables


def get_table_references(
    sql: str,
    dialect: str = "postgres",
) -> list[dict[str, str]]:
    references = []

    for table in get_physical_tables(sql, dialect):
        references.append(
            {
                "catalog": table.catalog,
                "schema": table.db,
                "table": table.name,
                "alias": table.alias or table.name,
            }
        )

    return references


@dataclass(frozen=True)
class CompiledDjangoAccess:
    row_filter: Q
    field_filters: dict[Q, list[ApplicationField]]


@dataclass(frozen=True)
class CompiledSqlAccess:
    query: str
    params: tuple[Any, ...] = ()
    denied: bool = False


class PermissionCompiler:
    """Compile normalized access rules for supported query backends."""

    @classmethod
    def compile_q_for_condition(
        cls,
        rule_condition: RowPolicyRuleCondition | dict,
        *,
        user=None,
        application_fields: dict[str, ApplicationField] | None = None,
    ) -> Q | None:
        """Compile one row-policy condition, failing closed when invalid."""
        if isinstance(rule_condition, dict):
            try:
                rule_condition = RowPolicyRuleCondition.model_validate(rule_condition)
            except Exception:
                return None
        if not isinstance(rule_condition, RowPolicyRuleCondition):
            return None

        application_field_id = rule_condition.application_field_id
        operator = str(rule_condition.operator or "")
        value = rule_condition.value
        field_path = rule_condition.field

        if field_path == "__all__" or application_field_id == "__all__":
            # Q() is a neutral element when OR-combined with another Q, not a
            # durable tautology. A non-null primary key is true for every
            # persisted Django row and composes correctly.
            return Q(pk__isnull=False)
        if not application_field_id or not operator:
            return None

        if application_fields is None:
            try:
                application_field = ApplicationField.objects.get(pk=application_field_id)
            except (ApplicationField.DoesNotExist, TypeError, ValueError):
                return None
        else:
            application_field = application_fields.get(str(application_field_id))
            if application_field is None:
                return None

        field_name = application_field.field
        if isinstance(field_path, str) and "__" in field_path:
            field_name = field_path

        if operator.startswith("__"):
            filter_key = operator.lstrip("_")
            lookup_name = filter_key.rsplit("__", 1)[-1]
            normalized_value = normalize_lookup_value(
                application_field,
                lookup_name,
                value,
            )
            return Q(**{filter_key: normalized_value})

        lookup = resolve_lookup(application_field, operator)
        if lookup is None:
            return None

        if lookup == Lookup.EQUALS_USER or str(value) == "$user":
            if user is None or getattr(user, "is_anonymous", False):
                return None
            return Q(**{field_name: user})

        normalized_value = normalize_lookup_value(application_field, lookup, value)
        if lookup == Lookup.NOT_EQUALS:
            return ~Q(**{field_name: normalized_value})

        django_lookup = (lookup.value.django_representation or "").strip()
        filter_key = f"{field_name}__{django_lookup}" if django_lookup else field_name
        return Q(**{filter_key: normalized_value})

    @classmethod
    def compile_q_for_row_rule(
        cls,
        row_rule: RowPolicyRuleContent | dict,
        *,
        user=None,
        application_fields: dict[str, ApplicationField] | None = None,
    ) -> Q | None:
        """Compile one stored row rule and its internal connector."""
        if isinstance(row_rule, dict):
            try:
                row_rule = RowPolicyRuleContent.model_validate(row_rule)
            except Exception:
                return None
        if not isinstance(row_rule, RowPolicyRuleContent) or not row_rule.conditions:
            return None

        condition_filters: list[Q] = []
        for condition in row_rule.conditions:
            condition_filter = cls.compile_q_for_condition(
                condition,
                user=user,
                application_fields=application_fields,
            )
            # Ignoring one invalid condition could broaden an allow rule, so
            # the complete row rule must fail closed.
            if condition_filter is None:
                return None
            condition_filters.append(condition_filter)

        combined_filter = condition_filters[0]
        for condition_filter in condition_filters[1:]:
            if row_rule.connector == "OR":
                combined_filter |= condition_filter
            else:
                combined_filter &= condition_filter
        return combined_filter

    @classmethod
    def compile_to_django(
        cls,
        rules: list[AccessRule],
        permissions: list[str | BloomerpPermission] | str | BloomerpPermission,
        match: PermissionMatch = PermissionMatch.ANY,
        *,
        user=None,
    ) -> CompiledDjangoAccess:
        """Compile access rules into row and row-dependent field filters."""
        if isinstance(permissions, (str, BloomerpPermission)):
            requested_permissions = [permissions]
        else:
            requested_permissions = list(permissions or [])
        
        normalized_rules: list[AccessRule] = []
        for rule in rules or []:
            if not isinstance(rule, AccessRule):
                try:
                    rule = AccessRule.model_validate(rule)
                except Exception:
                    continue
            normalized_rules.append(rule)

        referenced_field_ids: set[str] = set()
        for rule in normalized_rules:
            referenced_field_ids.update(
                str(field_id)
                for field_id in rule.field_permissions
                if field_id != "__all__"
            )
            for row_rule in rule.row_permissions:
                referenced_field_ids.update(
                    str(condition.application_field_id)
                    for condition in row_rule.conditions
                    if condition.application_field_id not in (None, "", "__all__")
                )

        valid_field_ids = []
        for field_id in referenced_field_ids:
            try:
                valid_field_ids.append(ApplicationField._meta.pk.to_python(field_id))
            except (TypeError, ValueError):
                continue

        application_fields = {
            str(field.pk): field
            for field in ApplicationField.objects.filter(pk__in=valid_field_ids)
        }
        row_filters: list[Q] = []
        field_filters: dict[Q, list[ApplicationField]] = {}

        for rule in normalized_rules:
            rule_row_filters: list[Q] = []
            for row_rule in rule.row_permissions or []:
                row_filter = cls.compile_q_for_row_rule(
                    row_rule,
                    user=user,
                    application_fields=application_fields,
                )
                if row_filter is not None:
                    rule_row_filters.append(row_filter)

            if not rule_row_filters:
                continue

            rule_filter = rule_row_filters[0]
            for row_filter in rule_row_filters[1:]:
                rule_filter |= row_filter
            row_filters.append(rule_filter)

            accessible_fields: list[ApplicationField] = []
            seen_field_ids: set[int] = set()
            for field_id, granted_permissions in (rule.field_permissions or {}).items():
                if not _matches_requested_permissions(
                    list(granted_permissions or []),
                    requested_permissions,
                    match,
                ):
                    continue
                if field_id == "__all__":
                    # Policy.to_access_rule expands wildcards. A raw compiler
                    # input has no model/content-type context with which to do so.
                    continue
                application_field = application_fields.get(str(field_id))
                if application_field and application_field.pk not in seen_field_ids:
                    accessible_fields.append(application_field)
                    seen_field_ids.add(application_field.pk)

            existing_fields = field_filters.setdefault(rule_filter, [])
            existing_ids = {field.pk for field in existing_fields}
            existing_fields.extend(
                field for field in accessible_fields if field.pk not in existing_ids
            )

        if not row_filters:
            return CompiledDjangoAccess(
                row_filter=Q(pk__in=[]),
                field_filters={},
            )

        combined_filter = row_filters[0]
        for row_filter in row_filters[1:]:
            combined_filter |= row_filter

        return CompiledDjangoAccess(
            row_filter=combined_filter,
            field_filters=field_filters,
        )

    @classmethod
    def compile_to_sql(
        cls,
        query: str,
        rules: dict[type[Model], list[AccessRule]],
        permissions: list[str | BloomerpPermission] | str | BloomerpPermission = BloomerpPermission.VIEW,
        match: PermissionMatch = PermissionMatch.ANY,
        *,
        user=None,
        dialect: str | None = None,
    ) -> CompiledSqlAccess:
        """Apply row and field policies before user-authored SQL expressions."""
        dialect = dialect or cls._connection_dialect()
        tree = cls._parse_single_read_query(query, dialect)
        physical_tables = cls._physical_tables_from_tree(tree)

        models_by_table: dict[str, type[Model]] = {}
        for model in rules:
            table_name = model._meta.db_table
            if table_name in models_by_table and models_by_table[table_name] is not model:
                raise PermissionError(f"Ambiguous model mapping for table: {table_name}")
            models_by_table[table_name] = model

        for table in physical_tables:
            if table.catalog or table.db:
                raise PermissionError(
                    f"Qualified table names are not allowed: {table.sql(dialect=dialect)}"
                )
            if table.name not in models_by_table:
                raise PermissionError(f"You do not have access to table: {table.name}")

        marker_prefix = f"__bloomerp_policy_param_{uuid4().hex}_"
        marker_values: dict[int, Any] = {}

        for occurrence, table in enumerate(physical_tables):
            model = models_by_table[table.name]
            compiled_access = cls.compile_to_django(
                rules=rules[model],
                permissions=permissions,
                match=match,
                user=user,
            )
            table.replace(
                cls._secure_table_expression(
                    model=model,
                    original_table=table,
                    compiled_access=compiled_access,
                    marker_prefix=marker_prefix,
                    marker_values=marker_values,
                    occurrence=occurrence,
                )
            )

        compiled_query = tree.sql(dialect=dialect)
        marker_pattern = re.compile(rf"{re.escape(marker_prefix)}(\d+)__")
        ordered_params: list[Any] = []

        def replace_marker(match_object: re.Match) -> str:
            marker_index = int(match_object.group(1))
            ordered_params.append(marker_values[marker_index])
            return "%s"
        
        compiled_query = marker_pattern.sub(replace_marker, compiled_query)
        if len(ordered_params) != len(marker_values):
            raise ValueError("Could not preserve all SQL policy parameters")

        return CompiledSqlAccess(
            query=compiled_query,
            params=tuple(ordered_params),
        )

    @staticmethod
    def _connection_dialect() -> str:
        dialects = {
            "postgresql": "postgres",
            "sqlite": "sqlite",
        }
        try:
            return dialects[connection.vendor]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported SQL permission dialect: {connection.vendor}"
            ) from exc

    @staticmethod
    def _parse_single_read_query(query: str, dialect: str) -> exp.Query:
        statements = [
            statement
            for statement in parse(query, read=dialect)
            if statement is not None
        ]
        if len(statements) != 1:
            raise ValueError("Exactly one SQL statement is required")

        statement = statements[0]
        if not isinstance(statement, exp.Query) or statement.find(exp.Into):
            raise ValueError("Only read-only SELECT/WITH queries are allowed")
        return statement

    @staticmethod
    def _physical_tables_from_tree(tree: exp.Query) -> list[exp.Table]:
        tables: list[exp.Table] = []
        for scope in traverse_scope(tree):
            for table in scope.tables:
                if (
                    isinstance(table, exp.Table)
                    and table.name
                    and table.name not in scope.cte_sources
                ):
                    tables.append(table)
        return tables

    @classmethod
    def _secure_table_expression(
        cls,
        *,
        model: type[Model],
        original_table: exp.Table,
        compiled_access: CompiledDjangoAccess,
        marker_prefix: str,
        marker_values: dict[int, Any],
        occurrence: int,
    ) -> exp.Subquery:
        raw_alias = f"__bloomerp_raw_{occurrence}"
        output_alias = original_table.alias or original_table.name
        raw_table = exp.Table(
            this=exp.to_identifier(model._meta.db_table),
            alias=exp.TableAlias(this=exp.to_identifier(raw_alias)),
        )

        field_predicates: dict[str, Q] = {}
        for row_filter, application_fields in compiled_access.field_filters.items():
            for application_field in application_fields:
                field_name = application_field.field
                existing = field_predicates.get(field_name)
                field_predicates[field_name] = (
                    row_filter if existing is None else existing | row_filter
                )

        projections: list[exp.Expression] = []
        for model_field in model._meta.concrete_fields:
            column_name = model_field.column
            raw_column = exp.column(column_name, table=raw_alias)
            field_predicate = field_predicates.get(model_field.name)

            if field_predicate is None:
                condition = exp.false()
            else:
                field_subquery = cls._pk_subquery(
                    model,
                    field_predicate,
                    marker_prefix,
                    marker_values,
                )
                condition = exp.In(
                    this=exp.column(model._meta.pk.column, table=raw_alias),
                    query=exp.Subquery(this=exp.Var(this=field_subquery)),
                )

            projections.append(
                exp.Case(
                    ifs=[exp.If(this=condition, true=raw_column)],
                    default=exp.Null(),
                ).as_(column_name)
            )

        row_subquery = cls._pk_subquery(
            model,
            compiled_access.row_filter,
            marker_prefix,
            marker_values,
        )
        row_condition = exp.In(
            this=exp.column(model._meta.pk.column, table=raw_alias),
            query=exp.Subquery(this=exp.Var(this=row_subquery)),
        )
        secured_select = (
            exp.Select(expressions=projections)
            .from_(raw_table)
            .where(row_condition)
        )
        return exp.Subquery(
            this=secured_select,
            alias=exp.TableAlias(this=exp.to_identifier(output_alias)),
        )

    @staticmethod
    def _pk_subquery(
        model: type[Model],
        row_filter: Q,
        marker_prefix: str,
        marker_values: dict[int, Any],
    ) -> str:
        queryset = (
            model.objects.filter(row_filter)
            .order_by()
            .values_list(model._meta.pk.attname, flat=True)
            .distinct()
        )
        sql, params = queryset.query.sql_with_params()
        if sql.count("%s") != len(params):
            raise ValueError("Unexpected SQL parameter format from Django")

        for value in params:
            marker_index = len(marker_values)
            marker = f"{marker_prefix}{marker_index}__"
            sql = sql.replace("%s", marker, 1)
            marker_values[marker_index] = value
        return sql
