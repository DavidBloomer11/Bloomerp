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
    type BehaviorRuntime,
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
        return { rules: [] };
    }
    const rules = (value as { rules?: unknown }).rules;
    return {
        rules: Array.isArray(rules) ? rules as BehaviorRule[] : [],
    };
}

function getComparableValue(value: DetailViewCellValue): string {
    return Array.isArray(value) ? value.join(",") : String(value ?? "");
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
            if (detail?.source === "behavior") return;
            const fieldId = detail?.cell?.applicationFieldId ?? detail?.cell?.getLayoutItemId();
            if (!fieldId) return;
            this.runFieldBehaviors(fieldId, BehaviorEvent.Change, 0, true);
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
                this.runFieldBehaviors(fieldId, BehaviorEvent.Initial, 0, false);
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

    private runFieldBehaviors(fieldId: string, event: BehaviorEvent, depth: number, trackChanges: boolean): void {
        if (depth > MAX_BEHAVIOR_DEPTH || this.activeFields.has(fieldId)) return;
        const source = this.getBehaviorSources().find((item) => item.fieldId === fieldId);
        if (!source) return;

        this.activeFields.add(fieldId);
        try {
            source.config.rules
                .filter((rule) => rule.enabled !== false && rule.events?.includes(event))
                .filter((rule) => this.matchesConditions(rule))
                .forEach((rule) => {
                    rule.actions?.forEach((action) => this.executeAction(fieldId, action, depth + 1, trackChanges));
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
        const definition = BehaviorOperator.get(condition.operator);
        return definition?.matches(condition, this.createRuntime(0, false)) ?? false;
    }

    private isFieldValueEmpty(fieldId: string, value: DetailViewCellValue): boolean {
        const relatedRows = this.getRelatedRows(fieldId);
        if (relatedRows !== null) return relatedRows.length === 0;
        if (Array.isArray(value)) return value.length === 0;
        return String(value ?? "").trim() === "";
    }

    private executeAction(
        sourceFieldId: string,
        action: BehaviorActionConfig,
        depth: number,
        trackChanges: boolean,
    ): void {
        const definition = BehaviorAction.get(action.type);
        if (!definition) {
            console.warn(`Unknown behavior action '${action.type}' was skipped.`);
            return;
        }
        definition.execute(
            action,
            this.createRuntime(depth, trackChanges),
            sourceFieldId,
        );
    }

    private createRuntime(depth: number, trackChanges: boolean): BehaviorRuntime {
        return {
            getFieldValue: (fieldId) => this.getFieldValue(fieldId),
            setFieldValue: (fieldId, value) => this.setFieldValue(fieldId, value, depth, trackChanges),
            setFieldVisibility: (fieldId, visible) => this.setFieldVisibility(fieldId, visible),
            setFieldEnabled: (fieldId, enabled) => this.setFieldEnabled(fieldId, enabled),
            setFieldRequired: (fieldId, required) => this.setFieldRequired(fieldId, required),
            getOneToManyField: (fieldId) => this.getOneToManyWidget(fieldId),
            isFieldEmpty: (fieldId) => this.isFieldValueEmpty(fieldId, this.getFieldValue(fieldId)),
            showMessage: (message, tone) => this.showBehaviorMessage(message, tone),
            warn: (message) => console.warn(message),
        };
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

    private setFieldValue(
        fieldId: string,
        value: DetailViewCellValue,
        depth: number,
        trackChanges: boolean,
    ): void {
        const cell = this.getFieldCell(fieldId);
        if (!cell) return;
        const previousValue = getComparableValue(cell.value);
        cell.setValue(value, trackChanges, "behavior");
        if (previousValue !== getComparableValue(cell.value)) {
            this.runFieldBehaviors(fieldId, BehaviorEvent.Change, depth, trackChanges);
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
        return this.getOneToManyWidget(fieldId)?.getRows() ?? null;
    }

    private getOneToManyWidget(fieldId: string): OneToManyFieldWidget | null {
        const field = this.getFieldElement(fieldId);
        const element = field?.querySelector<HTMLElement>('[bloomerp-component="one-to-many-field-widget"]');
        if (!element) return null;
        const component = getComponent(element);
        return component instanceof OneToManyFieldWidget ? component : null;
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
