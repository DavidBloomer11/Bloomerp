import { attachObjectPreviewTooltip, hideObjectPreviewTooltip } from "@/utils/objectPreviewTooltip";
import { BaseWidget, type BaseWidgetSerializableState } from "./BaseWidget";

type GenericForeignKeyValue = {
    contentTypeId: string;
    objectId: string;
    label: string;
    url: string;
};

type GenericForeignKeySerializableState = BaseWidgetSerializableState & GenericForeignKeyValue & {
    inputValue: string;
};

export default class GenericForeignKeyWidget extends BaseWidget {
    private input: HTMLInputElement | null = null;
    private dropdown: HTMLElement | null = null;
    private resultsList: HTMLUListElement | null = null;
    private selectedContainer: HTMLElement | null = null;
    private contentTypeInput: HTMLInputElement | null = null;
    private objectIdInput: HTMLInputElement | null = null;
    private debounceTimer: number | null = null;
    private outsideClickHandler: ((event: MouseEvent) => void) | null = null;
    private inputHandler: (() => void) | null = null;
    private resultClickHandler: ((event: Event) => void) | null = null;
    private previewCleanup: (() => void) | null = null;
    private isDisabled = false;

    public initialize(): void {
        if (!this.element) return;

        const contentTypeFieldName = this.element.dataset.contentTypeFieldName || "";
        const objectIdFieldName = this.element.dataset.objectIdFieldName || "";
        this.input = this.element.querySelector('input[type="text"]');
        this.dropdown = this.element.querySelector(".generic-foreign-key-dropdown");
        this.resultsList = this.element.querySelector(".generic-foreign-key-results");
        this.selectedContainer = this.element.querySelector(".generic-foreign-key-selected");
        this.contentTypeInput = this.element.querySelector(`input[type="hidden"][name="${contentTypeFieldName}"]`);
        this.objectIdInput = this.element.querySelector(`input[type="hidden"][name="${objectIdFieldName}"]`);
        this.isDisabled = this.element.dataset.disabled === "true";

        if (!this.input || !this.dropdown || !this.resultsList || !this.selectedContainer || !this.contentTypeInput || !this.objectIdInput) {
            return;
        }

        this.renderSelectedState();
        if (this.isDisabled) return;

        this.inputHandler = () => this.onInput();
        this.resultClickHandler = (event: Event) => this.onResultClick(event);
        this.outsideClickHandler = (event: MouseEvent) => {
            if (!this.element.contains(event.target as Node)) this.hideDropdown();
        };
        this.input.addEventListener("input", this.inputHandler);
        this.resultsList.addEventListener("click", this.resultClickHandler);
        document.addEventListener("click", this.outsideClickHandler);
    }

    public destroy(): void {
        if (this.input && this.inputHandler) this.input.removeEventListener("input", this.inputHandler);
        if (this.resultsList && this.resultClickHandler) this.resultsList.removeEventListener("click", this.resultClickHandler);
        if (this.outsideClickHandler) document.removeEventListener("click", this.outsideClickHandler);
        if (this.debounceTimer) window.clearTimeout(this.debounceTimer);
        this.cleanupPreview();
    }

    private onInput(): void {
        if (!this.input) return;
        const query = this.input.value.trim();
        if (this.debounceTimer) window.clearTimeout(this.debounceTimer);
        if (
            this.objectIdInput?.value
            && query !== (this.element.dataset.selectedLabel || "").trim()
        ) {
            this.clearSelection(false);
            this.input.value = query;
        }
        if (!query) {
            this.clearSelection(false);
            this.hideDropdown();
            return;
        }

        this.debounceTimer = window.setTimeout(() => this.fetchResults(query), 250);
    }

    private async fetchResults(query: string): Promise<void> {
        const searchUrl = this.element.dataset.searchUrl;
        if (!searchUrl) return;

        try {
            const separator = searchUrl.includes("?") ? "&" : "?";
            const response = await fetch(`${searchUrl}${separator}q=${encodeURIComponent(query)}`, { credentials: "same-origin" });
            if (!response.ok) return;
            const data = await response.json();
            this.renderResults(data.objects || []);
        } catch (error) {
            console.error("GenericForeignKeyWidget search error", error);
        }
    }

    private renderResults(objects: Array<{ content_type_id: string; object_id: string; label: string; model_label: string; detail_url?: string }>): void {
        if (!this.resultsList || !this.dropdown) return;
        this.resultsList.innerHTML = "";

        if (!objects.length) {
            const empty = document.createElement("li");
            empty.className = "px-3 py-2 text-gray-500";
            empty.textContent = "No results";
            this.resultsList.appendChild(empty);
        } else {
            objects.forEach((object) => {
                const item = document.createElement("li");
                item.className = "cursor-pointer px-3 py-2 hover:bg-gray-50";
                item.dataset.contentTypeId = String(object.content_type_id);
                item.dataset.objectId = String(object.object_id);
                item.dataset.label = object.label;
                item.dataset.url = object.detail_url || "";

                const label = document.createElement("div");
                label.className = "truncate text-gray-900";
                label.textContent = object.label;
                const modelLabel = document.createElement("div");
                modelLabel.className = "text-xs text-gray-500";
                modelLabel.textContent = object.model_label;
                item.append(label, modelLabel);
                this.resultsList?.appendChild(item);
            });
        }
        this.dropdown.classList.remove("hidden");
    }

    private onResultClick(event: Event): void {
        const item = (event.target as HTMLElement).closest("li[data-content-type-id]") as HTMLElement | null;
        if (!item) return;
        this.setSelection({
            contentTypeId: item.dataset.contentTypeId || "",
            objectId: item.dataset.objectId || "",
            label: item.dataset.label || item.dataset.objectId || "",
            url: item.dataset.url || "",
        });
    }

    private setSelection(value: GenericForeignKeyValue, emitChange = true): void {
        const previousValue = this.getValue();
        if (!this.contentTypeInput || !this.objectIdInput || !this.input) return;
        this.contentTypeInput.value = value.contentTypeId;
        this.objectIdInput.value = value.objectId;
        this.element.dataset.selectedLabel = value.label;
        this.element.dataset.selectedUrl = value.url;
        this.input.value = value.label;
        this.renderSelectedState();
        this.hideDropdown();
        if (emitChange && JSON.stringify(previousValue) !== JSON.stringify(this.getValue())) this.onChange();
    }

    private clearSelection(emitChange = true): void {
        this.setSelection({ contentTypeId: "", objectId: "", label: "", url: "" }, emitChange);
    }

    private renderSelectedState(): void {
        if (!this.selectedContainer || !this.contentTypeInput || !this.objectIdInput) return;
        this.cleanupPreview();
        this.selectedContainer.innerHTML = "";
        if (!this.contentTypeInput.value || !this.objectIdInput.value) return;

        const badge = document.createElement("span");
        badge.className = "inline-flex items-center gap-1 rounded-full bg-primary px-2 py-1 text-xs text-white";
        const label = this.element.dataset.selectedLabel || this.objectIdInput.value;
        const url = this.element.dataset.selectedUrl || "";
        const content = document.createElement(url ? "a" : "span");
        content.className = "max-w-56 truncate px-1";
        content.textContent = label;
        if (url) content.setAttribute("href", url);
        badge.appendChild(content);

        if (!this.isDisabled) {
            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "rounded-full px-1 leading-none hover:bg-white/20";
            remove.setAttribute("aria-label", `Remove ${label}`);
            remove.textContent = "×";
            remove.addEventListener("click", (event) => {
                event.preventDefault();
                this.clearSelection();
            });
            badge.appendChild(remove);
        }

        this.selectedContainer.appendChild(badge);
        this.previewCleanup = attachObjectPreviewTooltip({
            element: content,
            objectId: this.objectIdInput.value,
            contentTypeId: this.contentTypeInput.value,
        });
    }

    private cleanupPreview(): void {
        this.previewCleanup?.();
        this.previewCleanup = null;
        hideObjectPreviewTooltip();
    }

    private hideDropdown(): void {
        this.dropdown?.classList.add("hidden");
    }

    public getValue(): GenericForeignKeyValue {
        return {
            contentTypeId: this.contentTypeInput?.value || "",
            objectId: this.objectIdInput?.value || "",
            label: this.element.dataset.selectedLabel || "",
            url: this.element.dataset.selectedUrl || "",
        };
    }

    public setValue(value: unknown, emitChange = false): void {
        if (!value || typeof value !== "object") return;
        const nextValue = value as Partial<GenericForeignKeyValue>;
        this.setSelection({
            contentTypeId: String(nextValue.contentTypeId || ""),
            objectId: String(nextValue.objectId || ""),
            label: String(nextValue.label || nextValue.objectId || ""),
            url: String(nextValue.url || ""),
        }, emitChange);
    }

    public override getSerializableState(): GenericForeignKeySerializableState {
        return { ...this.getValue(), value: this.getValue(), inputValue: this.input?.value || "" };
    }

    public override setSerializableState(state: BaseWidgetSerializableState, emitChange = false): void {
        const nextState = state as GenericForeignKeySerializableState;
        this.setValue(nextState, emitChange);
        if (this.input) this.input.value = nextState.inputValue || nextState.label || "";
    }
}
