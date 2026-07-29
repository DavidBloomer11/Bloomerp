import { BaseDataViewComponent } from "./BaseDataViewComponent";
import { BaseDataViewCell } from "./BaseDataViewCell";
import { MessageType } from "../UiMessage";
import { getComponent } from "../BaseComponent";
import { getCsrfToken } from "../../utils/cookies";
import showMessage from "../../utils/messages";

type CalendarDirection = "up" | "down" | "left" | "right";
type CalendarDateUpdate = { object_id: string; start_ms?: number; end_ms?: number };
type CalendarDragPayload = {
    object_id: string;
    start_ms: number;
    end_ms?: number;
};

export class CalendarCell extends BaseDataViewCell {
    private get section(): HTMLElement | null {
        if (this.element?.hasAttribute("data-calendar-event")) return this.element;
        return this.element?.closest<HTMLElement>("[data-calendar-unit-section]") ?? null;
    }

    public override highlight(): void {
        super.highlight();
        this.section?.classList.add("ring-2", "ring-inset", "ring-primary");
    }

    public override unhighlight(): void {
        super.unhighlight();
        this.section?.classList.remove("ring-2", "ring-inset", "ring-primary");
    }

    public override select(): void {
        super.select();
        this.section?.classList.add("bg-primary-50");
    }

    public override unselect(): void {
        super.unselect();
        this.section?.classList.remove("bg-primary-50");
    }

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
    private mutationInFlight = false;
    private activeGestureController: AbortController | null = null;

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
            const optionsSelect = this.dataViewContainer?.element?.querySelector<HTMLSelectElement>(
                '[data-display-options-form] [name="view_mode"]',
            );
            if (!optionsSelect) return;
            optionsSelect.value = modeSelect.value;
            optionsSelect.dispatchEvent(new Event("change", { bubbles: true }));
        }, { signal: controller.signal });

        this.element.addEventListener("pointerdown", this.onEventPointerDown, {
            signal: controller.signal,
        });
        this.element.addEventListener("dragstart", this.onCalendarDragStart, {
            signal: controller.signal,
        });
        this.element.addEventListener("dragend", this.clearDropHighlights, {
            signal: controller.signal,
        });
        this.element.addEventListener("dragover", this.onGridDragOver, {
            signal: controller.signal,
        });
        this.element.addEventListener("dragleave", this.onGridDragLeave, {
            signal: controller.signal,
        });
        this.element.addEventListener("drop", this.onGridDrop, {
            signal: controller.signal,
        });

        this.element.addEventListener("keydown", (event) => {
            if (!event.metaKey || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            this.navigateTo(this.pageOffset + (event.key === "ArrowLeft" ? -1 : 1));
        }, { capture: true, signal: controller.signal });
    }

    public override destroy(): void {
        this.activeGestureController?.abort();
        this.activeGestureController = null;
        super.destroy();
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

    protected override handleAltArrow(event: KeyboardEvent): boolean {
        if (!event.key.startsWith("Arrow")) return false;
        const direction = event.key.replace("Arrow", "").toLowerCase() as CalendarDirection;
        event.preventDefault();
        if (this.viewMode === "day" && (direction === "left" || direction === "right")) {
            return true;
        }
        if (!this.currentCell) this.initFocus();

        const selected = this.getSelectedCells().filter(
            (cell): cell is CalendarCell => cell instanceof CalendarCell,
        );
        const candidates = selected.length > 0
            ? selected
            : (this.currentCell instanceof CalendarCell ? [this.currentCell] : []);
        const itemsById = new Map<string, HTMLElement>();
        for (const cell of candidates) {
            const item = cell.element?.closest<HTMLElement>("[data-calendar-event]");
            const objectId = item?.dataset.objectId;
            if (item && objectId) itemsById.set(objectId, item);
        }
        if (itemsById.size === 0) return true;
        const items = Array.from(itemsById.values());
        if (!items.every((item) => this.canMoveEvent(item))) {
            showMessage("You do not have permission to move every selected record.", MessageType.ERROR);
            return true;
        }
        const updates = items
            .map((item) => this.buildMovedUpdate(item, direction))
            .filter((update): update is CalendarDateUpdate => update !== null);
        if (updates.length > 0) void this.persistDateUpdates(updates, true);
        return true;
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
        const cyclesItems = direction === "up"
            || direction === "down"
            || (this.viewMode !== "week" && this.viewMode !== "day");
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

    private canMoveEvent(item: HTMLElement): boolean {
        return item.dataset.calendarCanEditStart === "true"
            && (!this.hasEndField || item.dataset.calendarCanEditEnd === "true");
    }

    private get hasEndField(): boolean {
        return Boolean(this.element?.dataset.calendarEndFieldType);
    }

    private buildMovedUpdate(
        item: HTMLElement,
        direction: CalendarDirection,
    ): CalendarDateUpdate | null {
        const objectId = item.dataset.objectId;
        const start = Number(item.dataset.calendarStart);
        const end = Number(item.dataset.calendarEnd);
        if (!objectId || !Number.isFinite(start)) return null;
        const update: CalendarDateUpdate = {
            object_id: objectId,
            start_ms: this.shiftTimestamp(start, direction),
        };
        if (this.hasEndField && Number.isFinite(end)) {
            update.end_ms = this.shiftTimestamp(end, direction);
        }
        return update;
    }

    private shiftTimestamp(timestamp: number, direction: CalendarDirection): number {
        const shifted = new Date(timestamp);
        const amount = direction === "left" || direction === "up" ? -1 : 1;
        if (this.viewMode === "week" && (direction === "up" || direction === "down")) {
            shifted.setHours(shifted.getHours() + amount);
        } else if (this.viewMode === "day") {
            shifted.setHours(shifted.getHours() + amount);
        } else if (this.viewMode === "month" && (direction === "up" || direction === "down")) {
            shifted.setDate(shifted.getDate() + amount * 7);
        } else if (this.viewMode === "year") {
            shifted.setMonth(shifted.getMonth() + amount);
        } else {
            shifted.setDate(shifted.getDate() + amount);
        }
        return shifted.getTime();
    }

    private onEventPointerDown = (event: PointerEvent): void => {
        if (!this.element || event.button !== 0 || this.mutationInFlight) return;
        const target = event.target as HTMLElement | null;
        const edge = target?.closest<HTMLElement>("[data-calendar-resize-start], [data-calendar-resize-end]");
        const item = target?.closest<HTMLElement>("[data-calendar-event]");
        if (!item) return;
        const component = getComponent(item);
        if (component instanceof CalendarCell) {
            this.focus(component);
            this.collapseSelectionToActive();
            this.element.focus({ preventScroll: true });
        }
        if (!edge) return;
        const isStart = edge.hasAttribute("data-calendar-resize-start");
        if (isStart && item.dataset.calendarCanEditStart !== "true") return;
        if (!isStart && item.dataset.calendarCanEditEnd !== "true") return;

        event.preventDefault();
        event.stopPropagation();
        const objectId = item.dataset.objectId;
        const original = Number(
            isStart ? item.dataset.calendarStart : item.dataset.calendarEnd,
        );
        if (!objectId || !Number.isFinite(original)) return;

        const vertical = this.viewMode === "day"
            || (this.viewMode === "week" && item.dataset.calendarUnit?.includes("T"));
        const origin = vertical ? event.clientY : event.clientX;
        const unit = item.dataset.calendarUnit;
        const section = item.closest<HTMLElement>("[data-calendar-unit-section]")
            ?? (
                unit
                    ? this.element.querySelector<HTMLElement>(
                        `[data-calendar-unit-section][data-calendar-unit="${CSS.escape(unit)}"]`,
                    )
                    : null
            );
        const unitPixels = vertical
            ? 80
            : Math.max(section?.getBoundingClientRect().width ?? 100, 1);
        let units = 0;
        this.activeGestureController?.abort();
        const gesture = new AbortController();
        this.activeGestureController = gesture;

        window.addEventListener("pointermove", (moveEvent: PointerEvent) => {
            const position = vertical ? moveEvent.clientY : moveEvent.clientX;
            units = Math.round((position - origin) / unitPixels);
        }, { signal: gesture.signal });
        window.addEventListener("pointerup", () => {
            gesture.abort();
            if (this.activeGestureController === gesture) this.activeGestureController = null;
            if (units === 0) return;
            let value = original;
            const direction: CalendarDirection = units < 0
                ? (vertical ? "up" : "left")
                : (vertical ? "down" : "right");
            for (let index = 0; index < Math.abs(units); index += 1) {
                value = this.shiftTimestamp(value, direction);
            }
            const start = Number(item.dataset.calendarStart);
            const end = Number(item.dataset.calendarEnd);
            if ((isStart && Number.isFinite(end) && value >= end)
                || (!isStart && Number.isFinite(start) && value <= start)) return;
            void this.persistDateUpdates([{
                object_id: objectId,
                ...(isStart ? { start_ms: value } : { end_ms: value }),
            }], true);
        }, { signal: gesture.signal, once: true });
        window.addEventListener("pointercancel", () => {
            gesture.abort();
            if (this.activeGestureController === gesture) this.activeGestureController = null;
        }, { signal: gesture.signal, once: true });
    };

    private onCalendarDragStart = (event: DragEvent): void => {
        const target = event.target as HTMLElement | null;
        if (target?.closest("[data-calendar-resize-start], [data-calendar-resize-end]")) {
            event.preventDefault();
            return;
        }

        const scheduledItem = target?.closest<HTMLElement>("[data-calendar-event]");
        if (scheduledItem) {
            if (!event.dataTransfer || !this.canMoveEvent(scheduledItem)) {
                event.preventDefault();
                return;
            }
            const objectId = scheduledItem.dataset.objectId;
            const start = Number(scheduledItem.dataset.calendarStart);
            const end = Number(scheduledItem.dataset.calendarEnd);
            if (!objectId || !Number.isFinite(start)) {
                event.preventDefault();
                return;
            }
            const payload: CalendarDragPayload = {
                object_id: objectId,
                start_ms: start,
                ...(Number.isFinite(end) ? { end_ms: end } : {}),
            };
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData(
                "application/x-bloomerp-calendar-event",
                JSON.stringify(payload),
            );
            event.dataTransfer.setData("text/plain", objectId);
            return;
        }

        const item = target?.closest<HTMLElement>(
            "[data-calendar-unscheduled-event]",
        );
        if (!item || !event.dataTransfer || !this.canMoveEvent(item)) {
            event.preventDefault();
            return;
        }
        const objectId = item.dataset.objectId;
        if (!objectId) return;
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("application/x-bloomerp-calendar-object", objectId);
        event.dataTransfer.setData("text/plain", objectId);
    };

    private onGridDragOver = (event: DragEvent): void => {
        const dropzone = this.findDropzone(event);
        if (!dropzone || !event.dataTransfer) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        this.clearDropHighlights();
        dropzone.classList.add("ring-2", "ring-inset", "ring-primary");
    };

    private onGridDragLeave = (event: DragEvent): void => {
        const dropzone = this.findDropzone(event);
        if (!dropzone || dropzone.contains(event.relatedTarget as Node | null)) return;
        dropzone.classList.remove("ring-2", "ring-inset", "ring-primary");
    };

    private onGridDrop = (event: DragEvent): void => {
        if (!event.dataTransfer || this.mutationInFlight) return;
        const dropzone = this.findDropzone(event);
        const unit = dropzone?.dataset.calendarUnit;
        if (!dropzone || !unit) return;
        event.preventDefault();
        this.clearDropHighlights();
        const scheduledPayload = this.parseScheduledDrag(
            event.dataTransfer.getData("application/x-bloomerp-calendar-event"),
        );
        const start = this.timestampForUnit(unit);
        if (scheduledPayload && start !== null) {
            const update: CalendarDateUpdate = {
                object_id: scheduledPayload.object_id,
                start_ms: start,
            };
            if (this.hasEndField && scheduledPayload.end_ms !== undefined) {
                const duration = Math.max(
                    scheduledPayload.end_ms - scheduledPayload.start_ms,
                    1,
                );
                update.end_ms = start + duration;
            }
            void this.persistDateUpdates([update], true);
            return;
        }

        const objectId = event.dataTransfer.getData("application/x-bloomerp-calendar-object")
            || event.dataTransfer.getData("text/plain");
        if (!objectId || start === null) return;
        const update: CalendarDateUpdate = { object_id: objectId, start_ms: start };
        if (this.hasEndField) {
            const direction: CalendarDirection = (
                (this.viewMode === "day" || this.viewMode === "week") && unit.includes("T")
            ) ? "down" : "right";
            update.end_ms = this.shiftTimestamp(start, direction);
        }
        void this.persistDateUpdates([update], true);
    };

    private findDropzone(event: DragEvent): HTMLElement | null {
        const direct = (event.target as HTMLElement | null)?.closest<HTMLElement>(
            "[data-calendar-dropzone]",
        );
        if (direct) return direct;
        for (const element of document.elementsFromPoint(event.clientX, event.clientY)) {
            const dropzone = (element as HTMLElement).closest<HTMLElement>(
                "[data-calendar-dropzone]",
            );
            if (dropzone) return dropzone;
        }
        return null;
    }

    private parseScheduledDrag(rawPayload: string): CalendarDragPayload | null {
        if (!rawPayload) return null;
        try {
            const payload = JSON.parse(rawPayload) as Partial<CalendarDragPayload>;
            if (!payload.object_id || !Number.isFinite(payload.start_ms)) return null;
            if (payload.end_ms !== undefined && !Number.isFinite(payload.end_ms)) return null;
            return payload as CalendarDragPayload;
        } catch {
            return null;
        }
    }

    private timestampForUnit(unit: string): number | null {
        let value: Date;
        if (/^\d{4}-\d{2}$/.test(unit)) {
            value = new Date(`${unit}-01T00:00:00`);
        } else if (unit.includes("T")) {
            value = new Date(`${unit}:00:00`);
        } else {
            value = new Date(`${unit}T00:00:00`);
        }
        return Number.isNaN(value.getTime()) ? null : value.getTime();
    }

    private async persistDateUpdates(
        updates: CalendarDateUpdate[],
        refresh: boolean,
    ): Promise<void> {
        if (!this.element || this.mutationInFlight) return;
        const url = this.element.dataset.calendarUpdateUrl;
        if (!url) return;
        this.mutationInFlight = true;
        const csrfToken = getCsrfToken();
        try {
            const response = await fetch(url, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
                },
                body: JSON.stringify({ updates }),
            });
            if (!response.ok) {
                const message = response.status === 403
                    ? "You do not have permission to change these dates."
                    : "Unable to update the calendar dates.";
                showMessage(message, MessageType.ERROR);
                console.error("Failed to update calendar dates", await response.text());
                return;
            }
            if (refresh) this.dataViewContainer?.refresh();
        } catch (error) {
            showMessage("Unable to update the calendar dates.", MessageType.ERROR);
            console.error("Failed to update calendar dates", error);
        } finally {
            this.mutationInFlight = false;
        }
    }

    private clearDropHighlights = (): void => {
        if (!this.element) return;
        for (const dropzone of this.element.querySelectorAll<HTMLElement>(
            "[data-calendar-dropzone]",
        )) {
            dropzone.classList.remove("ring-2", "ring-inset", "ring-primary");
        }
    };
}
