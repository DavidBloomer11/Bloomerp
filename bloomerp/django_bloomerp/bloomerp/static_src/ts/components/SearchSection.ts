import BaseComponent from "./BaseComponent";

export default class SearchSection extends BaseComponent {
    private searchInput: HTMLInputElement | null = null;
    private searchItems: HTMLElement[] = [];
    private searchHandler: ((event: Event) => void) | null = null;
    private itemKeydownHandler: ((event: KeyboardEvent) => void) | null = null;
    private itemClickHandler: ((event: MouseEvent) => void) | null = null;
    private onItemClick: ((item: HTMLElement) => void) | null = null;

    public initialize(): void {
        if (!this.element) return;

        this.searchInput = this.element.querySelector<HTMLInputElement>('input[name="q"]');
        const itemSelector = this.element.dataset.containerQuerySelector;
        this.searchItems = itemSelector
            ? Array.from(this.element.querySelectorAll<HTMLElement>(itemSelector))
            : [];

        if (!this.searchInput) return;

        this.searchHandler = () => {
            this.applySearch(this.searchInput?.value || "");
        };
        this.itemKeydownHandler = (event: KeyboardEvent) => this.onItemKeydown(event);
        this.itemClickHandler = (event: MouseEvent) => {
            const target = event.target instanceof HTMLElement ? event.target : null;
            const item = itemSelector ? target?.closest<HTMLElement>(itemSelector) : null;
            if (item && this.element?.contains(item)) this.onItemClick?.(item);
        };

        this.searchInput.addEventListener("input", this.searchHandler);
        this.element.addEventListener("keydown", this.itemKeydownHandler);
        this.element.addEventListener("click", this.itemClickHandler);
        this.applySearch(this.searchInput.value || "");
    }

    public destroy(): void {
        if (this.searchInput && this.searchHandler) {
            this.searchInput.removeEventListener("input", this.searchHandler);
        }
        if (this.element && this.itemKeydownHandler) {
            this.element.removeEventListener("keydown", this.itemKeydownHandler);
        }
        if (this.element && this.itemClickHandler) {
            this.element.removeEventListener("click", this.itemClickHandler);
        }

        this.searchHandler = null;
        this.itemKeydownHandler = null;
        this.itemClickHandler = null;
        this.onItemClick = null;
        this.searchInput = null;
        this.searchItems = [];
    }

    private applySearch(rawQuery: string): void {
        const query = rawQuery.trim().toLowerCase();

        this.searchItems.forEach((item) => {
            const searchableText = this.getSearchableText(item);
            const matches = !query || searchableText.toLowerCase().includes(query);
            item.classList.toggle("hidden", !matches);
        });
    }

    private getSearchableText(item: HTMLElement): string {
        const attributeNames = this.element?.dataset.searchTextAttribute?.split(/\s+/).filter(Boolean) ?? [];
        const attributeText = attributeNames
            .map((attributeName) => item.getAttribute(attributeName) ?? "")
            .join(" ");
        return `${attributeText} ${item.textContent ?? ""}`;
    }

    private onItemKeydown(event: KeyboardEvent): void {
        const target = event.target instanceof HTMLElement ? event.target : null;
        if (!target) return;

        if (target === this.searchInput && event.key === "ArrowDown") {
            this.searchItems[0]?.focus();
            event.preventDefault();
            return;
        }

        const itemSelector = this.element?.dataset.containerQuerySelector;
        if (!itemSelector) return;
        const currentItem = this.searchItems.find((item) => item === target.closest(itemSelector));
        if (!currentItem) return;

        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            const currentIndex = this.searchItems.indexOf(currentItem);
            const nextIndex = event.key === "ArrowDown"
                ? Math.min(currentIndex + 1, this.searchItems.length - 1)
                : Math.max(currentIndex - 1, 0);
            this.searchItems[nextIndex]?.focus();
            event.preventDefault();
            return;
        }

        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            this.onItemClick?.(currentItem);
        }
    }

    /**
     * Focuses the search input field if it exists.
     */
    public focus(): void {
        this.searchInput?.focus();
    }

    /**
     * Sets a click handler for each search item.
     * @param handler the handler for what to do when the item is clicked
     */
    public setOnClickHandler(handler: (item: HTMLElement) => void): void {
        this.onItemClick = handler;
    }

}
