import BaseComponent from "./BaseComponent"

export enum MessageType {
    INFO = "info",
    SUCCESS = "success",
    WARNING = "warning",
    ERROR = "error"
}


export default class UiMessage extends BaseComponent {
    private messageText: string;
    private messageType: MessageType;
    private duration: number = 5;
    private position: string = "bottom-right";
    private pauseWhenHidden: boolean = false;
    private remainingDurationMs: number = 0;
    private timerStartedAt: number = 0;
    private removalTimer: number | null = null;
    private fadeTimer: number | null = null;
    private messageContainer: HTMLElement | null = null;
    private closeButton: HTMLButtonElement | null = null;
    private dismissed: boolean = false;

    private readonly visibilityChangeHandler = (): void => {
        if (document.hidden) {
            this.pauseRemovalTimer();
        } else {
            this.startRemovalTimer();
        }
    };

    private readonly closeHandler = (): void => {
        this.fadeOutAndRemove();
    };

    public initialize(): void {
        if (!this.element) {
            return;
        }

        this.messageText = this.element.dataset.messageText || "";
        this.messageType = (this.element.dataset.messageType as MessageType) || MessageType.INFO;
        this.position = this.element.dataset.position || this.position;
        this.pauseWhenHidden = this.element.dataset.pauseWhenHidden === "true";
        const durationData = this.element.dataset.duration;
        if (durationData) {
            this.duration = parseInt(durationData, 10);
        }
        this.remainingDurationMs = this.duration * 1000;

        this.showMessage();
    }

    /**
     * Method to show the actual message on the screen
     */
    public showMessage(): void {
        if (!this.element) {
            return;
        }

        const messageContainer = document.createElement("div");
        const alertClassMap: Record<MessageType, string> = {
            [MessageType.INFO]: "alert-info",
            [MessageType.SUCCESS]: "alert-success",
            [MessageType.WARNING]: "alert-warning",
            [MessageType.ERROR]: "alert-danger",
        };

        messageContainer.classList.add(
            "alert",
            alertClassMap[this.messageType] || "alert-info",
            "flex",
            "items-center",
            "justify-between",
            "shadow-md",
            "my-2",
            "message-container"
        );

        // Create message inside the element with an icon and close button
        const left = document.createElement('div');
        left.classList.add('flex', 'items-center');

        const iconElem = document.createElement('i');
        iconElem.classList.add('alert-icon');
        // Map to Font Awesome icons (common names)
        const iconMap: Record<MessageType, string[]> = {
            [MessageType.INFO]: ['fa-solid', 'fa-info-circle'],
            [MessageType.SUCCESS]: ['fa-solid', 'fa-check-circle'],
            [MessageType.WARNING]: ['fa-solid', 'fa-exclamation-triangle'],
            [MessageType.ERROR]: ['fa-solid', 'fa-exclamation-circle'],
        };
        const faClasses = iconMap[this.messageType] || iconMap[MessageType.INFO];
        faClasses.forEach((c) => iconElem.classList.add(c));

        const textElem = document.createElement('div');
        textElem.classList.add('ml-3');
        textElem.innerHTML = this.messageText;

        left.appendChild(iconElem);
        left.appendChild(textElem);

        const closeBtn = document.createElement('button');
        closeBtn.classList.add('alert-close');
        closeBtn.setAttribute('aria-label', 'Dismiss message');
        closeBtn.innerHTML = '<i class="fa-solid fa-xmark"></i>';

        // Container layout: left (icon+text) and right (close)
        messageContainer.appendChild(left);
        messageContainer.appendChild(closeBtn);

        // Append to a fixed-position wrapper so messages are fixed in place
        const wrapper = this.getOrCreateWrapper(this.position);
        wrapper.appendChild(messageContainer);

        this.messageContainer = messageContainer;
        this.closeButton = closeBtn;
        closeBtn.addEventListener("click", this.closeHandler);
        if (this.pauseWhenHidden) {
            document.addEventListener(
                "visibilitychange",
                this.visibilityChangeHandler,
            );
        }
        this.startRemovalTimer();
    }

    private startRemovalTimer(): void {
        if (
            this.dismissed
            || this.removalTimer !== null
            || (this.pauseWhenHidden && document.hidden)
        ) {
            return;
        }

        this.timerStartedAt = Date.now();
        this.removalTimer = window.setTimeout(
            () => {
                if (this.pauseWhenHidden && document.hidden) {
                    this.pauseRemovalTimer();
                    return;
                }

                this.removalTimer = null;
                this.fadeOutAndRemove();
            },
            this.remainingDurationMs,
        );
    }

    private pauseRemovalTimer(): void {
        if (!this.pauseWhenHidden || this.removalTimer === null) {
            return;
        }

        window.clearTimeout(this.removalTimer);
        this.removalTimer = null;
        this.remainingDurationMs = Math.max(
            0,
            this.remainingDurationMs - (Date.now() - this.timerStartedAt),
        );
    }

    private fadeOutAndRemove(): void {
        if (this.dismissed || !this.messageContainer) {
            return;
        }

        this.dismissed = true;
        this.cleanupListenersAndTimers();
        this.messageContainer.classList.add("fade-out");
        this.fadeTimer = window.setTimeout(() => {
            this.messageContainer?.remove();
            if (this.element?.dataset.autoRemove === "true") {
                this.element.remove();
            }
            this.messageContainer = null;
            this.closeButton = null;
            this.fadeTimer = null;
        }, 500);
    }

    private cleanupListenersAndTimers(): void {
        if (this.removalTimer !== null) {
            window.clearTimeout(this.removalTimer);
            this.removalTimer = null;
        }
        document.removeEventListener(
            "visibilitychange",
            this.visibilityChangeHandler,
        );
        this.closeButton?.removeEventListener("click", this.closeHandler);
    }

    public override destroy(): void {
        this.cleanupListenersAndTimers();
        if (this.fadeTimer !== null) {
            window.clearTimeout(this.fadeTimer);
            this.fadeTimer = null;
        }
        this.messageContainer?.remove();
        this.messageContainer = null;
        this.closeButton = null;
    }

    private getOrCreateWrapper(position: string): HTMLElement {
        const id = `messages-wrapper-${position}`;
        let wrapper = document.getElementById(id) as HTMLElement | null;
        if (wrapper) return wrapper;

        wrapper = document.createElement("div");
        wrapper.id = id;
        wrapper.classList.add("messages-wrapper");
        // Set position defaults; override the CSS .messages-wrapper base anchors
        wrapper.style.position = "fixed";
        wrapper.style.zIndex = "1100";
        wrapper.style.display = "flex";
        wrapper.style.flexDirection = "column";
        wrapper.style.gap = "10px";

        // Position mapping
        switch (position) {
            case "top-right":
                wrapper.style.top = "40px";
                wrapper.style.right = "60px";
                wrapper.style.left = "auto";
                wrapper.style.bottom = "auto";
                break;
            case "bottom-left":
                wrapper.style.bottom = "40px";
                wrapper.style.left = "60px";
                wrapper.style.top = "auto";
                wrapper.style.right = "auto";
                break;
            case "bottom-right":
                wrapper.style.bottom = "40px";
                wrapper.style.right = "60px";
                wrapper.style.top = "auto";
                wrapper.style.left = "auto";
                break;
            case "top-left":
            default:
                wrapper.style.top = "40px";
                wrapper.style.left = "60px";
                wrapper.style.right = "auto";
                wrapper.style.bottom = "auto";
                break;
        }

        document.body.appendChild(wrapper);
        return wrapper;
    }

}
