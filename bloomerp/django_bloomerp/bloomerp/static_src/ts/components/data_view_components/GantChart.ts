import { componentIdentifier, getComponent } from "../BaseComponent";
import { BaseDataViewCell } from "./BaseDataViewCell";
import { BaseDataViewComponent } from "./BaseDataViewComponent";

export class GantChartItem extends BaseDataViewCell {
    public initialize(): void {
        super.initialize();
    }
}

export class GantChart extends BaseDataViewComponent {
    protected cellClass = GantChartItem;
    private resizeObserver: ResizeObserver | null = null;
    private drawFrame: number | null = null;

    public initialize(): void {
        if (!this.element) return;

        super.initialize();
        const abortController = this.ensureAbortController();
        this.element.addEventListener('htmx:afterSwap', this.scheduleDependencyDraw, {
            signal: abortController.signal,
        });
        window.addEventListener('resize', this.scheduleDependencyDraw, {
            signal: abortController.signal,
        });

        this.resizeObserver = new ResizeObserver(this.scheduleDependencyDraw);
        this.resizeObserver.observe(this.element);
        this.scheduleDependencyDraw();
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

    // A Gantt bar represents one row, so horizontal arrows keep the row selected.
    public moveCellRight(): BaseDataViewCell {
        return this.currentCell!;
    }

    public moveCellLeft(): BaseDataViewCell {
        return this.currentCell!;
    }

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
        if (this.drawFrame !== null) {
            window.cancelAnimationFrame(this.drawFrame);
        }
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
                this.appendDependency(
                    lineGroup,
                    itemsById.get(dependencyFromId),
                    item,
                    `${dependencyFromId}:${objectId}`,
                    drawn,
                );
            }
            if (objectId && dependencyForId) {
                this.appendDependency(
                    lineGroup,
                    item,
                    itemsById.get(dependencyForId),
                    `${objectId}:${dependencyForId}`,
                    drawn,
                );
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
        const startY = sourceRect.top + (sourceRect.height / 2) - rootRect.top + this.element.scrollTop;
        const endX = targetRect.left - rootRect.left + this.element.scrollLeft;
        const endY = targetRect.top + (targetRect.height / 2) - rootRect.top + this.element.scrollTop;
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
