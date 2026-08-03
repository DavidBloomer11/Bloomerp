import { FieldType, type FieldTypeDefinition } from "@/modules/fieldTypes";

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
    version: 1;
    rules: BehaviorRule[];
};

/**
 * The stable API available to behavior actions. Definitions own the behavior;
 * the form runtime only adapts these operations to the current DOM/widgets.
 */
export interface BehaviorActionExecutionContext {
    readonly action: BehaviorActionConfig;
    readonly sourceFieldId: string;
    getFieldValue(fieldId: string): BehaviorFieldValue;
    setFieldValue(fieldId: string, value: BehaviorFieldValue): void;
    setFieldVisibility(fieldId: string, visible: boolean): void;
    setFieldEnabled(fieldId: string, enabled: boolean): void;
    setFieldRequired(fieldId: string, required: boolean): void;
    getRelatedRows(fieldId: string): BehaviorRelatedRow[] | null;
    getRelatedDateField(fieldId: string): string | null;
    setRelatedRows(fieldId: string, rows: BehaviorRelatedRow[]): void;
    showMessage(message: string, tone: BehaviorMessageTone): void;
    warn(message: string): void;
}

export type BehaviorActionExecutor = (context: BehaviorActionExecutionContext) => void;

export class BehaviorActionDefinition implements BehaviorDefinition<string> {
    public readonly id: string;
    public readonly label: string;
    public readonly execute: BehaviorActionExecutor;
    public readonly targetFieldTypes?: readonly FieldTypeDefinition[];

    public constructor(
        id: string,
        label: string,
        execute: BehaviorActionExecutor,
        targetFieldTypes?: readonly FieldTypeDefinition[],
    ) {
        this.id = id;
        this.label = label;
        this.execute = execute;
        this.targetFieldTypes = targetFieldTypes;
    }
}

export class BehaviorOperatorDefinition implements BehaviorDefinition<string> {
    public readonly id: string;
    public readonly label: string;

    public constructor(id: string, label: string) {
        this.id = id;
        this.label = label;
    }
}

export class BehaviorOperator {
    public static readonly EQUALS = new BehaviorOperatorDefinition("equals", "equals");
    public static readonly NOT_EQUALS = new BehaviorOperatorDefinition("not_equals", "does not equal");
    public static readonly IS_EMPTY = new BehaviorOperatorDefinition("is_empty", "is empty");
    public static readonly IS_NOT_EMPTY = new BehaviorOperatorDefinition("not_empty", "is not empty");
    public static readonly CONTAINS = new BehaviorOperatorDefinition("contains", "contains");
    public static readonly GREATER_THAN = new BehaviorOperatorDefinition("greater_than", "is greater than");
    public static readonly LESS_THAN = new BehaviorOperatorDefinition("less_than", "is less than");

    public static values(): readonly BehaviorOperatorDefinition[] {
        return Object.values(BehaviorOperator).filter(
            (value): value is BehaviorOperatorDefinition => value instanceof BehaviorOperatorDefinition,
        );
    }

    public static get(id: string): BehaviorOperatorDefinition | undefined {
        return BehaviorOperator.values().find((definition) => definition.id === id);
    }
}

export type BehaviorResolverDefinition = BehaviorDefinition<BehaviorResolver> & {
    sourceFieldTypes?: readonly FieldTypeDefinition[];
};

export const BEHAVIOR_RESOLVER_DEFINITIONS: readonly BehaviorResolverDefinition[] = [
    {
        id: BehaviorResolver.IsoWeekDays,
        label: "Weekdays of ISO week",
        sourceFieldTypes: [FieldType.WEEK_FIELD],
    },
    {
        id: BehaviorResolver.IsoWeek,
        label: "Full ISO week",
        sourceFieldTypes: [FieldType.WEEK_FIELD],
    },
    { id: BehaviorResolver.BlankRows, label: "Create blank rows" },
    { id: BehaviorResolver.CopyRelatedRows, label: "Copy rows from another field" },
];

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

function getComparableValue(value: BehaviorFieldValue): string {
    return Array.isArray(value) ? value.join(",") : String(value ?? "");
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

function executePopulateRows(context: BehaviorActionExecutionContext): void {
    const { action } = context;
    const currentRows = context.getRelatedRows(action.targetField);
    if (currentRows === null) return;
    
    let generatedRows: BehaviorRelatedRow[] = [];
    if (action.resolver === BehaviorResolver.BlankRows) {
        generatedRows = Array.from({ length: normalizeBehaviorRowCount(action.rowCount) }, () => ({}));
    } else if (action.resolver === BehaviorResolver.CopyRelatedRows) {
        const sourceRows = context.getRelatedRows(action.sourceField);
        generatedRows = sourceRows === null ? [] : structuredClone(sourceRows);
    } else if (
        action.resolver === BehaviorResolver.IsoWeekDays
        || action.resolver === BehaviorResolver.IsoWeek
    ) {
        const dateField = context.getRelatedDateField(action.targetField);
        const weekValue = getComparableValue(context.getFieldValue(context.sourceFieldId));
        if (!dateField || !weekValue) return;
        const dayCount = action.resolver === BehaviorResolver.IsoWeek ? 7 : 5;
        const dates = getIsoWeekDates(weekValue, dayCount);
        if (!dates.length) return;
        generatedRows = dates.map((dateValue) => ({ [dateField]: dateValue }));
    } else {
        context.warn(`Unknown related-row resolver '${action.resolver}' was skipped.`);
        return;
    }

    if (action.writePolicy === BehaviorWritePolicy.IfEmpty && currentRows.length > 0) return;
    const rows = action.writePolicy === BehaviorWritePolicy.ReplaceGenerated
        ? generatedRows.map((row, index) => ({ ...(currentRows[index] ?? {}), ...row }))
        : generatedRows;
    context.setRelatedRows(action.targetField, rows);
}

export class BehaviorAction {
    public static readonly SHOW_FIELD = new BehaviorActionDefinition(
        "show_field",
        "Show field",
        ({ action, setFieldVisibility }) => setFieldVisibility(action.targetField, true),
    );

    public static readonly HIDE_FIELD = new BehaviorActionDefinition(
        "hide_field",
        "Hide field",
        ({ action, setFieldVisibility }) => setFieldVisibility(action.targetField, false),
    );

    public static readonly ENABLE_FIELD = new BehaviorActionDefinition(
        "enable_field",
        "Enable field",
        ({ action, setFieldEnabled }) => setFieldEnabled(action.targetField, true),
    );

    public static readonly DISABLE_FIELD = new BehaviorActionDefinition(
        "disable_field",
        "Disable field",
        ({ action, setFieldEnabled }) => setFieldEnabled(action.targetField, false),
    );

    public static readonly REQUIRE_FIELD = new BehaviorActionDefinition(
        "require_field",
        "Make field required",
        ({ action, setFieldRequired }) => setFieldRequired(action.targetField, true),
    );

    public static readonly MAKE_OPTIONAL = new BehaviorActionDefinition(
        "make_optional",
        "Make field optional",
        ({ action, setFieldRequired }) => setFieldRequired(action.targetField, false),
    );

    public static readonly SET_VALUE = new BehaviorActionDefinition(
        "set_value",
        "Set field value",
        ({ action, setFieldValue }) => setFieldValue(action.targetField, action.value),
    );

    public static readonly CLEAR_VALUE = new BehaviorActionDefinition(
        "clear_value",
        "Clear field value",
        ({ action, setFieldValue }) => setFieldValue(action.targetField, ""),
    );

    public static readonly COPY_VALUE = new BehaviorActionDefinition(
        "copy_value",
        "Copy field value",
        ({ action, getFieldValue, setFieldValue }) => {
            setFieldValue(action.targetField, getFieldValue(action.sourceField));
        },
    );

    public static readonly POPULATE_ROWS = new BehaviorActionDefinition(
        "populate_rows",
        "Populate related rows",
        executePopulateRows,
        [FieldType.ONE_TO_MANY_FIELD],
    );

    public static readonly FILTER_CHOICES = new BehaviorActionDefinition(
        "filter_choices",
        "Filter available choices",
        ({ warn }) => warn("Behavior action 'filter_choices' requires a filter definition and was skipped."),
    );

    public static readonly SHOW_MESSAGE = new BehaviorActionDefinition(
        "show_message",
        "Show a message",
        ({ action, showMessage }) => {
            if (action.value) showMessage(action.value, action.messageTone);
        },
    );

    public static values(): readonly BehaviorActionDefinition[] {
        return Object.values(BehaviorAction).filter(
            (value): value is BehaviorActionDefinition => value instanceof BehaviorActionDefinition,
        );
    }

    public static get(id: string): BehaviorActionDefinition | undefined {
        return BehaviorAction.values().find((definition) => definition.id === id);
    }
}

export function resolveBehaviorDefinitionId<TId extends string>(
    value: unknown,
    definitions: readonly BehaviorDefinition<TId>[],
    fallback: TId,
): TId {
    return definitions.some((definition) => definition.id === value) ? value as TId : fallback;
}

export function normalizeBehaviorRowCount(value: unknown): number {
    const parsed = typeof value === "number" ? value : Number.parseInt(String(value ?? ""), 10);
    if (!Number.isFinite(parsed)) return 5;
    return Math.min(100, Math.max(1, Math.trunc(parsed)));
}
