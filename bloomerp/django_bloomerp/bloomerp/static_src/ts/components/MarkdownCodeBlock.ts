import BaseComponent from "./BaseComponent";


export default class MarkdownCodeBlock extends BaseComponent {
    private copyButton: HTMLButtonElement | null = null;
    private clickHandler: (() => void) | null = null;
    private resetTimeout: number | null = null;

    public initialize(): void {
        if (!this.element) return;

        this.copyButton = this.element.querySelector<HTMLButtonElement>("[data-copy-code]");
        if (!this.copyButton) return;

        this.clickHandler = () => void this.copyCode();
        this.copyButton.addEventListener("click", this.clickHandler);
    }

    public destroy(): void {
        if (this.copyButton && this.clickHandler) {
            this.copyButton.removeEventListener("click", this.clickHandler);
        }
        if (this.resetTimeout !== null) {
            window.clearTimeout(this.resetTimeout);
        }

        this.copyButton = null;
        this.clickHandler = null;
        this.resetTimeout = null;
        super.destroy();
    }

    private async copyCode(): Promise<void> {
        if (!this.element || !this.copyButton) return;

        const code = this.element.querySelector<HTMLElement>("pre code");
        if (!code) return;

        try {
            await navigator.clipboard.writeText(code.textContent ?? "");
            this.showCopiedState();
        } catch (error) {
            console.error("Failed to copy Markdown code block:", error);
        }
    }

    private showCopiedState(): void {
        if (!this.copyButton) return;

        const copyLabel = this.copyButton.dataset.copyLabel ?? "Copy";
        const copiedLabel = this.copyButton.dataset.copiedLabel ?? "Copied";
        this.copyButton.textContent = copiedLabel;
        this.copyButton.setAttribute("aria-label", copiedLabel);

        if (this.resetTimeout !== null) {
            window.clearTimeout(this.resetTimeout);
        }
        this.resetTimeout = window.setTimeout(() => {
            if (!this.copyButton) return;
            this.copyButton.textContent = copyLabel;
            this.copyButton.setAttribute("aria-label", copyLabel);
            this.resetTimeout = null;
        }, 2000);
    }
}
