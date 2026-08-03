import showMessage from "@/utils/messages";

import { MessageType } from "../UiMessage";
import { getComponent } from "../BaseComponent";
import { DetailViewCell, type DetailViewCellChangeDetail, type DetailViewCellValue } from "../detail_view_components/DetailViewCell";
import OneToManyFieldWidget from "../widgets/OneToManyFieldWidget";
import {
    BehaviorAction,
    BehaviorConnector,
    BehaviorEvent,
    BehaviorMessageTone,
    BehaviorOperator,
    type BehaviorActionConfig,
    type BehaviorCondition,
    type BehaviorConfig,
    type BehaviorRelatedRow,
    type BehaviorRule,
} from "./BehaviorDefinitions";

const MAX_BEHAVIOR_DEPTH = 20;

function parseJson<T>(value: string | undefined, fallback: T): T {
    if (!value) return fallback;
    try {
        return JSON.parse(value) as T;
    } catch {
        return fallback;
    }
}

function normalizeBehaviorConfig(value: unknown): BehaviorConfig {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return { version: 1, rules: [] };
    }
    const rules = (value as { rules?: unknown }).rules;
    return {
        version: 1,
        rules: Array.isArray(rules) ? rules as BehaviorRule[] : [],
    };
}

function getComparableValue(value: DetailViewCellValue): string {
    return Array.isArray(value) ? value.join(",") : String(value ?? "");
}

function compareValues(left: string, right: string): number {
    const leftNumber = Number(left);
    const rightNumber = Number(right);
    if (left.trim() !== "" && right.trim() !== "" && Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
        return leftNumber - rightNumber;
    }
    return left.localeCompare(right, undefined, { numeric: true, sensitivity: "base" });
}

function readRows(widget: OneToManyFieldWidget): BehaviorRelatedRow[] {
    return parseJson<BehaviorRelatedRow[]>(String(widget.getValue() ?? "[]"), []);
}

function findDateFieldName(widgetElement: HTMLElement): string | null {
    const template = widgetElement.querySelector<HTMLTemplateElement>("[data-one-to-many-row-template]");
    const dateInput = template?.content.querySelector<HTMLInputElement>('input[type="date"][name]');
    if (!dateInput) return null;
    const parts = dateInput.name.replace("__prefix__", "0").split("__");
    return parts.length >= 3 ? parts.slice(2).join("__") : null;
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

export default class FormBehaviorRuntime {
    private root: HTMLElement;
    private activeFields = new Set<string>();
    private initialRuleSignatures = new Map<string, string>();
    private changeHandler: ((event: Event) => void) | null = null;
    private initialRunToken = 0;

    public constructor(root: HTMLElement) {
        this.root = root;
    }

    public initialize(): void {
        this.changeHandler = (event: Event) => {
            const detail = (event as CustomEvent<DetailViewCellChangeDetail>).detail;
            const fieldId = detail?.cell?.applicationFieldId ?? detail?.cell?.getLayoutItemId();
            if (!fieldId) return;
            this.runFieldBehaviors(fieldId, BehaviorEvent.Change, 0);
        };
        this.root.addEventListener(DetailViewCell.changeEventName, this.changeHandler);
        this.scheduleInitialRun();
    }

    public destroy(): void {
        if (this.changeHandler) {
            this.root.removeEventListener(DetailViewCell.changeEventName, this.changeHandler);
        }
        this.changeHandler = null;
        this.initialRunToken += 1;
        this.activeFields.clear();
        this.initialRuleSignatures.clear();
    }

    public refresh(): void {
        this.scheduleInitialRun();
    }

    private scheduleInitialRun(): void {
        const token = ++this.initialRunToken;
        queueMicrotask(() => {
            if (token !== this.initialRunToken || !this.root.isConnected) return;
            this.getBehaviorSources().forEach(({ fieldId, config }) => {
                const signature = JSON.stringify(config.rules);
                if (this.initialRuleSignatures.get(fieldId) === signature) return;
                this.initialRuleSignatures.set(fieldId, signature);
                this.runFieldBehaviors(fieldId, BehaviorEvent.Initial, 0);
            });
        });
    }

    private getBehaviorSources(): Array<{ fieldId: string; config: BehaviorConfig }> {
        return Array.from(this.root.querySelectorAll<HTMLElement>("[data-layout-item-id][data-layout-item-config]"))
            .map((element) => {
                const fieldId = element.dataset.applicationFieldId ?? element.dataset.layoutItemId ?? "";
                const itemConfig = parseJson<Record<string, unknown>>(element.dataset.layoutItemConfig, {});
                const behaviorConfig = normalizeBehaviorConfig(itemConfig.behaviors);
                return { fieldId, config: behaviorConfig };
            })
            .filter(({ fieldId, config }) => Boolean(fieldId) && config.rules.length > 0);
    }

    private runFieldBehaviors(fieldId: string, event: BehaviorEvent, depth: number): void {
        if (depth > MAX_BEHAVIOR_DEPTH || this.activeFields.has(fieldId)) return;
        const source = this.getBehaviorSources().find((item) => item.fieldId === fieldId);
        if (!source) return;

        this.activeFields.add(fieldId);
        try {
            source.config.rules
                .filter((rule) => rule.enabled !== false && rule.events?.includes(event))
                .filter((rule) => this.matchesConditions(rule))
                .forEach((rule) => {
                    rule.actions?.forEach((action) => this.executeAction(fieldId, action, depth + 1));
                });
        } finally {
            this.activeFields.delete(fieldId);
        }
    }

    private matchesConditions(rule: BehaviorRule): boolean {
        const conditions = Array.isArray(rule.conditions) ? rule.conditions : [];
        if (!conditions.length) return true;
        const results = conditions.map((condition) => this.matchesCondition(condition));
        return rule.connector === BehaviorConnector.Any ? results.some(Boolean) : results.every(Boolean);
    }

    private matchesCondition(condition: BehaviorCondition): boolean {
        const actual = getComparableValue(this.getFieldValue(condition.field));
        const expected = condition.value ?? "";
        switch (condition.operator) {
            case BehaviorOperator.EQUALS.id:
                return actual === expected;
            case BehaviorOperator.NOT_EQUALS.id:
                return actual !== expected;
            case BehaviorOperator.IS_EMPTY.id:
                return actual.trim() === "";
            case BehaviorOperator.IS_NOT_EMPTY.id:
                return actual.trim() !== "";
            case BehaviorOperator.CONTAINS.id:
                return actual.toLocaleLowerCase().includes(expected.toLocaleLowerCase());
            case BehaviorOperator.GREATER_THAN.id:
                return compareValues(actual, expected) > 0;
            case BehaviorOperator.LESS_THAN.id:
                return compareValues(actual, expected) < 0;
            default:
                return false;
        }
    }

    private executeAction(sourceFieldId: string, action: BehaviorActionConfig, depth: number): void {
        const definition = BehaviorAction.get(action.type);
        if (!definition) {
            console.warn(`Unknown behavior action '${action.type}' was skipped.`);
            return;
        }
        definition.execute({
            action,
            sourceFieldId,
            getFieldValue: (fieldId) => this.getFieldValue(fieldId),
            setFieldValue: (fieldId, value) => this.setFieldValue(fieldId, value, depth),
            setFieldVisibility: (fieldId, visible) => this.setFieldVisibility(fieldId, visible),
            setFieldEnabled: (fieldId, enabled) => this.setFieldEnabled(fieldId, enabled),
            setFieldRequired: (fieldId, required) => this.setFieldRequired(fieldId, required),
            getRelatedRows: (fieldId) => this.getRelatedRows(fieldId),
            getRelatedDateField: (fieldId) => this.getRelatedDateField(fieldId),
            setRelatedRows: (fieldId, rows) => this.setRelatedRows(fieldId, rows),
            showMessage: (message, tone) => this.showBehaviorMessage(message, tone),
            warn: (message) => console.warn(message),
        });
    }

    private getFieldElement(fieldId: string): HTMLElement | null {
        if (!fieldId) return null;
        const escapedId = CSS.escape(fieldId);
        return this.root.querySelector<HTMLElement>(
            `[data-application-field-id="${escapedId}"], [data-layout-item-id="${escapedId}"]`,
        );
    }

    private getFieldCell(fieldId: string): DetailViewCell | null {
        const element = this.getFieldElement(fieldId);
        if (!element) return null;
        const component = getComponent(element);
        return component instanceof DetailViewCell ? component : null;
    }

    private getFieldValue(fieldId: string): DetailViewCellValue {
        return this.getFieldCell(fieldId)?.value ?? "";
    }

    private setFieldValue(fieldId: string, value: DetailViewCellValue, depth: number): void {
        const cell = this.getFieldCell(fieldId);
        if (!cell) return;
        const previousValue = getComparableValue(cell.value);
        cell.restoreValue(value);
        if (previousValue !== getComparableValue(cell.value)) {
            this.runFieldBehaviors(fieldId, BehaviorEvent.Change, depth);
        }
    }

    private setFieldVisibility(fieldId: string, visible: boolean): void {
        const element = this.getFieldElement(fieldId);
        if (!element) return;
        element.classList.toggle("hidden", !visible);
        element.toggleAttribute("data-behavior-hidden", !visible);
        element.setAttribute("aria-hidden", visible ? "false" : "true");
    }

    private setFieldEnabled(fieldId: string, enabled: boolean): void {
        const body = this.getFieldElement(fieldId)?.querySelector<HTMLElement>("[data-layout-item-body]");
        body?.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | HTMLButtonElement>(
            "input:not([type=hidden]), textarea, select, button",
        ).forEach((control) => {
            control.disabled = !enabled;
        });
    }

    private setFieldRequired(fieldId: string, required: boolean): void {
        const element = this.getFieldElement(fieldId);
        if (!element) return;
        const controls = element.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
            "[data-layout-item-body] input:not([type=hidden]), [data-layout-item-body] textarea, [data-layout-item-body] select",
        );
        controls.forEach((control) => {
            control.required = required;
            control.setAttribute("aria-required", required ? "true" : "false");
        });
        element.dataset.required = String(required);
        const label = element.querySelector<HTMLElement>("[data-detail-label]");
        const marker = label?.querySelector<HTMLElement>("[data-behavior-required-marker]");
        if (required && label && !marker) {
            label.insertAdjacentHTML(
                "beforeend",
                ' <span class="text-danger-dark" aria-hidden="true" data-behavior-required-marker>*</span>',
            );
        } else if (!required) {
            marker?.remove();
        }
    }

    private getRelatedRows(fieldId: string): BehaviorRelatedRow[] | null {
        const relatedField = this.getOneToManyWidget(fieldId);
        return relatedField ? readRows(relatedField.widget) : null;
    }

    private getRelatedDateField(fieldId: string): string | null {
        const relatedField = this.getOneToManyWidget(fieldId);
        return relatedField ? findDateFieldName(relatedField.element) : null;
    }

    private setRelatedRows(fieldId: string, rows: BehaviorRelatedRow[]): void {
        this.getOneToManyWidget(fieldId)?.widget.setValue(rows, true);
    }

    private getOneToManyWidget(fieldId: string): { element: HTMLElement; widget: OneToManyFieldWidget } | null {
        const field = this.getFieldElement(fieldId);
        const element = field?.querySelector<HTMLElement>('[bloomerp-component="one-to-many-field-widget"]');
        if (!element) return null;
        const component = getComponent(element);
        return component instanceof OneToManyFieldWidget ? { element, widget: component } : null;
    }

    private showBehaviorMessage(message: string, tone: BehaviorMessageTone): void {
        const messageTypes: Record<BehaviorMessageTone, MessageType> = {
            [BehaviorMessageTone.Error]: MessageType.ERROR,
            [BehaviorMessageTone.Warning]: MessageType.WARNING,
            [BehaviorMessageTone.Info]: MessageType.INFO,
        };
        showMessage(escapeHtml(message), messageTypes[tone] ?? MessageType.INFO);
    }
}
