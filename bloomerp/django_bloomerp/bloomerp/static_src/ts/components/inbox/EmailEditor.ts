import { $createParagraphNode } from "lexical";
import BaseComponent, { getComponent } from "../BaseComponent";
import { BloomerpTextEditor } from "../text_editor/BloomerpTextEditor";
import { $createHtmlNode } from "../text_editor/nodes/HtmlNode";



export class EmailEditor extends BaseComponent {
    private editor: BloomerpTextEditor;
    
    public initialize(): void {
        this.setupCcBccListeners();
        this.setupEditor();
    }

    public setupEditor(): void {
        const editorElement = this.element?.querySelector('[bloomerp-component="bloomerp-text-editor"]') as HTMLElement;
        this.editor = getComponent(editorElement) as BloomerpTextEditor;

        // Add empty paragraph node to the editor to ensure it has a starting point
        this.editor.insertNode(
            ()=> $createParagraphNode()
        )
        
        // Insert the parent email HTML into the editor if it exists
        this.editor.insertNode(() =>
            $createHtmlNode(this.getDataAttribute("parentEmail") || "")
        );
        
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