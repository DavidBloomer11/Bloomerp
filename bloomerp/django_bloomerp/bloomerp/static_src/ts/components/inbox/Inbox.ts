import htmx from "htmx.org";
import BaseComponent from "../BaseComponent";
import { InboxItem } from "./InboxItem";
import getGeneralModal from "@/utils/modals";
import getSdk from "@/sdk/getSdk";
import { insertSkeleton } from "@/utils/animations";
import { getCsrfToken } from "@/utils/cookies";

export class Inbox extends BaseComponent {
    private searchInput: HTMLInputElement | null = null;
    private searchInputHandler: (() => void) | null = null;
    private searchDebounceTimer: number | null = null;
    private inboxActionClickHandler: ((event: Event) => void) | null = null;

    public initialize(): void {
        if (!this.element) return;

        // Initialy load inbox items
        this.queryInbox();

        // Setup event listeners
        this.setupAddFolderBtnListener();
        this.setupSelectFolderListener();
        this.setupSearchInputListener();
        this.setupInboxActionListener();
        
    }

    private queryInbox(query?:Map<string, string>) {
        const folderId = this.getDataAttribute('inboxFolderId');
        if (!folderId) return;
        const target = this.element?.querySelector('#inbox-items');
        insertSkeleton(target as HTMLElement);

        htmx.ajax(
            'get',
            this.getRenderInboxItemsUrl(folderId, query),
            {
                target: '#inbox-items'
            }
        ).then(() => {
            this.setupDeepSearchListener();
        })
    }

    private getInboxItems() : InboxItem[] {
        return []
    }


    private setupAddFolderBtnListener() {
        if (!this.element) return;

        const  addFolderBtn = this.element.querySelector('#add-folder-btn');

        if (addFolderBtn) {
            addFolderBtn.addEventListener('click', () => {
                const modal = getGeneralModal();

                htmx.ajax('get', this.getDataAttribute('addFolderComponentUrl'), {
                    target: modal.getBodyElement(),
                })

                modal.open()

            });
        }
    }

    private setupSelectFolderListener() {
        if (!this.element) return;

        // Get the select folder dropdown element
        const selectFolderDropdown = this.element.querySelector('#select-folder-dropdown');

        // Get all the items in the dropdown that start with select-folder-<folder_id>
        const folderItems = selectFolderDropdown?.querySelectorAll('[id^="select-folder-"]');

        // Add click event listeners to each folder item
        folderItems?.forEach((item) => {
            item.addEventListener('click', () => {
                const folderId = item.id.replace('select-folder-', '');
                const sdk = getSdk();
                sdk.userInboxPreferences.partialUpdate(
                    this.getDataAttribute('inboxPreferenceId') || '',
                    {
                        selected_inbox_folder: folderId
                    }
                ).then(()=> {
                    // Reload the window
                    window.location.reload();
                })
                
            });
        });
    }

    private setupSearchInputListener() {
        if (!this.element) return;

        this.searchInput = this.element.querySelector('#inbox-search-input') as HTMLInputElement;
        
        if (this.searchInput) {
            this.searchInputHandler = () => {
                if (this.searchDebounceTimer) {
                    window.clearTimeout(this.searchDebounceTimer);
                }

                this.searchDebounceTimer = window.setTimeout(() => {
                    const query = this.searchInput?.value.trim() || '';
                    const queryMap = new Map<string, string>();
                    if (query) {
                        queryMap.set('q', query);
                    }
                    this.queryInbox(queryMap);
                }, 250);
            };

            this.searchInput.addEventListener('input', this.searchInputHandler);
        }
    }

    private setupDeepSearchListener() {
        if (!this.element) return;

        const deepSearchBtn = this.element.querySelector('#deep-search-btn');

        if (deepSearchBtn) {
            deepSearchBtn.addEventListener('click', () => {
                const query = this.searchInput?.value.trim() || '';
                const queryMap = new Map<string, string>();
                if (query) {
                    queryMap.set('q', query);
                }
                queryMap.set('deep_search', 'true');
                this.queryInbox(queryMap);
            });
        }
    }

    private setupInboxActionListener() {
        if (!this.element) return;

        this.inboxActionClickHandler = (event: Event) => {
            const trigger = (event.target as HTMLElement | null)?.closest<HTMLElement>('[data-inbox-action]');
            if (!trigger || !this.element?.contains(trigger)) return;
            if (trigger.dataset.inboxActionLevel !== 'folder') return;

            event.preventDefault();
            this.executeInboxAction(trigger);
        };

        this.element.addEventListener('click', this.inboxActionClickHandler);
    }

    private executeInboxAction(trigger: HTMLElement) {
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
                return this.getDataAttribute('renderInboxItemTarget') || '#inbox-item-render-target';
            default:
                return '#inbox-message-target';
        }
    }

    private getExecuteInboxActionUrl(level: string, itemId: string, actionKey: string): string {
        const url = this.getDataAttribute('executeInboxActionUrl') || '';
        if (!url || !level || !itemId || !actionKey) return '';

        return url
            .replace('REPLACE_LEVEL', encodeURIComponent(level))
            .replace('REPLACE_WITH_ID', encodeURIComponent(itemId))
            .replace('REPLACE_ACTION_KEY', encodeURIComponent(actionKey));
    }

    /**
     * Returns the URL for rendering the inbox items for a specific folder.
     * @param folderId the ID of the folder for which to render inbox items.
     * @param query optional query parameters to append to the render URL.
     * @returns the URL for rendering the inbox items for the specified folder.
     */
    private getRenderInboxItemsUrl(folderId: string, query?: Map<string, string>): string {
        const url = this.getDataAttribute('inboxFolderItemsComponentUrl')?.replace('REPLACE_WITH_ID', folderId) || '';
        if (!query || query.size === 0) return url;

        const params = new URLSearchParams();
        query.forEach((value, key) => {
            if (value) {
                params.set(key, value);
            }
        });

        const queryString = params.toString();
        if (!queryString) return url;

        return `${url}${url.includes('?') ? '&' : '?'}${queryString}`;
    }


    public destroy(): void {
        if (this.element && this.inboxActionClickHandler) {
            this.element.removeEventListener('click', this.inboxActionClickHandler);
        }
        if (this.searchInput && this.searchInputHandler) {
            this.searchInput.removeEventListener('input', this.searchInputHandler);
        }
        if (this.searchDebounceTimer) {
            window.clearTimeout(this.searchDebounceTimer);
        }
        this.searchInput = null;
        this.searchInputHandler = null;
        this.searchDebounceTimer = null;
        this.inboxActionClickHandler = null;
    }
}
