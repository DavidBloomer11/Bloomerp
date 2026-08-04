import { FieldType, type FieldTypeDefinition } from "@/modules/fieldTypes";
import OneToManyFieldWidget, {
    type OneToManyAggregation,
} from "../widgets/OneToManyFieldWidget";

export enum BehaviorEvent {
    Change = "change",
    Initial = "initial",
}

export enum BehaviorConnector {
    All = "all",
    Any = "any",
}

export enum BehaviorResolver {
    IsoWeekDays = "iso_week_days",
    IsoWeek = "iso_week",
    BlankRows = "blank_rows",
    CopyRelatedRows = "copy_related_rows",
}

export enum BehaviorWritePolicy {
    IfEmpty = "if_empty",
    ReplaceGenerated = "replace_generated",
    Always = "always",
}

export enum BehaviorMessageTone {
    Info = "info",
    Warning = "warning",
    Error = "error",
}

export type BehaviorDefinition<TId extends string> = {
    id: TId;
    label: string;
};

export type CatalogField = {
    id: string;
    label: string;
    name: string;
    fieldType: string;
    columns?: CatalogField[];
};

export type BehaviorFieldValue = string | string[] | null;
export type BehaviorRelatedRow = Record<string, string | string[]>;

export type BehaviorCondition = {
    id: string;
    field: string;
    operator: string;
    value: string;
};

export type BehaviorActionConfig = {
    id: string;
    type: string;
    targetField: string;
    value: string;
    sourceField: string;
    resolver: BehaviorResolver;
    rowCount: number;
    writePolicy: BehaviorWritePolicy;
    messageTone: BehaviorMessageTone;
    aggregation: OneToManyAggregation;
    columnName: string;
};

export type BehaviorRule = {
    id: string;
    name: string;
    enabled: boolean;
    events: BehaviorEvent[];
    connector: BehaviorConnector;
    conditions: BehaviorCondition[];
    actions: BehaviorActionConfig[];
};

export type BehaviorConfig = {
    rules: BehaviorRule[];
};

export interface BehaviorRuntime {
    getFieldValue(fieldId: string): BehaviorFieldValue;
    setFieldValue(fieldId: string, value: BehaviorFieldValue): void;
    setFieldVisibility(fieldId: string, visible: boolean): void;
    setFieldEnabled(fieldId: string, enabled: boolean): void;
    setFieldRequired(fieldId: string, required: boolean): void;
    getOneToManyField(fieldId: string): OneToManyFieldWidget | null;
    isFieldEmpty(fieldId: string): boolean;
    showMessage(message: string, tone: BehaviorMessageTone): void;
    warn(message: string): void;
}

export type BehaviorDefinitionContext = {
    sourceField: CatalogField;
    fields: readonly CatalogField[];
};

type ActionConfigKey = Exclude<keyof BehaviorActionConfig, "id" | "type">;

type ActionEditorBase = {
    key: ActionConfigKey;
    label: string;
    rerender?: boolean;
};

export type BehaviorActionEditorField =
    | (ActionEditorBase & {
        kind: "field";
        fields: readonly CatalogField[];
    })
    | (ActionEditorBase & {
        kind: "select";
        options: readonly BehaviorDefinition<string>[];
    })
    | (ActionEditorBase & {
        kind: "text";
        placeholder?: string;
    })
    | (ActionEditorBase & {
        kind: "number";
        min?: number;
        max?: number;
    })
    | {
        kind: "warning";
        message: string;
    };

export type BehaviorConditionValueEditor =
    | { kind: "none" }
    | { kind: "text"; placeholder?: string }
    | { kind: "number" }
    | { kind: "date" }
    | { kind: "boolean" };

export const BEHAVIOR_WRITE_POLICY_DEFINITIONS: readonly BehaviorDefinition<BehaviorWritePolicy>[] = [
    { id: BehaviorWritePolicy.IfEmpty, label: "Only fill empty values" },
    { id: BehaviorWritePolicy.ReplaceGenerated, label: "Replace generated values" },
    { id: BehaviorWritePolicy.Always, label: "Always replace" },
];

export const BEHAVIOR_MESSAGE_TONE_DEFINITIONS: readonly BehaviorDefinition<BehaviorMessageTone>[] = [
    { id: BehaviorMessageTone.Info, label: "Information" },
    { id: BehaviorMessageTone.Warning, label: "Warning" },
    { id: BehaviorMessageTone.Error, label: "Error" },
];

const BEHAVIOR_RESOLVER_DEFINITIONS: readonly BehaviorDefinition<BehaviorResolver>[] = [
    { id: BehaviorResolver.IsoWeekDays, label: "Weekdays of ISO week" },
    { id: BehaviorResolver.IsoWeek, label: "Full ISO week" },
    { id: BehaviorResolver.BlankRows, label: "Create blank rows" },
    { id: BehaviorResolver.CopyRelatedRows, label: "Copy rows from another field" },
];

const AGGREGATION_DEFINITIONS: readonly BehaviorDefinition<OneToManyAggregation>[] = [
    { id: "count", label: "Count rows" },
    { id: "sum", label: "Sum" },
    { id: "average", label: "Average" },
    { id: "min", label: "Minimum" },
    { id: "max", label: "Maximum" },
    { id: "first", label: "First value" },
    { id: "last", label: "Last value" },
];

const NUMERIC_FIELD_TYPES: readonly FieldTypeDefinition[] = [
    FieldType.INTEGER_FIELD,
    FieldType.FLOAT_FIELD,
    FieldType.DECIMAL_FIELD,
    FieldType.POSITIVE_INTEGER_FIELD,
    FieldType.POSITIVE_SMALL_INTEGER_FIELD,
    FieldType.BIG_INTEGER_FIELD,
    FieldType.SMALL_INTEGER_FIELD,
];

const BOOLEAN_FIELD_TYPES: readonly FieldTypeDefinition[] = [
    FieldType.BOOLEAN_FIELD,
    FieldType.NULL_BOOLEAN_FIELD,
];

const DATE_FIELD_TYPES: readonly FieldTypeDefinition[] = [
    FieldType.DATE_FIELD,
    FieldType.DATE_TIME_FIELD,
    FieldType.WEEK_FIELD,
];

const TEXT_FIELD_TYPES: readonly FieldTypeDefinition[] = [
    FieldType.CHAR_FIELD,
    FieldType.CODE_FIELD,
    FieldType.CHOICE_FIELD,
    FieldType.TEXT_FIELD,
    FieldType.EMAIL_FIELD,
    FieldType.URL_FIELD,
    FieldType.ADDRESS_FIELD,
    FieldType.PHONE_NUMBER_FIELD,
    FieldType.SLUG_FIELD,
    FieldType.PROPERTY
];

function fieldHasType(field: CatalogField, types: readonly FieldTypeDefinition[]): boolean {
    return types.some(({ id }) => id === field.fieldType);
}

function fieldsOfType(
    fields: readonly CatalogField[],
    types: readonly FieldTypeDefinition[],
): CatalogField[] {
    return fields.filter((field) => fieldHasType(field, types));
}

function scalarFields(fields: readonly CatalogField[]): CatalogField[] {
    return fields.filter((field) => field.fieldType !== FieldType.ONE_TO_MANY_FIELD.id);
}

function normalizeRowCount(value: unknown): number {
    const parsed = typeof value === "number" ? value : Number.parseInt(String(value ?? ""), 10);
    if (!Number.isFinite(parsed)) return 5;
    return Math.min(100, Math.max(1, Math.trunc(parsed)));
}

function createActionConfig(
    type: string,
    value: Partial<BehaviorActionConfig>,
    context: BehaviorDefinitionContext,
    defaults: Partial<BehaviorActionConfig> = {},
): BehaviorActionConfig {
    return {
        id: value.id || createBehaviorId("action"),
        type,
        targetField: value.targetField || defaults.targetField || "",
        value: value.value ?? defaults.value ?? "",
        sourceField: value.sourceField || defaults.sourceField || context.sourceField.id,
        resolver: value.resolver || defaults.resolver || BehaviorResolver.BlankRows,
        rowCount: normalizeRowCount(value.rowCount ?? defaults.rowCount),
        writePolicy: value.writePolicy || defaults.writePolicy || BehaviorWritePolicy.ReplaceGenerated,
        messageTone: value.messageTone || defaults.messageTone || BehaviorMessageTone.Info,
        aggregation: value.aggregation || defaults.aggregation || "count",
        columnName: value.columnName || defaults.columnName || "",
    };
}

function targetFieldEditor(
    fields: readonly CatalogField[],
    label = "Target field",
): BehaviorActionEditorField {
    return { kind: "field", key: "targetField", label, fields };
}

function simpleTargetAction(
    id: string,
    label: string,
    execute: BehaviorActionExecutor,
): BehaviorActionDefinition {
    return new BehaviorActionDefinition({
        id,
        label,
        execute,
        editor: (_action, context) => [targetFieldEditor(context.fields)],
    });
}

function getComparableValue(value: BehaviorFieldValue): string {
    return Array.isArray(value) ? value.join(",") : String(value ?? "");
}

function compareValues(left: string, right: string): number {
    const leftNumber = Number(left);
    const rightNumber = Number(right);
    if (left.trim() && right.trim() && Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
        return leftNumber - rightNumber;
    }
    return left.localeCompare(right, undefined, { numeric: true, sensitivity: "base" });
}

function getIsoWeekDates(value: string, dayCount: 5 | 7): string[] {
    const match = /^(\d{4})-W(\d{2})$/.exec(value.trim());
    if (!match) return [];
    const year = Number.parseInt(match[1], 10);
    const week = Number.parseInt(match[2], 10);
    const januaryFourth = new Date(Date.UTC(year, 0, 4));
    const januaryFourthDay = januaryFourth.getUTCDay() || 7;
    const weekOneMonday = new Date(januaryFourth);
    weekOneMonday.setUTCDate(januaryFourth.getUTCDate() - januaryFourthDay + 1);
    const selectedMonday = new Date(weekOneMonday);
    selectedMonday.setUTCDate(weekOneMonday.getUTCDate() + (week - 1) * 7);

    return Array.from({ length: dayCount }, (_, index) => {
        const day = new Date(selectedMonday);
        day.setUTCDate(selectedMonday.getUTCDate() + index);
        return day.toISOString().slice(0, 10);
    });
}

function compatibleResolvers(context: BehaviorDefinitionContext): readonly BehaviorDefinition<BehaviorResolver>[] {
    if (context.sourceField.fieldType === FieldType.WEEK_FIELD.id) {
        return BEHAVIOR_RESOLVER_DEFINITIONS;
    }
    return BEHAVIOR_RESOLVER_DEFINITIONS.filter(
        ({ id }) => id === BehaviorResolver.BlankRows || id === BehaviorResolver.CopyRelatedRows,
    );
}

function aggregationDefinitionsFor(column?: CatalogField): readonly BehaviorDefinition<OneToManyAggregation>[] {
    if (!column) return AGGREGATION_DEFINITIONS.filter(({ id }) => id === "count");
    if (fieldHasType(column, NUMERIC_FIELD_TYPES)) return AGGREGATION_DEFINITIONS;
    return AGGREGATION_DEFINITIONS.filter(
        ({ id }) => ["count", "min", "max", "first", "last"].includes(id),
    );
}

export type BehaviorActionExecutor = (
    action: BehaviorActionConfig,
    runtime: BehaviorRuntime,
    sourceFieldId: string,
) => void;

type BehaviorActionDefinitionOptions = {
    id: string;
    label: string;
    execute: BehaviorActionExecutor;
    normalize?: (
        value: Partial<BehaviorActionConfig>,
        context: BehaviorDefinitionContext,
    ) => BehaviorActionConfig;
    editor?: (
        action: BehaviorActionConfig,
        context: BehaviorDefinitionContext,
    ) => readonly BehaviorActionEditorField[];
    summary?: (
        action: BehaviorActionConfig,
        context: BehaviorDefinitionContext,
    ) => string;
};

export class BehaviorActionDefinition implements BehaviorDefinition<string> {
    public readonly id: string;
    public readonly label: string;
    public readonly execute: BehaviorActionExecutor;
    private readonly normalizeConfig?: BehaviorActionDefinitionOptions["normalize"];
    private readonly buildEditor?: BehaviorActionDefinitionOptions["editor"];
    private readonly buildSummary?: BehaviorActionDefinitionOptions["summary"];

    public constructor(options: BehaviorActionDefinitionOptions) {
        this.id = options.id;
        this.label = options.label;
        this.execute = options.execute;
        this.normalizeConfig = options.normalize;
        this.buildEditor = options.editor;
        this.buildSummary = options.summary;
    }

    public normalize(
        value: Partial<BehaviorActionConfig>,
        context: BehaviorDefinitionContext,
    ): BehaviorActionConfig {
        return this.normalizeConfig?.(value, context)
            ?? createActionConfig(this.id, value, context);
    }

    public editor(
        action: BehaviorActionConfig,
        context: BehaviorDefinitionContext,
    ): readonly BehaviorActionEditorField[] {
        return this.buildEditor?.(action, context) ?? [];
    }

    public summarize(
        action: BehaviorActionConfig,
        context: BehaviorDefinitionContext,
    ): string {
        return this.buildSummary?.(action, context) ?? this.label.toLowerCase();
    }
}

type BehaviorConditionMatcher = (
    condition: BehaviorCondition,
    runtime: BehaviorRuntime,
) => boolean;

type BehaviorOperatorDefinitionOptions = {
    id: string;
    label: string;
    matches: BehaviorConditionMatcher;
    fieldTypes?: readonly FieldTypeDefinition[];
    valueEditor?: (
        field: CatalogField,
        condition: BehaviorCondition,
    ) => BehaviorConditionValueEditor;
};

export class BehaviorOperatorDefinition implements BehaviorDefinition<string> {
    public readonly id: string;
    public readonly label: string;
    private readonly matcher: BehaviorConditionMatcher;
    private readonly fieldTypes?: readonly FieldTypeDefinition[];
    private readonly editor?: BehaviorOperatorDefinitionOptions["valueEditor"];

    public constructor(options: BehaviorOperatorDefinitionOptions) {
        this.id = options.id;
        this.label = options.label;
        this.matcher = options.matches;
        this.fieldTypes = options.fieldTypes;
        this.editor = options.valueEditor;
    }

    public supports(field: CatalogField): boolean {
        return !this.fieldTypes || fieldHasType(field, this.fieldTypes);
    }

    public matches(condition: BehaviorCondition, runtime: BehaviorRuntime): boolean {
        return this.matcher(condition, runtime);
    }

    public valueEditor(field: CatalogField, condition: BehaviorCondition): BehaviorConditionValueEditor {
        if (this.editor) return this.editor(field, condition);
        if (fieldHasType(field, BOOLEAN_FIELD_TYPES)) return { kind: "boolean" };
        if (fieldHasType(field, NUMERIC_FIELD_TYPES)) return { kind: "number" };
        if (fieldHasType(field, DATE_FIELD_TYPES)) return { kind: "date" };
        return { kind: "text", placeholder: "Comparison value" };
    }
}

function comparableMatch(
    predicate: (actual: string, expected: string) => boolean,
): BehaviorConditionMatcher {
    return (condition, runtime) => predicate(
        getComparableValue(runtime.getFieldValue(condition.field)),
        condition.value ?? "",
    );
}

export class BehaviorOperator {
    public static readonly EQUALS = new BehaviorOperatorDefinition({
        id: "equals",
        label: "equals",
        matches: comparableMatch((actual, expected) => actual === expected),
    });

    public static readonly NOT_EQUALS = new BehaviorOperatorDefinition({
        id: "not_equals",
        label: "does not equal",
        matches: comparableMatch((actual, expected) => actual !== expected),
    });

    public static readonly IS_EMPTY = new BehaviorOperatorDefinition({
        id: "is_empty",
        label: "is empty",
        matches: (condition, runtime) => runtime.isFieldEmpty(condition.field),
        valueEditor: () => ({ kind: "none" }),
    });

    public static readonly IS_NOT_EMPTY = new BehaviorOperatorDefinition({
        id: "not_empty",
        label: "is not empty",
        matches: (condition, runtime) => !runtime.isFieldEmpty(condition.field),
        valueEditor: () => ({ kind: "none" }),
    });

    public static readonly CONTAINS = new BehaviorOperatorDefinition({
        id: "contains",
        label: "contains",
        matches: comparableMatch((actual, expected) => (
            actual.toLocaleLowerCase().includes(expected.toLocaleLowerCase())
        )),
        fieldTypes: TEXT_FIELD_TYPES,
    });

    public static readonly GREATER_THAN = new BehaviorOperatorDefinition({
        id: "greater_than",
        label: "is greater than",
        matches: comparableMatch((actual, expected) => compareValues(actual, expected) > 0),
        fieldTypes: [...NUMERIC_FIELD_TYPES, ...DATE_FIELD_TYPES],
    });

    public static readonly LESS_THAN = new BehaviorOperatorDefinition({
        id: "less_than",
        label: "is less than",
        matches: comparableMatch((actual, expected) => compareValues(actual, expected) < 0),
        fieldTypes: [...NUMERIC_FIELD_TYPES, ...DATE_FIELD_TYPES],
    });

    public static values(): readonly BehaviorOperatorDefinition[] {
        return Object.values(BehaviorOperator).filter(
            (value): value is BehaviorOperatorDefinition => value instanceof BehaviorOperatorDefinition,
        );
    }

    public static forField(field: CatalogField): readonly BehaviorOperatorDefinition[] {
        return BehaviorOperator.values().filter((definition) => definition.supports(field));
    }

    public static get(id: string): BehaviorOperatorDefinition | undefined {
        return BehaviorOperator.values().find((definition) => definition.id === id);
    }
}

function executePopulateRows(
    action: BehaviorActionConfig,
    runtime: BehaviorRuntime,
    sourceFieldId: string,
): void {
    const targetWidget = runtime.getOneToManyField(action.targetField);
    if (!targetWidget) return;
    const currentRows = targetWidget.getRows();

    let generatedRows: BehaviorRelatedRow[] = [];
    if (action.resolver === BehaviorResolver.BlankRows) {
        generatedRows = Array.from({ length: normalizeRowCount(action.rowCount) }, () => ({}));
    } else if (action.resolver === BehaviorResolver.CopyRelatedRows) {
        generatedRows = structuredClone(
            runtime.getOneToManyField(action.sourceField)?.getRows() ?? [],
        );
    } else if (
        action.resolver === BehaviorResolver.IsoWeekDays
        || action.resolver === BehaviorResolver.IsoWeek
    ) {
        const dateField = targetWidget.getFirstColumnName("date");
        const weekValue = getComparableValue(runtime.getFieldValue(sourceFieldId));
        if (!dateField || !weekValue) return;
        const dayCount = action.resolver === BehaviorResolver.IsoWeek ? 7 : 5;
        generatedRows = getIsoWeekDates(weekValue, dayCount)
            .map((dateValue) => ({ [dateField]: dateValue }));
    } else {
        runtime.warn(`Unknown related-row resolver '${action.resolver}' was skipped.`);
        return;
    }

    if (action.writePolicy === BehaviorWritePolicy.IfEmpty && currentRows.length > 0) return;
    const rows = action.writePolicy === BehaviorWritePolicy.ReplaceGenerated
        ? generatedRows.map((row, index) => ({ ...(currentRows[index] ?? {}), ...row }))
        : generatedRows;
    targetWidget.setRows(rows);
}

export class BehaviorAction {
    public static readonly SHOW_FIELD = simpleTargetAction(
        "show_field",
        "Show field",
        (action, runtime) => runtime.setFieldVisibility(action.targetField, true),
    );

    public static readonly HIDE_FIELD = simpleTargetAction(
        "hide_field",
        "Hide field",
        (action, runtime) => runtime.setFieldVisibility(action.targetField, false),
    );

    public static readonly ENABLE_FIELD = simpleTargetAction(
        "enable_field",
        "Enable field",
        (action, runtime) => runtime.setFieldEnabled(action.targetField, true),
    );

    public static readonly DISABLE_FIELD = simpleTargetAction(
        "disable_field",
        "Disable field",
        (action, runtime) => runtime.setFieldEnabled(action.targetField, false),
    );

    public static readonly REQUIRE_FIELD = simpleTargetAction(
        "require_field",
        "Make field required",
        (action, runtime) => runtime.setFieldRequired(action.targetField, true),
    );

    public static readonly MAKE_OPTIONAL = simpleTargetAction(
        "make_optional",
        "Make field optional",
        (action, runtime) => runtime.setFieldRequired(action.targetField, false),
    );

    public static readonly SET_VALUE = new BehaviorActionDefinition({
        id: "set_value",
        label: "Set field value",
        execute: (action, runtime) => runtime.setFieldValue(action.targetField, action.value),
        editor: (_action, context) => [
            targetFieldEditor(context.fields),
            { kind: "text", key: "value", label: "Value", placeholder: "Value" },
        ],
    });

    public static readonly CLEAR_VALUE = simpleTargetAction(
        "clear_value",
        "Clear field value",
        (action, runtime) => runtime.setFieldValue(action.targetField, ""),
    );

    public static readonly COPY_VALUE = new BehaviorActionDefinition({
        id: "copy_value",
        label: "Copy field value",
        execute: (action, runtime) => {
            runtime.setFieldValue(action.targetField, runtime.getFieldValue(action.sourceField));
        },
        editor: (action, context) => [
            targetFieldEditor(context.fields),
            {
                kind: "field",
                key: "sourceField",
                label: "Source field",
                fields: context.fields,
                rerender: true,
            },
            ...(action.sourceField && action.sourceField === action.targetField
                ? [{ kind: "warning" as const, message: "Source and target are the same, so this action will not change anything." }]
                : []),
        ],
        summary: (action, context) => {
            const source = context.fields.find(({ id }) => id === action.sourceField)?.label ?? "a source field";
            const target = context.fields.find(({ id }) => id === action.targetField)?.label ?? "a target field";
            return `copy ${source} into ${target}`;
        },
    });

    public static readonly POPULATE_ROWS = new BehaviorActionDefinition({
        id: "populate_rows",
        label: "Populate related rows",
        execute: executePopulateRows,
        normalize: (value, context) => {
            const resolvers = compatibleResolvers(context);
            const resolver = resolvers.some(({ id }) => id === value.resolver)
                ? value.resolver
                : resolvers[0]?.id ?? BehaviorResolver.BlankRows;
            return createActionConfig("populate_rows", value, context, { resolver });
        },
        editor: (action, context) => {
            const relatedFields = fieldsOfType(context.fields, [FieldType.ONE_TO_MANY_FIELD]);
            const fields: BehaviorActionEditorField[] = [
                targetFieldEditor(relatedFields, "Related field"),
                {
                    kind: "select",
                    key: "resolver",
                    label: "Recipe",
                    options: compatibleResolvers(context),
                    rerender: true,
                },
            ];
            if (action.resolver === BehaviorResolver.BlankRows) {
                fields.push({ kind: "number", key: "rowCount", label: "Number of rows", min: 1, max: 100 });
            } else if (action.resolver === BehaviorResolver.CopyRelatedRows) {
                fields.push({ kind: "field", key: "sourceField", label: "Copy rows from", fields: relatedFields });
            }
            fields.push({
                kind: "select",
                key: "writePolicy",
                label: "When a value already exists",
                options: BEHAVIOR_WRITE_POLICY_DEFINITIONS,
            });
            return fields;
        },
    });

    public static readonly FILTER_CHOICES = new BehaviorActionDefinition({
        id: "filter_choices",
        label: "Filter available choices",
        execute: (_action, runtime) => runtime.warn(
            "Behavior action 'filter_choices' requires a filter definition and was skipped.",
        ),
        editor: () => [{
            kind: "warning",
            message: "Choice filtering requires a filter definition and is not available yet.",
        }],
    });

    public static readonly SHOW_MESSAGE = new BehaviorActionDefinition({
        id: "show_message",
        label: "Show a message",
        execute: (action, runtime) => {
            if (action.value) runtime.showMessage(action.value, action.messageTone);
        },
        editor: () => [
            {
                kind: "select",
                key: "messageTone",
                label: "Tone",
                options: BEHAVIOR_MESSAGE_TONE_DEFINITIONS,
            },
            {
                kind: "text",
                key: "value",
                label: "Message",
                placeholder: "Message shown to the person filling the form",
            },
        ],
    });

    public static readonly COPY_VALUE_FROM_ONE_TO_MANY = new BehaviorActionDefinition({
        id: "copy_value_from_one_to_many",
        label: "Aggregate one-to-many values",
        execute: (action, runtime) => {
            const widget = runtime.getOneToManyField(action.sourceField);
            if (!(widget instanceof OneToManyFieldWidget)) {
                runtime.warn("The aggregation source is not an available one-to-many field.");
                return;
            }
            const value = widget.aggregateColumn(
                action.columnName,
                action.aggregation,
            );
            runtime.setFieldValue(action.targetField, String(value ?? ""));
        },
        normalize: (value, context) => {
            const relatedFields = fieldsOfType(context.fields, [FieldType.ONE_TO_MANY_FIELD]);
            const sourceField = relatedFields.some(({ id }) => id === value.sourceField)
                ? value.sourceField
                : context.sourceField.fieldType === FieldType.ONE_TO_MANY_FIELD.id
                    ? context.sourceField.id
                    : relatedFields[0]?.id ?? "";
            const source = relatedFields.find(({ id }) => id === sourceField);
            const columnName = source?.columns?.some(({ name }) => name === value.columnName)
                ? value.columnName ?? ""
                : source?.columns?.[0]?.name ?? "";
            const column = source?.columns?.find(({ name }) => name === columnName);
            const aggregations = aggregationDefinitionsFor(column);
            const aggregation = aggregations.some(({ id }) => id === value.aggregation)
                ? value.aggregation
                : aggregations[0]?.id ?? "count";
            return createActionConfig("copy_value_from_one_to_many", value, context, {
                sourceField,
                columnName,
                aggregation,
            });
        },
        editor: (action, context) => {
            const relatedFields = fieldsOfType(context.fields, [FieldType.ONE_TO_MANY_FIELD]);
            const source = relatedFields.find(({ id }) => id === action.sourceField);
            const column = source?.columns?.find(({ name }) => name === action.columnName);
            return [
                {
                    kind: "field",
                    key: "sourceField",
                    label: "One-to-many field",
                    fields: relatedFields,
                    rerender: true,
                },
                {
                    kind: "select",
                    key: "columnName",
                    label: "Column",
                    options: (source?.columns ?? []).map(({ name, label }) => ({ id: name, label })),
                    rerender: true,
                },
                {
                    kind: "select",
                    key: "aggregation",
                    label: "Aggregation",
                    options: aggregationDefinitionsFor(column),
                    rerender: true,
                },
                targetFieldEditor(scalarFields(context.fields)),
            ];
        },
        summary: (action, context) => {
            const source = context.fields.find(({ id }) => id === action.sourceField);
            const column = source?.columns?.find(({ name }) => name === action.columnName)?.label;
            const target = context.fields.find(({ id }) => id === action.targetField)?.label ?? "a target field";
            const subject = action.aggregation === "count" ? source?.label : column;
            return `${action.aggregation} ${subject ?? "related rows"} into ${target}`;
        },
    });

    public static values(): readonly BehaviorActionDefinition[] {
        return Object.values(BehaviorAction).filter(
            (value): value is BehaviorActionDefinition => value instanceof BehaviorActionDefinition,
        );
    }

    public static get(id: string): BehaviorActionDefinition | undefined {
        return BehaviorAction.values().find((definition) => definition.id === id);
    }
}

export function createBehaviorId(prefix: string): string {
    const suffix = typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    return `${prefix}-${suffix}`;
}

export function resolveBehaviorDefinitionId<TId extends string>(
    value: unknown,
    definitions: readonly BehaviorDefinition<TId>[],
    fallback: TId,
): TId {
    return definitions.some((definition) => definition.id === value) ? value as TId : fallback;
}

export const normalizeBehaviorRowCount = normalizeRowCount;
