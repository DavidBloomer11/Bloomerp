import BaseComponent from "../BaseComponent";

export class PivotTable extends BaseComponent {
    public initialize(): void {
        if (!this.element) return;
        this.element.addEventListener('click', this.handleClick);
    }

    public override destroy(): void {
        this.element?.removeEventListener('click', this.handleClick);
    }

    private handleClick = (event: Event): void => {
        if (!this.element) return;

        const target = event.target as HTMLElement | null;
        const toggle = target?.closest<HTMLButtonElement>('[data-pivot-toggle]');
        if (!toggle || !this.element.contains(toggle)) return;

        const rowId = toggle.dataset.pivotToggle;
        if (!rowId) return;

        const expanded = toggle.getAttribute('aria-expanded') === 'true';
        this.setToggleState(toggle, !expanded);
        if (expanded) {
            this.collapseDescendants(rowId);
            return;
        }

        for (const row of this.getRows()) {
            if (row.dataset.pivotParentId === rowId) {
                row.hidden = false;
            }
        }
    };

    private collapseDescendants(parentId: string): void {
        if (!this.element) return;

        for (const row of this.getRows()) {
            if (row.dataset.pivotParentId !== parentId) continue;
            row.hidden = true;

            const rowId = row.dataset.pivotRowId;
            if (!rowId) continue;
            const toggle = row.querySelector<HTMLButtonElement>('[data-pivot-toggle]');
            if (toggle) this.setToggleState(toggle, false);
            this.collapseDescendants(rowId);
        }
    }

    private setToggleState(toggle: HTMLButtonElement, expanded: boolean): void {
        toggle.setAttribute('aria-expanded', String(expanded));
        toggle.querySelector('i')?.classList.toggle('rotate-90', expanded);
        toggle.title = expanded ? 'Collapse row' : 'Expand row';
    }

    private getRows(): HTMLElement[] {
        if (!this.element) return [];
        return Array.from(this.element.querySelectorAll<HTMLElement>('[data-pivot-row-id]'));
    }
}
