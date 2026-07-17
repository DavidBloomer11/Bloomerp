import { componentIdentifier, getComponent } from "../BaseComponent";
import { BaseDataViewCell } from "./BaseDataViewCell";
import { BaseDataViewComponent } from "./BaseDataViewComponent";

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;
const MONTH = 30.4375 * DAY;
const DEFAULT_SIDEBAR_WIDTH = 320;

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

export class GantChartSidebarItem extends BaseDataViewCell {
    public initialize(): void {
        super.initialize();
    }
}

export class GantChart extends BaseDataViewComponent {
    protected cellClass = GantChartItem;
    private resizeObserver: ResizeObserver | null = null;
    private sidebarResizeObserver: ResizeObserver | null = null;
    private drawFrame: number | null = null;
    private zoomIndex = 0;
    private rangeStart = 0;
    private rangeEnd = 0;
    private canvasWidth = 0;
    private dataStart = 0;
    private dataEnd = 0;
    private sidebarWidth = DEFAULT_SIDEBAR_WIDTH;
    private extendingTimeline = false;

    public initialize(): void {
        if (!this.element) return;

        super.initialize();
        this.dataStart = Number(this.element.dataset.gantStart);
        this.dataEnd = Number(this.element.dataset.gantEnd);
        if (!Number.isFinite(this.dataStart) || !Number.isFinite(this.dataEnd)) return;

        const sidebarPanel = this.element.querySelector<HTMLElement>('[data-gant-sidebar]');
        const sidebar = sidebarPanel?.closest<HTMLElement>('[bloomerp-component="resizable-div"]')
            ?? sidebarPanel;

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
            () => this.focusTimestamp(Date.now()),
            { signal: abortController.signal },
        );
        this.element.addEventListener('scroll', this.handleScroll, {
            signal: abortController.signal,
            passive: true,
        });
        this.element.addEventListener('htmx:afterSwap', this.handleHtmxSwap, {
            signal: abortController.signal,
        });
        window.addEventListener('resize', this.onResize, { signal: abortController.signal });

        this.resizeObserver = new ResizeObserver(this.onResize);
        this.resizeObserver.observe(this.element);
        if (sidebar) {
            this.sidebarResizeObserver = new ResizeObserver(this.onSidebarResize);
            this.sidebarResizeObserver.observe(sidebar);
        }
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
        this.sidebarResizeObserver?.disconnect();
        this.resizeObserver = null;
        this.sidebarResizeObserver = null;
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
            ? this.getViewportCenterTimestamp()
            : null;
        const zoom = ZOOM_LEVELS[this.zoomIndex];
        const viewportWidth = this.getTimelineViewportWidth();
        const center = oldCenter ?? (
            Date.now() >= this.dataStart && Date.now() <= this.dataEnd
                ? Date.now()
                : (this.dataStart + this.dataEnd) / 2
        );
        const minimumSpan = Math.max(viewportWidth / zoom.pixelsPerMs * 6, zoom.paddingMs * 2);
        this.rangeStart = Math.min(this.dataStart - zoom.paddingMs, center - minimumSpan / 2);
        this.rangeEnd = Math.max(this.dataEnd + zoom.paddingMs, center + minimumSpan / 2);
        this.updateTimelineGeometry();

        this.scrollToTimestamp(center);
    }

    private updateTimelineGeometry(): void {
        if (!this.element) return;
        const zoom = ZOOM_LEVELS[this.zoomIndex];
        this.canvasWidth = Math.max((this.rangeEnd - this.rangeStart) * zoom.pixelsPerMs, 1);
        for (const layout of this.element.querySelectorAll<HTMLElement>('[data-gant-layout]')) {
            layout.style.gridTemplateColumns = `${this.sidebarWidth}px ${this.canvasWidth}px`;
            layout.style.width = `${this.sidebarWidth + this.canvasWidth}px`;
        }

        const grid = this.element.querySelector<HTMLElement>('[data-gant-grid]');
        if (grid) {
            grid.style.left = `${this.sidebarWidth}px`;
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
            todayLine.dataset.gantTodayLine = 'true';
            todayLine.style.left = `${left}px`;
            grid.appendChild(todayLine);

            const todayMarker = document.createElement('div');
            todayMarker.className = 'absolute inset-y-0 border-l border-primary';
            todayMarker.dataset.gantTodayMarker = 'true';
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
        const viewportWidth = this.getTimelineViewportWidth();
        this.element.scrollLeft = Math.max(0, position - viewportWidth / 2);
        this.updateVisibleRange();
    }

    private focusTimestamp(timestamp: number): void {
        if (!this.element) return;
        if (timestamp < this.rangeStart || timestamp > this.rangeEnd) {
            const zoom = ZOOM_LEVELS[this.zoomIndex];
            const visibleDuration = this.getTimelineViewportWidth() / zoom.pixelsPerMs;
            this.rangeStart = Math.min(this.rangeStart, timestamp - visibleDuration * 3);
            this.rangeEnd = Math.max(this.rangeEnd, timestamp + visibleDuration * 3);
            this.updateTimelineGeometry();
        }
        this.scrollToTimestamp(timestamp);
    }

    private getTimelineViewportWidth(): number {
        if (!this.element) return 640;
        return Math.max(this.element.clientWidth - this.sidebarWidth, 320);
    }

    private getViewportCenterTimestamp(): number {
        if (!this.element || this.canvasWidth <= 0) return (this.dataStart + this.dataEnd) / 2;
        const canvasCenter = this.element.scrollLeft + this.getTimelineViewportWidth() / 2;
        return this.rangeStart + (canvasCenter / this.canvasWidth) * (this.rangeEnd - this.rangeStart);
    }

    private updateVisibleRange = (): void => {
        if (!this.element || this.canvasWidth <= 0) return;
        const viewportWidth = this.getTimelineViewportWidth();
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

    private handleScroll = (): void => {
        this.updateVisibleRange();
        this.extendTimelineNearEdge();
    };

    private extendTimelineNearEdge(): void {
        if (!this.element || this.extendingTimeline) return;
        const viewportWidth = this.getTimelineViewportWidth();
        const threshold = viewportWidth * 0.75;
        const nearStart = this.element.scrollLeft < threshold;
        const nearEnd = this.element.scrollLeft + viewportWidth > this.canvasWidth - threshold;
        if (!nearStart && !nearEnd) return;

        this.extendingTimeline = true;
        const zoom = ZOOM_LEVELS[this.zoomIndex];
        const extensionMs = Math.max(
            viewportWidth * 2 / zoom.pixelsPerMs,
            this.tickDuration(zoom.tickUnit) * 8,
        );
        const previousScrollLeft = this.element.scrollLeft;
        let prependedWidth = 0;
        if (nearStart) {
            this.rangeStart -= extensionMs;
            prependedWidth = extensionMs * zoom.pixelsPerMs;
        }
        if (nearEnd) this.rangeEnd += extensionMs;

        this.updateTimelineGeometry();
        this.element.scrollLeft = previousScrollLeft + prependedWidth;
        window.requestAnimationFrame(() => {
            this.extendingTimeline = false;
            this.updateVisibleRange();
        });
    }

    private handleHtmxSwap = (): void => {
        this.applyZoom(true);
    };

    private onResize = (): void => {
        this.applyZoom(true);
    };

    private onSidebarResize = (entries: ResizeObserverEntry[]): void => {
        if (!this.element || entries.length === 0) return;
        const nextWidth = Math.max(0, Math.round(entries[0].contentRect.width));
        if (nextWidth === this.sidebarWidth) return;
        const center = this.getViewportCenterTimestamp();
        this.sidebarWidth = nextWidth;
        this.updateTimelineGeometry();
        this.scrollToTimestamp(center);
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

        const rows = this.element.querySelector<HTMLElement>('[data-gant-rows]');
        const width = this.sidebarWidth + this.canvasWidth;
        const height = rows ? rows.offsetTop + rows.scrollHeight : this.element.clientHeight;
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
