import BaseComponent from "../BaseComponent";
import {
    BEHAVIOR_MESSAGE_TONE_DEFINITIONS,
    BEHAVIOR_RESOLVER_DEFINITIONS,
    BEHAVIOR_WRITE_POLICY_DEFINITIONS,
    BehaviorAction,
    BehaviorConnector,
    BehaviorEvent,
    BehaviorMessageTone,
    BehaviorOperator,
    BehaviorResolver,
    BehaviorWritePolicy,
    normalizeBehaviorRowCount,
    resolveBehaviorDefinitionId,
    type BehaviorActionConfig,
    type BehaviorConfig,
    type BehaviorCondition,
    type BehaviorDefinition,
    type BehaviorRule,
    type BehaviorResolverDefinition,
} from "../behaviors/BehaviorDefinitions";

export type {
    BehaviorActionConfig,
    BehaviorConfig,
    BehaviorCondition,
    BehaviorRule,
} from "../behaviors/BehaviorDefinitions";

export type CatalogField = {
    id: string;
    label: string;
    name: string;
    fieldType: string;
};

function parseJson<T>(value: string | undefined, fallback: T): T {
    if (!value) return fallback;
    try {
        return JSON.parse(value) as T;
    } catch {
        return fallback;
    }
}

function newBehaviorId(prefix: string): string {
    const suffix = typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    return `${prefix}-${suffix}`;
}

function escapeHtml(value: unknown): string {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

export default class BehaviorBuilder extends BaseComponent {
    private input: HTMLInputElement | null = null;
    private rulesContainer: HTMLElement | null = null;
    private fields: CatalogField[] = [];
    private sourceFieldId = "";
    private sourceFieldLabel = "This field";
    private sourceFieldType = "";
    private config: BehaviorConfig = { version: 1, rules: [] };
    private clickHandler: ((event: Event) => void) | null = null;
    private changeHandler: ((event: Event) => void) | null = null;
    private inputHandler: ((event: Event) => void) | null = null;

    public initialize(): void {
        if (!this.element) return;

        this.input = this.element.querySelector<HTMLInputElement>("[data-behavior-input]");
        this.rulesContainer = this.element.querySelector<HTMLElement>("[data-behavior-rules]");
        this.sourceFieldId = this.element.dataset.behaviorSourceFieldId ?? "";
        this.sourceFieldLabel = this.element.dataset.behaviorSourceFieldLabel ?? "This field";
        this.sourceFieldType = this.element.dataset.behaviorSourceFieldType ?? "";
        this.fields = this.parseFields(this.element.dataset.behaviorFieldCatalog);
        this.config = this.parseConfig(this.input?.value);

        this.clickHandler = (event) => this.handleClick(event);
        this.changeHandler = (event) => this.handleChange(event);
        this.inputHandler = () => this.syncConfigFromDom();
        this.element.addEventListener("click", this.clickHandler);
        this.element.addEventListener("change", this.changeHandler);
        this.element.addEventListener("input", this.inputHandler);

        this.render();
    }

    public destroy(): void {
        if (this.element && this.clickHandler) this.element.removeEventListener("click", this.clickHandler);
        if (this.element && this.changeHandler) this.element.removeEventListener("change", this.changeHandler);
        if (this.element && this.inputHandler) this.element.removeEventListener("input", this.inputHandler);
        this.clickHandler = null;
        this.changeHandler = null;
        this.inputHandler = null;
        this.input = null;
        this.rulesContainer = null;
    }

    private parseFields(value: string | undefined): CatalogField[] {
        const parsed = parseJson<unknown>(value, []);
        return Array.isArray(parsed) ? parsed as CatalogField[] : [];
    }

    private parseConfig(value: string | undefined): BehaviorConfig {
        const parsed = parseJson<unknown>(value, {});
        const rules = Array.isArray(parsed)
            ? parsed
            : (parsed as { rules?: unknown })?.rules;
        return {
            version: 1,
            rules: Array.isArray(rules)
                ? rules.map((rule) => this.normalizeRule(rule as Partial<BehaviorRule>))
                : [],
        };
    }

    private normalizeRule(value: Partial<BehaviorRule>): BehaviorRule {
        const events = Array.isArray(value.events)
            ? value.events.filter((event) => event === BehaviorEvent.Change || event === BehaviorEvent.Initial)
            : [];
        return {
            id: value.id || newBehaviorId("rule"),
            name: value.name || "",
            enabled: value.enabled !== false,
            events: events.length ? events : [BehaviorEvent.Change],
            connector: value.connector === BehaviorConnector.Any ? BehaviorConnector.Any : BehaviorConnector.All,
            conditions: Array.isArray(value.conditions)
                ? value.conditions.map((condition) => this.normalizeCondition(condition))
                : [],
            actions: Array.isArray(value.actions) && value.actions.length
                ? value.actions.map((action) => this.normalizeAction(action))
                : [this.normalizeAction({})],
        };
    }

    private normalizeCondition(value: Partial<BehaviorCondition>): BehaviorCondition {
        return {
            id: value.id || newBehaviorId("condition"),
            field: value.field || this.sourceFieldId,
            operator: resolveBehaviorDefinitionId(
                value.operator,
                BehaviorOperator.values(),
                BehaviorOperator.EQUALS.id,
            ),
            value: value.value || "",
        };
    }

    private normalizeAction(value: Partial<BehaviorActionConfig>): BehaviorActionConfig {
        const compatibleResolvers = this.getCompatibleResolvers();
        const fallbackResolver = compatibleResolvers[0]?.id ?? BehaviorResolver.BlankRows;
        const requestedResolver = resolveBehaviorDefinitionId(
            value.resolver,
            BEHAVIOR_RESOLVER_DEFINITIONS,
            fallbackResolver,
        );
        const resolver = compatibleResolvers.some(({ id }) => id === requestedResolver)
            ? requestedResolver
            : fallbackResolver;
        const action: BehaviorActionConfig = {
            id: value.id || newBehaviorId("action"),
            type: resolveBehaviorDefinitionId(
                value.type,
                BehaviorAction.values(),
                BehaviorAction.SHOW_FIELD.id,
            ),
            targetField: value.targetField || "",
            value: value.value || "",
            sourceField: value.sourceField || this.sourceFieldId,
            resolver,
            rowCount: normalizeBehaviorRowCount(value.rowCount),
            writePolicy: resolveBehaviorDefinitionId(
                value.writePolicy,
                BEHAVIOR_WRITE_POLICY_DEFINITIONS,
                BehaviorWritePolicy.ReplaceGenerated,
            ),
            messageTone: resolveBehaviorDefinitionId(
                value.messageTone,
                BEHAVIOR_MESSAGE_TONE_DEFINITIONS,
                BehaviorMessageTone.Info,
            ),
        };
        return this.normalizeActionTarget(action);
    }

    private normalizeActionTarget(action: BehaviorActionConfig): BehaviorActionConfig {
        if (action.type === BehaviorAction.SHOW_MESSAGE.id) return { ...action, targetField: "" };
        if (!action.targetField) return action;

        const compatibleFields = this.getActionTargetFields(action.type);
        return compatibleFields.some((field) => field.id === action.targetField)
            ? action
            : { ...action, targetField: "" };
    }

    private getActionTargetFields(actionType: string): CatalogField[] {
        const allowedTypes = BehaviorAction.get(actionType)?.targetFieldTypes;
        return allowedTypes
            ? this.fields.filter((field) => allowedTypes.some(({ id }) => id === field.fieldType))
            : this.fields;
    }

    private getCompatibleResolvers(): BehaviorResolverDefinition[] {
        return BEHAVIOR_RESOLVER_DEFINITIONS.filter((definition) => {
            const allowedTypes = definition.sourceFieldTypes;
            return !allowedTypes || allowedTypes.some(({ id }) => id === this.sourceFieldType);
        });
    }

    private handleClick(event: Event): void {
        const button = (event.target as HTMLElement | null)?.closest<HTMLButtonElement>("button");
        if (!button || !this.element?.contains(button)) return;

        this.syncConfigFromDom();
        if (button.matches("[data-behavior-add-rule]")) {
            this.config.rules.push(this.normalizeRule({ name: `Behavior ${this.config.rules.length + 1}` }));
        } else {
            const ruleElement = button.closest<HTMLElement>("[data-behavior-rule]");
            const rule = this.config.rules.find((item) => item.id === ruleElement?.dataset.behaviorRule);
            if (!rule) return;

            if (button.matches("[data-behavior-delete-rule]")) {
                this.config.rules = this.config.rules.filter((item) => item.id !== rule.id);
            } else if (button.matches("[data-behavior-move-rule]")) {
                this.moveRule(rule.id, button.dataset.behaviorMoveRule === "up" ? -1 : 1);
            } else if (button.matches("[data-behavior-add-condition]")) {
                rule.conditions.push(this.normalizeCondition({}));
            } else if (button.matches("[data-behavior-remove-condition]")) {
                const id = button.closest<HTMLElement>("[data-behavior-condition]")?.dataset.behaviorCondition;
                rule.conditions = rule.conditions.filter((item) => item.id !== id);
            } else if (button.matches("[data-behavior-add-action]")) {
                rule.actions.push(this.normalizeAction({}));
            } else if (button.matches("[data-behavior-remove-action]")) {
                const id = button.closest<HTMLElement>("[data-behavior-action]")?.dataset.behaviorAction;
                rule.actions = rule.actions.filter((item) => item.id !== id);
                if (!rule.actions.length) rule.actions.push(this.normalizeAction({}));
            } else {
                return;
            }
        }

        this.writeConfig();
        this.render();
    }

    private handleChange(event: Event): void {
        this.syncConfigFromDom();
        const target = event.target as HTMLElement | null;
        if (target?.hasAttribute("data-behavior-rerender")) this.render();
    }

    private moveRule(id: string, offset: number): void {
        const index = this.config.rules.findIndex((rule) => rule.id === id);
        const nextIndex = index + offset;
        if (index < 0 || nextIndex < 0 || nextIndex >= this.config.rules.length) return;
        const [rule] = this.config.rules.splice(index, 1);
        this.config.rules.splice(nextIndex, 0, rule);
    }

    private syncConfigFromDom(): void {
        if (!this.rulesContainer) return;
        const previousRules = new Map(this.config.rules.map((rule) => [rule.id, rule]));
        this.config.rules = Array.from(this.rulesContainer.querySelectorAll<HTMLElement>("[data-behavior-rule]")).map((element) => {
            const id = element.dataset.behaviorRule ?? newBehaviorId("rule");
            const previous = previousRules.get(id) ?? this.normalizeRule({ id });
            const previousActions = new Map(previous.actions.map((action) => [action.id, action]));
            return {
                ...previous,
                name: this.valueOf(element, "[data-behavior-name]"),
                enabled: this.checkedOf(element, "[data-behavior-enabled]"),
                events: [
                    BehaviorEvent.Change,
                    ...(this.checkedOf(element, "[data-behavior-initial]") ? [BehaviorEvent.Initial] : []),
                ],
                connector: this.valueOf(element, "[data-behavior-connector]") === BehaviorConnector.Any
                    ? BehaviorConnector.Any
                    : BehaviorConnector.All,
                conditions: Array.from(element.querySelectorAll<HTMLElement>("[data-behavior-condition]")).map((row) => ({
                    id: row.dataset.behaviorCondition ?? newBehaviorId("condition"),
                    field: this.valueOf(row, "[data-behavior-condition-field]"),
                    operator: resolveBehaviorDefinitionId(
                        this.valueOf(row, "[data-behavior-condition-operator]"),
                        BehaviorOperator.values(),
                        BehaviorOperator.EQUALS.id,
                    ),
                    value: this.valueOf(row, "[data-behavior-condition-value]"),
                })),
                actions: Array.from(element.querySelectorAll<HTMLElement>("[data-behavior-action]")).map((row) => {
                    const actionId = row.dataset.behaviorAction ?? newBehaviorId("action");
                    const previousAction = previousActions.get(actionId) ?? this.normalizeAction({ id: actionId });
                    return this.normalizeActionTarget({
                        id: actionId,
                        type: resolveBehaviorDefinitionId(
                            this.optionalValueOf(row, "[data-behavior-action-type]"),
                            BehaviorAction.values(),
                            previousAction.type,
                        ),
                        targetField: this.optionalValueOf(row, "[data-behavior-action-target]") ?? previousAction.targetField,
                        value: this.optionalValueOf(row, "[data-behavior-action-value]") ?? previousAction.value,
                        sourceField: this.optionalValueOf(row, "[data-behavior-action-source]") ?? previousAction.sourceField,
                        resolver: resolveBehaviorDefinitionId(
                            this.optionalValueOf(row, "[data-behavior-action-resolver]"),
                            BEHAVIOR_RESOLVER_DEFINITIONS,
                            previousAction.resolver,
                        ),
                        rowCount: normalizeBehaviorRowCount(
                            this.optionalValueOf(row, "[data-behavior-action-row-count]") ?? previousAction.rowCount,
                        ),
                        writePolicy: resolveBehaviorDefinitionId(
                            this.optionalValueOf(row, "[data-behavior-action-write-policy]"),
                            BEHAVIOR_WRITE_POLICY_DEFINITIONS,
                            previousAction.writePolicy,
                        ),
                        messageTone: resolveBehaviorDefinitionId(
                            this.optionalValueOf(row, "[data-behavior-action-message-tone]"),
                            BEHAVIOR_MESSAGE_TONE_DEFINITIONS,
                            previousAction.messageTone,
                        ),
                    });
                }),
            };
        });
        this.writeConfig();
        this.syncSummaries();
    }

    private valueOf(root: ParentNode, selector: string): string {
        return root.querySelector<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(selector)?.value ?? "";
    }

    private optionalValueOf(root: ParentNode, selector: string): string | undefined {
        return root.querySelector<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(selector)?.value;
    }

    private checkedOf(root: ParentNode, selector: string): boolean {
        return root.querySelector<HTMLInputElement>(selector)?.checked ?? false;
    }

    private writeConfig(): void {
        if (this.input) this.input.value = JSON.stringify(this.config);
    }

    private render(): void {
        if (!this.rulesContainer) return;
        if (!this.config.rules.length) {
            this.rulesContainer.innerHTML = this.renderEmptyState();
            this.writeConfig();
            return;
        }
        this.rulesContainer.innerHTML = this.config.rules.map((rule, index) => this.renderRule(rule, index)).join("");
        this.writeConfig();
        this.syncSummaries();
    }

    private renderEmptyState(): string {
        return `
            <div class="bg-white px-5 py-8 text-center">
                <span class="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <i class="fa-solid fa-bolt"></i>
                </span>
                <p class="mt-3 text-sm font-medium text-dark">No behaviors yet</p>
                <p class="mx-auto mt-1 max-w-sm text-xs leading-5 text-gray-500">Add a behavior to show fields, set values, filter choices, or populate related rows when ${escapeHtml(this.sourceFieldLabel)} changes.</p>
            </div>`;
    }

    private renderRule(rule: BehaviorRule, index: number): string {
        const conditionRows = rule.conditions.length
            ? rule.conditions.map((condition) => this.renderCondition(condition)).join("")
            : `<div class="rounded-xl border border-dashed border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-500">No conditions — this behavior always runs.</div>`;
        return `
            <section class="overflow-hidden border-b border-gray-200 bg-white shadow-xs" data-behavior-rule="${escapeHtml(rule.id)}">
                <div class="flex flex-wrap items-center gap-3 border-b border-gray-200 bg-gray-50 px-3 py-2.5">
                    <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">${index + 1}</span>
                    <input class="input input-sm min-w-0 flex-1 border-transparent bg-transparent font-medium" value="${escapeHtml(rule.name || `Behavior ${index + 1}`)}" aria-label="Behavior name" data-behavior-name>
                    <label class="flex items-center gap-1.5 text-xs text-gray-600">
                        <input type="checkbox" class="toggle toggle-sm" ${rule.enabled ? "checked" : ""} data-behavior-enabled>
                        Enabled
                    </label>
                    <div class="flex items-center">
                        <button type="button" class="btn btn-ghost btn-xs" title="Move up" ${index === 0 ? "disabled" : ""} data-behavior-move-rule="up"><i class="fa-solid fa-arrow-up"></i></button>
                        <button type="button" class="btn btn-ghost btn-xs" title="Move down" ${index === this.config.rules.length - 1 ? "disabled" : ""} data-behavior-move-rule="down"><i class="fa-solid fa-arrow-down"></i></button>
                        <button type="button" class="btn btn-ghost btn-xs text-danger-dark" title="Delete behavior" data-behavior-delete-rule><i class="fa-solid fa-trash"></i></button>
                    </div>
                </div>

                <div class="space-y-4 p-4">
                    <div class="grid gap-3 md:grid-cols-[64px_minmax(0,1fr)]">
                        <div class="pt-2 text-xs font-semibold uppercase tracking-wide text-primary">When</div>
                        <div class="space-y-2">
                            <div class="flex flex-wrap items-center gap-2 rounded-xl bg-primary/5 px-3 py-2 text-sm text-dark">
                                <span class="font-medium">${escapeHtml(this.sourceFieldLabel)}</span>
                                <span>changes</span>
                            </div>
                            <label class="flex items-center gap-2 text-xs text-gray-600">
                                <input type="checkbox" ${rule.events.includes(BehaviorEvent.Initial) ? "checked" : ""} data-behavior-initial>
                                Also run when the form opens
                            </label>
                        </div>
                    </div>

                    <div class="grid gap-3 border-t border-gray-200 pt-4 md:grid-cols-[64px_minmax(0,1fr)]">
                        <div class="pt-2 text-xs font-semibold uppercase tracking-wide text-warning-dark">If</div>
                        <div class="space-y-2">
                            ${rule.conditions.length > 1 ? `
                                <label class="flex items-center gap-2 text-xs text-gray-600">Match
                                    <select class="select select-sm w-auto" data-behavior-connector>
                                        <option value="${BehaviorConnector.All}" ${rule.connector === BehaviorConnector.All ? "selected" : ""}>all conditions</option>
                                        <option value="${BehaviorConnector.Any}" ${rule.connector === BehaviorConnector.Any ? "selected" : ""}>any condition</option>
                                    </select>
                                </label>` : `<input type="hidden" value="${rule.connector}" data-behavior-connector>`}
                            <div class="space-y-2">${conditionRows}</div>
                            <button type="button" class="btn btn-secondary btn-xs" data-behavior-add-condition><i class="fa-solid fa-plus"></i> Add condition</button>
                        </div>
                    </div>

                    <div class="grid gap-3 border-t border-gray-200 pt-4 md:grid-cols-[64px_minmax(0,1fr)]">
                        <div class="pt-2 text-xs font-semibold uppercase tracking-wide text-success-dark">Then</div>
                        <div class="space-y-2">
                            ${rule.actions.map((action) => this.renderAction(action)).join("")}
                            <button type="button" class="btn btn-secondary btn-xs" data-behavior-add-action><i class="fa-solid fa-plus"></i> Add action</button>
                        </div>
                    </div>
                </div>

                <div class="border-t border-gray-200 bg-gray-50 px-4 py-2 text-xs text-gray-500" data-behavior-summary></div>
            </section>`;
    }

    private renderCondition(condition: BehaviorCondition): string {
        const hidesValue = [BehaviorOperator.IS_EMPTY.id, BehaviorOperator.IS_NOT_EMPTY.id]
            .includes(condition.operator);
        return `
            <div class="grid gap-2 rounded-xl border border-gray-200 p-2 sm:grid-cols-[minmax(120px,1fr)_minmax(130px,1fr)_minmax(120px,1fr)_auto]" data-behavior-condition="${escapeHtml(condition.id)}">
                ${this.renderFieldSelect(condition.field, "data-behavior-condition-field")}
                ${this.renderSelect(BehaviorOperator.values(), condition.operator, "data-behavior-condition-operator data-behavior-rerender")}
                <input class="input input-sm ${hidesValue ? "invisible" : ""}" value="${escapeHtml(condition.value)}" placeholder="Comparison value" data-behavior-condition-value>
                <button type="button" class="btn btn-ghost btn-xs self-center text-gray-400 hover:text-danger-dark" title="Remove condition" data-behavior-remove-condition><i class="fa-solid fa-xmark"></i></button>
            </div>`;
    }

    private renderAction(action: BehaviorActionConfig): string {
        const needsTarget = action.type !== BehaviorAction.SHOW_MESSAGE.id;
        const targetFields = this.getActionTargetFields(action.type);
        const targetLabel = action.type === BehaviorAction.POPULATE_ROWS.id ? "Related field" : "Target field";
        const targetAttributes = action.type === BehaviorAction.COPY_VALUE.id
            ? "data-behavior-action-target data-behavior-rerender"
            : "data-behavior-action-target";
        return `
            <div class="space-y-2 rounded-xl border border-gray-200 p-2" data-behavior-action="${escapeHtml(action.id)}">
                <div class="grid gap-2 sm:grid-cols-[minmax(160px,1fr)_minmax(140px,1fr)_auto]">
                    <label class="text-xs text-gray-500">Action${this.renderSelect(BehaviorAction.values(), action.type, "data-behavior-action-type data-behavior-rerender")}</label>
                    ${needsTarget ? `<label class="text-xs text-gray-500">${targetLabel}${this.renderFieldSelect(action.targetField, targetAttributes, targetFields)}</label>` : `<div></div>`}
                    <button type="button" class="btn btn-ghost btn-xs self-center text-gray-400 hover:text-danger-dark" title="Remove action" data-behavior-remove-action><i class="fa-solid fa-xmark"></i></button>
                </div>
                ${this.renderActionDetails(action)}
            </div>`;
    }

    private renderActionDetails(action: BehaviorActionConfig): string {
        if (action.type === BehaviorAction.SET_VALUE.id) {
            return `<input class="input input-sm w-full" value="${escapeHtml(action.value)}" placeholder="Value" data-behavior-action-value>`;
        }
        if (action.type === BehaviorAction.COPY_VALUE.id) {
            const sameFieldWarning = action.sourceField && action.sourceField === action.targetField
                ? `<p class="text-xs text-warning-dark"><i class="fa-solid fa-triangle-exclamation me-1"></i>Source and target are the same, so this action will not change anything.</p>`
                : "";
            return `<label class="block text-xs text-gray-500">Source field${this.renderFieldSelect(action.sourceField, "data-behavior-action-source data-behavior-rerender")}</label>${sameFieldWarning}`;
        }
        if (action.type === BehaviorAction.POPULATE_ROWS.id) {
            const recipeField = `<label class="text-xs text-gray-500">Recipe${this.renderSelect(this.getCompatibleResolvers(), action.resolver, "data-behavior-action-resolver data-behavior-rerender")}</label>`;
            let recipeOptions = "";
            if (action.resolver === BehaviorResolver.BlankRows) {
                recipeOptions = `<label class="text-xs text-gray-500">Number of rows<input type="number" min="1" max="100" class="input input-sm w-full" value="${action.rowCount}" data-behavior-action-row-count></label>`;
            } else if (action.resolver === BehaviorResolver.CopyRelatedRows) {
                recipeOptions = `<label class="text-xs text-gray-500">Copy rows from${this.renderFieldSelect(action.sourceField, "data-behavior-action-source", this.getActionTargetFields(BehaviorAction.POPULATE_ROWS.id))}</label>`;
            }
            return `<div class="grid gap-2 sm:grid-cols-2">${recipeField}${recipeOptions}</div>${this.renderWritePolicy(action.writePolicy)}`;
        }
        if (action.type === BehaviorAction.FILTER_CHOICES.id) {
            return `<p class="text-xs text-warning-dark">Choice filtering requires a filter definition and is not available yet.</p>`;
        }
        if (action.type === BehaviorAction.SHOW_MESSAGE.id) {
            return `<div class="grid gap-2 sm:grid-cols-[140px_minmax(0,1fr)]">${this.renderSelect(BEHAVIOR_MESSAGE_TONE_DEFINITIONS, action.messageTone, "data-behavior-action-message-tone")}<input class="input input-sm" value="${escapeHtml(action.value)}" placeholder="Message shown to the person filling the form" data-behavior-action-value></div>`;
        }
        return "";
    }

    private renderWritePolicy(value: BehaviorWritePolicy): string {
        return `<label class="text-xs text-gray-500">When a value already exists${this.renderSelect(BEHAVIOR_WRITE_POLICY_DEFINITIONS, value, "data-behavior-action-write-policy")}</label>`;
    }

    private renderFieldSelect(
        selected: string,
        attribute: string,
        fields: CatalogField[] = this.fields,
    ): string {
        const options = fields.map((field) => `<option value="${escapeHtml(field.id)}" ${field.id === selected ? "selected" : ""}>${escapeHtml(field.label)}</option>`).join("");
        const placeholder = fields.length ? "Select field…" : "No compatible fields";
        return `<select class="select select-sm w-full" ${attribute} ${fields.length ? "" : "disabled"}><option value="">${placeholder}</option>${options}</select>`;
    }

    private renderSelect<TId extends string>(
        options: readonly BehaviorDefinition<TId>[],
        selected: TId,
        attributes: string,
    ): string {
        return `<select class="select select-sm w-full" ${attributes}>${options.map(({ id, label }) => `<option value="${id}" ${id === selected ? "selected" : ""}>${label}</option>`).join("")}</select>`;
    }

    private syncSummaries(): void {
        if (!this.rulesContainer) return;
        this.config.rules.forEach((rule) => {
            const element = this.rulesContainer?.querySelector<HTMLElement>(`[data-behavior-rule="${CSS.escape(rule.id)}"] [data-behavior-summary]`);
            if (!element) return;
            const actionLabels = rule.actions.map((action) => this.getActionSummary(action));
            const timing = rule.events.includes(BehaviorEvent.Initial)
                ? "when the form opens and when the field changes"
                : "when the field changes";
            element.textContent = `${rule.conditions.length ? `${rule.connector === BehaviorConnector.All ? "All" : "Any"} of ${rule.conditions.length} condition${rule.conditions.length === 1 ? "" : "s"}` : "Always"}: ${actionLabels.join(", ")} ${timing}.`;
        });
    }

    private getActionSummary(action: BehaviorActionConfig): string {
        if (action.type === BehaviorAction.COPY_VALUE.id) {
            const source = this.fields.find((field) => field.id === action.sourceField)?.label ?? "a source field";
            const target = this.fields.find((field) => field.id === action.targetField)?.label ?? "a target field";
            return `copy ${source} into ${target}`;
        }
        return BehaviorAction.get(action.type)?.label.toLowerCase() ?? "run action";
    }
}
