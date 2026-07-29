import htmx from "htmx.org";
import BaseComponent from "../BaseComponent";
import { insertSkeleton } from "@/utils/animations";
import getGeneralModal from "@/utils/modals";
import { getCsrfToken } from "@/utils/cookies";

export class InboxItem extends BaseComponent {
    private renderTarget: HTMLElement | null = null;
    private clickHandler: ((event: Event) => void) | null = null;
    private actionClickHandler: ((event: Event) => void) | null = null;

    public initialize(): void {
        if (!this.element) return;

        if (this.isDetailMode()) {
            this.setupInboxActionListener();
            return;
        }

        this.renderTarget = this.getRenderTarget();
        this.clickHandler = (event: Event) => {
            event.preventDefault();
            this.render();
        };
        this.element.addEventListener('click', this.clickHandler);
    }

    public destroy(): void {
        if (this.element && this.clickHandler) {
            this.element.removeEventListener('click', this.clickHandler);
        }
        if (this.element && this.actionClickHandler) {
            this.element.removeEventListener('click', this.actionClickHandler);
        }
        this.renderTarget = null;
        this.clickHandler = null;
        this.actionClickHandler = null;
    }

    public render(): void {
        if (!this.element) return;

        const url = this.getRenderUrl();
        const target = this.renderTarget || this.getRenderTarget();
        if (!url || !target) return;

        insertSkeleton(target);

        htmx.ajax('get', url, { target });
    }

    private getRenderUrl(): string | null {
        const itemId = this.getDataAttribute('inboxItemId');
        const inbox = this.getInboxElement();
        const urlTemplate = inbox?.dataset.renderInboxItemUrl || null;
        if (!itemId || !urlTemplate) return null;

        return urlTemplate.replace('REPLACE_WITH_ID', itemId);
    }

    private getRenderTarget(): HTMLElement | null {
        const inbox = this.getInboxElement();
        const targetSelector = inbox?.dataset.renderInboxItemTarget || null;
        if (!targetSelector) return null;

        return document.querySelector(targetSelector);
    }

    private setupInboxActionListener(): void {
        if (!this.element) return;

        this.actionClickHandler = (event: Event) => {
            const trigger = (event.target as HTMLElement | null)?.closest<HTMLElement>('[data-inbox-action]');
            if (!trigger || !this.element?.contains(trigger)) return;
            if (trigger.dataset.inboxActionLevel !== 'item') return;

            event.preventDefault();
            event.stopPropagation();
            this.executeInboxAction(trigger);
        };

        this.element.addEventListener('click', this.actionClickHandler);
    }

    private executeInboxAction(trigger: HTMLElement): void {
        const level = trigger.dataset.inboxActionLevel || '';
        const itemId = trigger.dataset.inboxActionItemId || '';
        const actionKey = trigger.dataset.inboxActionKey || '';
        const method = trigger.dataset.inboxActionMethod === 'post' ? 'post' : 'get';
        const target = this.resolveInboxActionTarget(trigger);
        const url = this.getExecuteInboxActionUrl(level, itemId, actionKey);

        if (!url || !target) return;

        const values: Record<string, string> | undefined = method === 'post' ? {} : undefined;
        const csrfToken = getCsrfToken();
        if (values && csrfToken) {
            values.csrfmiddlewaretoken = csrfToken;
        }

        htmx.ajax(method, url, {
            target,
            swap: 'innerHTML',
            values,
        });
    }

    private resolveInboxActionTarget(trigger: HTMLElement): HTMLElement | string | null {
        const target = trigger.dataset.inboxActionTarget;

        switch (target) {
            case 'modal': {
                const modal = getGeneralModal();
                modal.open();
                return modal.getBodyElement();
            }
            case 'items':
                return '#inbox-items';
            case 'message':
                return '#inbox-message-target';
            case 'render-item':
                return this.getInboxElement()?.dataset.renderInboxItemTarget || '#inbox-item-render-target';
            default:
                return '#inbox-message-target';
        }
    }

    private getExecuteInboxActionUrl(level: string, itemId: string, actionKey: string): string {
        const url = this.getInboxElement()?.dataset.executeInboxActionUrl || '';
        if (!url || !level || !itemId || !actionKey) return '';

        return url
            .replace('REPLACE_LEVEL', encodeURIComponent(level))
            .replace('REPLACE_WITH_ID', encodeURIComponent(itemId))
            .replace('REPLACE_ACTION_KEY', encodeURIComponent(actionKey));
    }

    private getInboxElement(): HTMLElement | null {
        if (!this.element) return null;
        return this.element.closest<HTMLElement>('[bloomerp-component="inbox"]');
    }

    private isDetailMode(): boolean {
        return this.getDataAttribute('inboxItemDetail') === 'true';
    }
}
