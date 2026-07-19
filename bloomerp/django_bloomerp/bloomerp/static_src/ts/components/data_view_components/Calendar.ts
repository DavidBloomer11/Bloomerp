import { BaseDataViewComponent } from "./BaseDataViewComponent";
import { BaseDataViewCell } from "./BaseDataViewCell";

type CalendarDirection = "up" | "down" | "left" | "right";

export class CalendarCell extends BaseDataViewCell {
    public override click(target?: string | HTMLElement): void {
        if (this.element?.hasAttribute("data-calendar-load-more")) {
            this.element.click();
            return;
        }
        super.click(target);
    }
}

export class Calendar extends BaseDataViewComponent {
    protected cellClass = CalendarCell;
    private viewMode = "week";
    private pageOffset = 0;

    public override initialize(): void {
        if (!this.element) return;
        super.initialize();

        this.viewMode = this.element.dataset.viewMode || "week";
        this.pageOffset = Number.parseInt(this.element.dataset.pageOffset || "0", 10) || 0;
        const controller = this.ensureAbortController();

        this.element.querySelectorAll<HTMLElement>("[data-calendar-nav]").forEach((button) => {
            button.addEventListener("click", () => {
                const action = button.dataset.calendarNav;
                if (action === "today") this.navigateTo(0);
                if (action === "prev") this.navigateTo(this.pageOffset - 1);
                if (action === "next") this.navigateTo(this.pageOffset + 1);
            }, { signal: controller.signal });
        });

        const modeSelect = this.element.querySelector<HTMLSelectElement>("[data-calendar-view-mode]");
        modeSelect?.addEventListener("change", () => {
            this.dataViewContainer?.filter({
                calendar_view_mode: modeSelect.value,
                calendar_page: 0,
            });
        }, { signal: controller.signal });

        this.element.addEventListener("keydown", (event) => {
            if (!event.metaKey || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            this.navigateTo(this.pageOffset + (event.key === "ArrowLeft" ? -1 : 1));
        }, { capture: true, signal: controller.signal });
    }

    public moveCellUp(): BaseDataViewCell {
        return this.move("up");
    }

    public moveCellDown(): BaseDataViewCell {
        return this.move("down");
    }

    public moveCellLeft(): BaseDataViewCell {
        return this.move("left");
    }

    public moveCellRight(): BaseDataViewCell {
        return this.move("right");
    }

    private navigateTo(pageOffset: number): void {
        this.dataViewContainer?.filter({ calendar_page: pageOffset });
    }

    private move(direction: CalendarDirection): BaseDataViewCell {
        if (!this.currentCell) this.initFocus();
        if (!this.currentCell) throw new Error("Calendar has no cells to navigate");

        const current = this.currentCell as CalendarCell;
        const unit = current.element?.dataset.calendarUnit;
        if (!unit) return current;

        const unitCells = this.cellsForUnit(unit);
        const itemIndex = unitCells.indexOf(current);
        const forward = direction === "down" || direction === "right";
        const cyclesItems = this.viewMode !== "week" || direction === "up" || direction === "down";
        if (cyclesItems && forward && itemIndex >= 0 && itemIndex < unitCells.length - 1) {
            return unitCells[itemIndex + 1];
        }
        if (cyclesItems && !forward && itemIndex > 0) {
            return unitCells[itemIndex - 1];
        }

        const sections = this.getUnitSections();
        const currentSection = sections.find((section) => section.dataset.calendarUnit === unit);
        if (!currentSection) return current;
        const targetSection = this.targetSection(sections, currentSection, direction);
        if (!targetSection) return current;
        const targetUnit = targetSection.dataset.calendarUnit;
        return targetUnit ? (this.cellsForUnit(targetUnit)[0] ?? current) : current;
    }

    private cellsForUnit(unit: string): CalendarCell[] {
        return this.getCells().filter((cell): cell is CalendarCell => (
            cell instanceof CalendarCell && cell.element?.dataset.calendarUnit === unit
        ));
    }

    private getUnitSections(): HTMLElement[] {
        if (!this.element) return [];
        return Array.from(this.element.querySelectorAll<HTMLElement>(
            "[data-calendar-unit][data-calendar-row][data-calendar-column]",
        ));
    }

    private targetSection(
        sections: HTMLElement[],
        current: HTMLElement,
        direction: CalendarDirection,
    ): HTMLElement | null {
        const currentIndex = sections.indexOf(current);
        if (currentIndex < 0) return null;

        if (this.viewMode === "month") {
            const delta = direction === "up" ? -7 : direction === "down" ? 7 : direction === "left" ? -1 : 1;
            return sections[currentIndex + delta] ?? null;
        }

        if (this.viewMode === "week") {
            const row = Number(current.dataset.calendarRow);
            const column = Number(current.dataset.calendarColumn);
            const targetRow = row + (direction === "up" ? -1 : direction === "down" ? 1 : 0);
            const targetColumn = column + (direction === "left" ? -1 : direction === "right" ? 1 : 0);
            return sections.find((section) => (
                Number(section.dataset.calendarRow) === targetRow
                && Number(section.dataset.calendarColumn) === targetColumn
            )) ?? null;
        }

        if (direction === "left" || direction === "right") return null;
        return sections[currentIndex + (direction === "up" ? -1 : 1)] ?? null;
    }
}
