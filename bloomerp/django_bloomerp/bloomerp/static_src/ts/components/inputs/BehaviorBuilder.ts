import BaseComponent from "../BaseComponent";
import {
    BehaviorAction,
    BehaviorConnector,
    BehaviorEvent,
    BehaviorOperator,
    createBehaviorId,
    resolveBehaviorDefinitionId,
    type BehaviorActionConfig,
    type BehaviorActionEditorField,
    type BehaviorConfig,
    type BehaviorCondition,
    type BehaviorConditionValueEditor,
    type BehaviorDefinition,
    type BehaviorRule,
    type CatalogField,
} from "../behaviors/BehaviorDefinitions";

export type {
    BehaviorActionConfig,
    BehaviorConfig,
    BehaviorCondition,
    BehaviorRule,
} from "../behaviors/BehaviorDefinitions";

function parseJson<T>(value: string | undefined, fallback: T): T {
    if (!value) return fallback;
    try {
        return JSON.parse(value) as T;
    } catch {
        return fallback;
    }
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
    private config: BehaviorConfig = { rules: [] };
    private expandedRuleIds = new Set<string>();
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
        this.expandedRuleIds.clear();

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
        this.expandedRuleIds.clear();
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
            id: value.id || createBehaviorId("rule"),
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
        const field = this.fields.find(({ id }) => id === value.field)
            ?? this.getDefinitionContext().sourceField;
        const operators = BehaviorOperator.forField(field);
        const fallbackOperator = operators[0] ?? BehaviorOperator.EQUALS;
        return {
            id: value.id || createBehaviorId("condition"),
            field: field.id,
            operator: resolveBehaviorDefinitionId(
                value.operator,
                operators,
                fallbackOperator.id,
            ),
            value: value.value || "",
        };
    }

    private normalizeAction(value: Partial<BehaviorActionConfig>): BehaviorActionConfig {
        const type = resolveBehaviorDefinitionId(
            value.type,
            BehaviorAction.values(),
            BehaviorAction.SHOW_FIELD.id,
        );
        const definition = BehaviorAction.get(type) ?? BehaviorAction.SHOW_FIELD;
        return definition.normalize(
            { ...value, id: value.id || createBehaviorId("action"), type },
            this.getDefinitionContext(),
        );
    }

    private getDefinitionContext() {
        const sourceField = this.fields.find(({ id }) => id === this.sourceFieldId) ?? {
            id: this.sourceFieldId,
            label: this.sourceFieldLabel,
            name: this.sourceFieldLabel,
            fieldType: this.sourceFieldType,
        };
        return { sourceField, fields: this.fields };
    }

    private handleClick(event: Event): void {
        const button = (event.target as HTMLElement | null)?.closest<HTMLButtonElement>("button");
        if (!button || !this.element?.contains(button)) return;

        this.syncConfigFromDom();
        if (button.matches("[data-behavior-add-rule]")) {
            const rule = this.normalizeRule({ name: `Behavior ${this.config.rules.length + 1}` });
            this.config.rules.push(rule);
            this.expandedRuleIds.add(rule.id);
        } else {
            const ruleElement = button.closest<HTMLElement>("[data-behavior-rule]");
            const rule = this.config.rules.find((item) => item.id === ruleElement?.dataset.behaviorRule);
            if (!rule) return;

            if (button.matches("[data-behavior-delete-rule]")) {
                this.config.rules = this.config.rules.filter((item) => item.id !== rule.id);
                this.expandedRuleIds.delete(rule.id);
            } else if (button.matches("[data-behavior-toggle-rule]")) {
                if (this.expandedRuleIds.has(rule.id)) {
                    this.expandedRuleIds.delete(rule.id);
                } else {
                    this.expandedRuleIds.add(rule.id);
                }
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
            const id = element.dataset.behaviorRule ?? createBehaviorId("rule");
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
                conditions: Array.from(element.querySelectorAll<HTMLElement>("[data-behavior-condition]"))
                    .map((row) => this.normalizeCondition({
                        id: row.dataset.behaviorCondition ?? createBehaviorId("condition"),
                        field: this.valueOf(row, "[data-behavior-condition-field]"),
                        operator: this.valueOf(row, "[data-behavior-condition-operator]"),
                        value: this.valueOf(row, "[data-behavior-condition-value]"),
                    })),
                actions: Array.from(element.querySelectorAll<HTMLElement>("[data-behavior-action]")).map((row) => {
                    const actionId = row.dataset.behaviorAction ?? createBehaviorId("action");
                    const previousAction = previousActions.get(actionId) ?? this.normalizeAction({ id: actionId });
                    const action = {
                        ...previousAction,
                        id: actionId,
                        type: resolveBehaviorDefinitionId(
                            this.optionalValueOf(row, "[data-behavior-action-type]"),
                            BehaviorAction.values(),
                            previousAction.type,
                        ),
                    } as BehaviorActionConfig;
                    row.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(
                        "[data-behavior-action-config]",
                    ).forEach((control) => {
                        const key = control.dataset.behaviorActionConfig as keyof BehaviorActionConfig | undefined;
                        if (!key) return;
                        (action as unknown as Record<string, unknown>)[key] = control.value;
                    });
                    return this.normalizeAction(action);
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
        const isExpanded = this.expandedRuleIds.has(rule.id);
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
                        <button type="button" class="btn btn-ghost btn-xs" title="${isExpanded ? "Collapse" : "Expand"} behavior" aria-expanded="${isExpanded}" data-behavior-toggle-rule><i class="fa-solid fa-chevron-${isExpanded ? "up" : "down"}"></i></button>
                        <button type="button" class="btn btn-ghost btn-xs" title="Move up" ${index === 0 ? "disabled" : ""} data-behavior-move-rule="up"><i class="fa-solid fa-arrow-up"></i></button>
                        <button type="button" class="btn btn-ghost btn-xs" title="Move down" ${index === this.config.rules.length - 1 ? "disabled" : ""} data-behavior-move-rule="down"><i class="fa-solid fa-arrow-down"></i></button>
                        <button type="button" class="btn btn-ghost btn-xs text-danger-dark" title="Delete behavior" data-behavior-delete-rule><i class="fa-solid fa-trash"></i></button>
                    </div>
                </div>

                <div class="space-y-4 p-4 ${isExpanded ? "" : "hidden"}" data-behavior-rule-body>
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
        const field = this.fields.find(({ id }) => id === condition.field)
            ?? this.getDefinitionContext().sourceField;
        const operators = BehaviorOperator.forField(field);
        const operator = BehaviorOperator.get(condition.operator) ?? operators[0] ?? BehaviorOperator.EQUALS;
        return `
            <div class="grid gap-2 rounded-xl border border-gray-200 p-2 sm:grid-cols-[minmax(120px,1fr)_minmax(130px,1fr)_minmax(120px,1fr)_auto]" data-behavior-condition="${escapeHtml(condition.id)}">
                ${this.renderFieldSelect(condition.field, "data-behavior-condition-field data-behavior-rerender")}
                ${this.renderSelect(operators, operator.id, "data-behavior-condition-operator data-behavior-rerender")}
                ${this.renderConditionValue(condition, operator.valueEditor(field, condition))}
                <button type="button" class="btn btn-ghost btn-xs self-center text-gray-400 hover:text-danger-dark" title="Remove condition" data-behavior-remove-condition><i class="fa-solid fa-xmark"></i></button>
            </div>`;
    }

    private renderConditionValue(
        condition: BehaviorCondition,
        editor: BehaviorConditionValueEditor,
    ): string {
        if (editor.kind === "none") {
            return `<input type="hidden" value="" data-behavior-condition-value>`;
        }
        if (editor.kind === "boolean") {
            return this.renderSelect(
                [
                    { id: "true", label: "Yes" },
                    { id: "false", label: "No" },
                ],
                condition.value === "false" ? "false" : "true",
                "data-behavior-condition-value",
            );
        }
        const inputType = editor.kind === "number" ? "number" : editor.kind === "date" ? "date" : "text";
        const placeholder = editor.kind === "text" ? editor.placeholder ?? "Comparison value" : "";
        return `<input type="${inputType}" class="input input-sm" value="${escapeHtml(condition.value)}" placeholder="${escapeHtml(placeholder)}" data-behavior-condition-value>`;
    }

    private renderAction(action: BehaviorActionConfig): string {
        const definition = BehaviorAction.get(action.type) ?? BehaviorAction.SHOW_FIELD;
        const editor = definition.editor(action, this.getDefinitionContext());
        return `
            <div class="space-y-2 rounded-xl border border-gray-200 p-2" data-behavior-action="${escapeHtml(action.id)}">
                <div class="grid gap-2 sm:grid-cols-[minmax(160px,1fr)_auto]">
                    <label class="text-xs text-gray-500">Action${this.renderSelect(BehaviorAction.values(), action.type, "data-behavior-action-type data-behavior-rerender")}</label>
                    <button type="button" class="btn btn-ghost btn-xs self-center text-gray-400 hover:text-danger-dark" title="Remove action" data-behavior-remove-action><i class="fa-solid fa-xmark"></i></button>
                </div>
                <div class="grid gap-2 sm:grid-cols-2">
                    ${editor.map((field) => this.renderActionEditorField(action, field)).join("")}
                </div>
            </div>`;
    }

    private renderActionEditorField(
        action: BehaviorActionConfig,
        field: BehaviorActionEditorField,
    ): string {
        if (field.kind === "warning") {
            return `<p class="text-xs text-warning-dark sm:col-span-2"><i class="fa-solid fa-triangle-exclamation me-1"></i>${escapeHtml(field.message)}</p>`;
        }
        const value = String(action[field.key] ?? "");
        const attributes = `data-behavior-action-config="${field.key}"${field.rerender ? " data-behavior-rerender" : ""}`;
        let control = "";
        if (field.kind === "field") {
            control = this.renderFieldSelect(value, attributes, field.fields);
        } else if (field.kind === "select") {
            control = this.renderSelect(field.options, value, attributes);
        } else if (field.kind === "number") {
            control = `<input type="number" class="input input-sm w-full" value="${escapeHtml(value)}" ${field.min === undefined ? "" : `min="${field.min}"`} ${field.max === undefined ? "" : `max="${field.max}"`} ${attributes}>`;
        } else {
            control = `<input type="text" class="input input-sm w-full" value="${escapeHtml(value)}" placeholder="${escapeHtml(field.placeholder ?? "")}" ${attributes}>`;
        }
        return `<label class="text-xs text-gray-500">${escapeHtml(field.label)}${control}</label>`;
    }

    private renderFieldSelect(
        selected: string,
        attribute: string,
        fields: readonly CatalogField[] = this.fields,
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
        return BehaviorAction.get(action.type)?.summarize(
            action,
            this.getDefinitionContext(),
        ) ?? "run action";
    }
}
