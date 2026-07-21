import { $getRoot } from "lexical";
import BaseComponent, { getComponent } from "../BaseComponent";
import { BloomerpTextEditor } from "../text_editor/BloomerpTextEditor";

export class EmailEditor extends BaseComponent {
    private editor: BloomerpTextEditor;
    
    public initialize(): void {
        this.setupCcBccListeners();
        this.setupEditor();
    }

    public setupEditor(): void {
        const editorElement = this.element?.querySelector('[bloomerp-component="bloomerp-text-editor"]') as HTMLElement;
        this.editor = getComponent(editorElement) as BloomerpTextEditor;

        const parentEmail = this.getDataAttribute("parentEmail") || "";
        if (!parentEmail.trim()) return;

        const quotedEmail = `
            <div data-text-editor-html-node="true">
                <hr style="border: 0; border-top: 1px solid #d1d5db; margin: 24px 0;">
                ${parentEmail}
            </div>
        `;
        const replyContent = this.editor.getValue() || "<p><br></p>";

        // Keep a dedicated editable paragraph above the quoted email.
        this.editor.setValue(`${replyContent}${quotedEmail}`);
        this.editor.editor?.update(() => {
            $getRoot().getLastChild()?.getPreviousSibling()?.selectEnd();
        }, { discrete: true });
        this.editor.editor?.focus();
    }

    public setupCcBccListeners() : void {
        if (!this.element) return;

        const showCcButton = this.element.querySelector("#show-cc-field");
        const showBccButton = this.element.querySelector("#show-bcc-field");
        const ccField = this.element.querySelector("#cc-field");
        const bccField = this.element.querySelector("#bcc-field");

        if (showCcButton && ccField) {
            showCcButton.addEventListener("click", () => {
                ccField.classList.toggle("hidden");
            });
        }

        if (showBccButton && bccField) {
            showBccButton.addEventListener("click", () => {
                bccField.classList.toggle("hidden");
            });
        }
    }

}
