import htmx from "htmx.org";
import BaseSectionedLayoutItem from "../layouts/BaseSectionedLayoutItem";
import getGeneralModal from "@/utils/modals";

export default class WorkspaceTile extends BaseSectionedLayoutItem {
    private icon = "";
    private title = "";
    private editButton: HTMLElement | null = null;
    private editButtonHandler: (() => void) | null = null;

    public initialize(): void {
        super.initialize();
        if (!this.element) return;

        const tileId = this.element.dataset.tileId ?? "";
        if (tileId) {
            this.itemId = tileId;
        }

        this.editButton = this.element.querySelector<HTMLElement>('[data-layout-edit-item]');
        this.editButtonHandler = () => {
            const url = this.element?.dataset.layoutEditUrl;
            if (!url) return;
            const modal = getGeneralModal()
            modal.setSize('full')
            modal.setTitle('Update Tile')

            htmx.ajax(
                'get',
                url,
                {
                    target: modal.getBodyElement()
                }
            ).then(()=> {modal.open()})
        };
        this.editButton?.addEventListener('click', this.editButtonHandler);
    }

    public override destroy(): void {
        if (this.editButton && this.editButtonHandler) {
            this.editButton.removeEventListener('click', this.editButtonHandler);
        }
        this.editButton = null;
        this.editButtonHandler = null;
        super.destroy();
    }

    public setIcon(icon: string): void {
        if (!this.element) return;

        this.icon = icon;
        const iconElement = this.element.querySelector<HTMLElement>("[data-tile-icon] i");
        if (iconElement) {
            iconElement.className = `fa ${icon}`;
        }
    }

    public setTitle(title: string): void {
        if (!this.element) return;

        this.title = title;
        const titleElement = this.element.querySelector<HTMLElement>("[data-tile-title]");
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    public getTileId(): string {
        return this.getLayoutItemId();
    }
}
