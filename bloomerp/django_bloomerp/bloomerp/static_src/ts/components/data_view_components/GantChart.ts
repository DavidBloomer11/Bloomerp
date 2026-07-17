import { componentIdentifier, getComponent } from "../BaseComponent";
import { BaseDataViewCell } from "./BaseDataViewCell";
import { BaseDataViewComponent } from "./BaseDataViewComponent";

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;
const MONTH = 30.4375 * DAY;
const SIDEBAR_WIDTH = 320;

type TickUnit = 'month' | 'week' | 'day' | 'hour';

interface ZoomLevel {
    pixelsPerMs: number;
    tickUnit: TickUnit;
    paddingMs: number;
}

const ZOOM_LEVELS: ZoomLevel[] = [
    { pixelsPerMs: 72 / MONTH, tickUnit: 'month', paddingMs: 2 * MONTH },
    { pixelsPerMs: 56 / WEEK, tickUnit: 'week', paddingMs: 3 * WEEK },
    { pixelsPerMs: 36 / DAY, tickUnit: 'day', paddingMs: 4 * DAY },
    { pixelsPerMs: 104 / DAY, tickUnit: 'day', paddingMs: 2 * DAY },
    { pixelsPerMs: 84 / HOUR, tickUnit: 'hour', paddingMs: 6 * HOUR },
];

export class GantChartItem extends BaseDataViewCell {
    public initialize(): void {
        super.initialize();
    }
}

export class GantChart extends BaseDataViewComponent {
    protected cellClass = GantChartItem;
    private resizeObserver: ResizeObserver | null = null;
    private drawFrame: number | null = null;
    private zoomIndex = 0;
    private rangeStart = 0;
    private rangeEnd = 0;
    private canvasWidth = 0;
    private dataStart = 0;
    private dataEnd = 0;

    public initialize(): void {
        if (!this.element) return;

        super.initialize();
        this.dataStart = Number(this.element.dataset.gantStart);
        this.dataEnd = Number(this.element.dataset.gantEnd);
        if (!Number.isFinite(this.dataStart) || !Number.isFinite(this.dataEnd)) return;

        const abortController = this.ensureAbortController();
        const zoomSelect = this.element.querySelector<HTMLSelectElement>('[data-gant-zoom]');
        const savedZoom = this.readSavedZoom();
        this.zoomIndex = savedZoom ?? this.getAutomaticZoom();
        if (zoomSelect) zoomSelect.value = String(this.zoomIndex);

        zoomSelect?.addEventListener('change', this.onZoomChange, { signal: abortController.signal });
        this.element.querySelector('[data-gant-zoom-out]')?.addEventListener(
            'click',
            () => this.changeZoom(-1),
            { signal: abortController.signal },
        );
        this.element.querySelector('[data-gant-zoom-in]')?.addEventListener(
            'click',
            () => this.changeZoom(1),
            { signal: abortController.signal },
        );
        this.element.querySelector('[data-gant-today]')?.addEventListener(
            'click',
            () => this.scrollToTimestamp(Date.now()),
            { signal: abortController.signal },
        );
        this.element.addEventListener('scroll', this.updateVisibleRange, {
            signal: abortController.signal,
            passive: true,
        });
        this.element.addEventListener('htmx:afterSwap', this.handleHtmxSwap, {
            signal: abortController.signal,
        });
        window.addEventListener('resize', this.onResize, { signal: abortController.signal });

        this.resizeObserver = new ResizeObserver(this.onResize);
        this.resizeObserver.observe(this.element);
        this.applyZoom(false);
        window.requestAnimationFrame(() => {
            const initialTarget = Date.now() >= this.rangeStart && Date.now() <= this.rangeEnd
                ? Date.now()
                : this.dataStart;
            this.scrollToTimestamp(initialTarget);
        });
    }

    public override destroy(): void {
        if (this.drawFrame !== null) {
            window.cancelAnimationFrame(this.drawFrame);
            this.drawFrame = null;
        }
        this.resizeObserver?.disconnect();
        this.resizeObserver = null;
        super.destroy();
    }

    public moveCellUp(): BaseDataViewCell {
        return this.getAdjacentItem(-1) ?? this.currentCell!;
    }

    public moveCellDown(): BaseDataViewCell {
        return this.getAdjacentItem(1) ?? this.currentCell!;
    }

    public moveCellRight(): BaseDataViewCell {
        return this.currentCell!;
    }

    public moveCellLeft(): BaseDataViewCell {
        return this.currentCell!;
    }

    private getAutomaticZoom(): number {
        const duration = Math.max(this.dataEnd - this.dataStart, HOUR);
        for (let index = ZOOM_LEVELS.length - 1; index >= 0; index -= 1) {
            if (duration * ZOOM_LEVELS[index].pixelsPerMs <= 2400) return index;
        }
        return 0;
    }

    private readSavedZoom(): number | null {
        try {
            const storedValue = window.localStorage.getItem(`bloomerp-gant-zoom-${this.contentTypeId}`);
            if (storedValue === null) return null;
            const value = Number(storedValue);
            return Number.isInteger(value) && value >= 0 && value < ZOOM_LEVELS.length ? value : null;
        } catch {
            return null;
        }
    }

    private saveZoom(): void {
        try {
            window.localStorage.setItem(`bloomerp-gant-zoom-${this.contentTypeId}`, String(this.zoomIndex));
        } catch {
            // Storage may be disabled; zoom still works for the current view.
        }
    }

    private onZoomChange = (event: Event): void => {
        const value = Number((event.currentTarget as HTMLSelectElement).value);
        if (!Number.isInteger(value) || value < 0 || value >= ZOOM_LEVELS.length) return;
        this.zoomIndex = value;
        this.saveZoom();
        this.applyZoom(true);
    };

    private changeZoom(delta: number): void {
        const nextZoom = Math.max(0, Math.min(ZOOM_LEVELS.length - 1, this.zoomIndex + delta));
        if (nextZoom === this.zoomIndex) return;
        this.zoomIndex = nextZoom;
        const zoomSelect = this.element?.querySelector<HTMLSelectElement>('[data-gant-zoom]');
        if (zoomSelect) zoomSelect.value = String(this.zoomIndex);
        this.saveZoom();
        this.applyZoom(true);
    }

    private applyZoom(preserveCenter: boolean): void {
        if (!this.element) return;

        const oldCenter = preserveCenter && this.canvasWidth > 0
            ? this.rangeStart + (
                (this.element.scrollLeft + (this.element.clientWidth - SIDEBAR_WIDTH) / 2)
                / this.canvasWidth
            ) * (this.rangeEnd - this.rangeStart)
            : null;
        const zoom = ZOOM_LEVELS[this.zoomIndex];
        this.rangeStart = this.dataStart - zoom.paddingMs;
        this.rangeEnd = Math.max(this.dataEnd + zoom.paddingMs, this.rangeStart + zoom.paddingMs * 2);
        this.canvasWidth = Math.max(
            (this.rangeEnd - this.rangeStart) * zoom.pixelsPerMs,
            Math.max(this.element.clientWidth - SIDEBAR_WIDTH, 640),
        );

        for (const layout of this.element.querySelectorAll<HTMLElement>('[data-gant-layout]')) {
            layout.style.gridTemplateColumns = `${SIDEBAR_WIDTH}px ${this.canvasWidth}px`;
            layout.style.width = `${SIDEBAR_WIDTH + this.canvasWidth}px`;
        }

        const grid = this.element.querySelector<HTMLElement>('[data-gant-grid]');
        if (grid) {
            grid.style.left = `${SIDEBAR_WIDTH}px`;
            grid.style.width = `${this.canvasWidth}px`;
        }

        for (const item of this.element.querySelectorAll<HTMLElement>('[data-gant-item]')) {
            const start = Number(item.dataset.start);
            const end = Number(item.dataset.end);
            if (!Number.isFinite(start) || !Number.isFinite(end)) continue;
            const left = this.positionForTimestamp(start);
            const width = Math.max(this.positionForTimestamp(end) - left, 4);
            item.style.left = `${left}px`;
            item.style.width = `${width}px`;
        }

        this.renderAxis();
        if (oldCenter !== null) this.scrollToTimestamp(oldCenter);
        this.updateVisibleRange();
        this.scheduleDependencyDraw();
    }

    private renderAxis(): void {
        if (!this.element) return;
        const header = this.element.querySelector<HTMLElement>('[data-gant-timeline-header]');
        const grid = this.element.querySelector<HTMLElement>('[data-gant-grid]');
        if (!header || !grid) return;
        header.replaceChildren();
        grid.replaceChildren();

        const zoom = ZOOM_LEVELS[this.zoomIndex];
        const roughCount = Math.ceil((this.rangeEnd - this.rangeStart) / this.tickDuration(zoom.tickUnit));
        const tickMultiplier = Math.max(1, Math.ceil(roughCount / 400));
        let tick = this.floorTick(new Date(this.rangeStart), zoom.tickUnit);
        let previousMajor = '';

        while (tick.getTime() <= this.rangeEnd) {
            const timestamp = tick.getTime();
            if (timestamp >= this.rangeStart) {
                const left = this.positionForTimestamp(timestamp);
                const labels = this.tickLabels(tick, zoom.tickUnit);
                const majorLabel = labels.major === previousMajor ? '' : labels.major;
                previousMajor = labels.major;

                const headerTick = document.createElement('div');
                headerTick.className = 'absolute inset-y-0 border-l border-gray-200 px-2 pt-1';
                headerTick.style.left = `${left}px`;
                const major = document.createElement('div');
                major.className = 'whitespace-nowrap text-[10px] font-medium uppercase tracking-wide text-gray-500';
                major.textContent = majorLabel;
                const minor = document.createElement('div');
                minor.className = 'mt-1 whitespace-nowrap text-xs text-gray-500';
                minor.textContent = labels.minor;
                headerTick.append(major, minor);
                header.appendChild(headerTick);

                const gridLine = document.createElement('div');
                gridLine.className = 'absolute inset-y-0 border-l border-gray-200';
                gridLine.style.left = `${left}px`;
                grid.appendChild(gridLine);
            }
            tick = this.addTicks(tick, zoom.tickUnit, tickMultiplier);
        }

        const now = Date.now();
        if (now >= this.rangeStart && now <= this.rangeEnd) {
            const left = this.positionForTimestamp(now);
            const todayLine = document.createElement('div');
            todayLine.className = 'absolute inset-y-0 border-l border-primary';
            todayLine.style.left = `${left}px`;
            grid.appendChild(todayLine);

            const todayMarker = document.createElement('div');
            todayMarker.className = 'absolute inset-y-0 border-l border-primary';
            todayMarker.style.left = `${left}px`;
            const todayLabel = document.createElement('span');
            todayLabel.className = 'absolute -left-7 top-1 rounded-xl bg-primary px-2 py-0.5 text-[10px] font-medium text-white';
            todayLabel.textContent = this.element.querySelector<HTMLElement>('[data-gant-today]')?.textContent?.trim() ?? 'Today';
            todayMarker.appendChild(todayLabel);
            header.appendChild(todayMarker);
        }
    }

    private tickDuration(unit: TickUnit): number {
        if (unit === 'month') return MONTH;
        if (unit === 'week') return WEEK;
        if (unit === 'day') return DAY;
        return HOUR;
    }

    private floorTick(value: Date, unit: TickUnit): Date {
        const tick = new Date(value);
        tick.setMinutes(0, 0, 0);
        if (unit === 'hour') return tick;
        tick.setHours(0);
        if (unit === 'day') return tick;
        if (unit === 'week') {
            const day = tick.getDay() || 7;
            tick.setDate(tick.getDate() - day + 1);
            return tick;
        }
        tick.setDate(1);
        return tick;
    }

    private addTicks(value: Date, unit: TickUnit, amount: number): Date {
        const next = new Date(value);
        if (unit === 'month') next.setMonth(next.getMonth() + amount);
        else if (unit === 'week') next.setDate(next.getDate() + 7 * amount);
        else if (unit === 'day') next.setDate(next.getDate() + amount);
        else next.setHours(next.getHours() + amount);
        return next;
    }

    private tickLabels(value: Date, unit: TickUnit): { major: string; minor: string } {
        if (unit === 'month') {
            return {
                major: new Intl.DateTimeFormat(undefined, { year: 'numeric' }).format(value),
                minor: new Intl.DateTimeFormat(undefined, { month: 'short' }).format(value),
            };
        }
        if (unit === 'hour') {
            return {
                major: new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(value),
                minor: new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(value),
            };
        }
        return {
            major: new Intl.DateTimeFormat(undefined, { month: 'short', year: 'numeric' }).format(value),
            minor: new Intl.DateTimeFormat(undefined, { day: 'numeric' }).format(value),
        };
    }

    private positionForTimestamp(timestamp: number): number {
        return ((timestamp - this.rangeStart) / (this.rangeEnd - this.rangeStart)) * this.canvasWidth;
    }

    private scrollToTimestamp(timestamp: number): void {
        if (!this.element) return;
        const position = this.positionForTimestamp(timestamp);
        const viewportWidth = Math.max(this.element.clientWidth - SIDEBAR_WIDTH, 0);
        this.element.scrollLeft = Math.max(0, position - viewportWidth / 2);
        this.updateVisibleRange();
    }

    private updateVisibleRange = (): void => {
        if (!this.element || this.canvasWidth <= 0) return;
        const viewportWidth = Math.max(this.element.clientWidth - SIDEBAR_WIDTH, 0);
        const visibleStart = this.rangeStart + (
            Math.max(this.element.scrollLeft, 0) / this.canvasWidth
        ) * (this.rangeEnd - this.rangeStart);
        const visibleEnd = this.rangeStart + (
            Math.min(this.element.scrollLeft + viewportWidth, this.canvasWidth) / this.canvasWidth
        ) * (this.rangeEnd - this.rangeStart);
        const label = this.element.querySelector<HTMLElement>('[data-gant-visible-range]');
        if (!label) return;
        const options: Intl.DateTimeFormatOptions = this.zoomIndex === ZOOM_LEVELS.length - 1
            ? { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }
            : { month: 'short', day: 'numeric', year: 'numeric' };
        const formatter = new Intl.DateTimeFormat(undefined, options);
        label.textContent = `${formatter.format(visibleStart)} – ${formatter.format(visibleEnd)}`;
    };

    private handleHtmxSwap = (): void => {
        this.applyZoom(true);
    };

    private onResize = (): void => {
        this.applyZoom(true);
    };

    private getAdjacentItem(delta: number): GantChartItem | null {
        if (!this.element || !this.currentCell?.element) return null;

        const itemElements = Array.from(
            this.element.querySelectorAll<HTMLElement>(`[${componentIdentifier}="gant-chart-item"]`),
        );
        const currentIndex = itemElements.indexOf(this.currentCell.element);
        if (currentIndex < 0 || itemElements.length === 0) return null;

        const nextIndex = Math.max(0, Math.min(itemElements.length - 1, currentIndex + delta));
        return getComponent(itemElements[nextIndex]) as GantChartItem | null;
    }

    private scheduleDependencyDraw = (): void => {
        if (this.drawFrame !== null) window.cancelAnimationFrame(this.drawFrame);
        this.drawFrame = window.requestAnimationFrame(() => {
            this.drawFrame = null;
            this.drawDependencies();
        });
    };

    private drawDependencies(): void {
        if (!this.element) return;

        const svg = this.element.querySelector<SVGSVGElement>('[data-gant-dependencies]');
        const lineGroup = svg?.querySelector<SVGGElement>('[data-gant-dependency-lines]');
        if (!svg || !lineGroup) return;

        const width = this.element.scrollWidth;
        const height = this.element.scrollHeight;
        svg.setAttribute('width', String(width));
        svg.setAttribute('height', String(height));
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.style.width = `${width}px`;
        svg.style.height = `${height}px`;
        lineGroup.replaceChildren();

        const items = Array.from(
            this.element.querySelectorAll<HTMLElement>(`[${componentIdentifier}="gant-chart-item"]`),
        );
        const itemsById = new Map(items.map((item) => [item.dataset.objectId ?? '', item]));
        const drawn = new Set<string>();

        for (const item of items) {
            const objectId = item.dataset.objectId;
            const dependencyFromId = item.dataset.dependencyFromId;
            const dependencyForId = item.dataset.dependencyForId;

            if (objectId && dependencyFromId) {
                this.appendDependency(lineGroup, itemsById.get(dependencyFromId), item, `${dependencyFromId}:${objectId}`, drawn);
            }
            if (objectId && dependencyForId) {
                this.appendDependency(lineGroup, item, itemsById.get(dependencyForId), `${objectId}:${dependencyForId}`, drawn);
            }
        }
    }

    private appendDependency(
        lineGroup: SVGGElement,
        source: HTMLElement | undefined,
        target: HTMLElement | undefined,
        key: string,
        drawn: Set<string>,
    ): void {
        if (!this.element || !source || !target || drawn.has(key)) return;
        drawn.add(key);

        const rootRect = this.element.getBoundingClientRect();
        const sourceRect = source.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();
        const startX = sourceRect.right - rootRect.left + this.element.scrollLeft;
        const startY = sourceRect.top + sourceRect.height / 2 - rootRect.top + this.element.scrollTop;
        const endX = targetRect.left - rootRect.left + this.element.scrollLeft;
        const endY = targetRect.top + targetRect.height / 2 - rootRect.top + this.element.scrollTop;
        const curve = Math.max(24, Math.abs(endX - startX) / 2);

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M ${startX} ${startY} C ${startX + curve} ${startY}, ${endX - curve} ${endY}, ${endX} ${endY}`);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', 'currentColor');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('class', 'text-primary');
        path.setAttribute('marker-end', `url(#gant-arrow-${this.contentTypeId})`);
        lineGroup.appendChild(path);
    }
}
