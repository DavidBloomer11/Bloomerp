import BaseTile from "./BaseTile";
import { Excalidraw, serializeAsJSON } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import { createElement } from "react";
import { createRoot, Root } from "react-dom/client";
import { getCsrfToken } from "@/utils/cookies";

const SAVE_INTERVAL_MS = 5_000;

export default class Canvas extends BaseTile {
    private root: Root | null = null;
    private saveInterval: number | null = null;
    private saveUrl = "";
    private initialState: Record<string, any> | null = null;
    private lastSavedState = "";
    private pendingState: string | null = null;
    private saveInProgress = false;

    private onExcalidrawChange = (elements: readonly any[], appState: any, files: any) => {
        try {
            const jsonState = serializeAsJSON(elements, appState, files, "local");
            if (this.saveUrl && jsonState !== this.lastSavedState) {
                this.pendingState = jsonState;
            }
        } catch (error) {
            console.error("[workspace-tile-canvas] Failed to serialize state", error);
        }
    };

    private parseInitialState(): void {
        const rawState = this.element?.dataset.initialState;
        if (!rawState) return;

        try {
            const parsedState = JSON.parse(rawState);
            if (parsedState && typeof parsedState === "object" && !Array.isArray(parsedState)) {
                this.initialState = parsedState;
                this.lastSavedState = JSON.stringify(parsedState);
            }
        } catch (error) {
            console.error("[workspace-tile-canvas] Failed to parse initial state", error);
        }
    }

    private savePendingState = async (): Promise<void> => {
        if (!this.saveUrl || !this.pendingState || this.saveInProgress) return;

        const stateToSave = this.pendingState;
        let state: Record<string, any>;
        try {
            state = JSON.parse(stateToSave);
        } catch (error) {
            console.error("[workspace-tile-canvas] Failed to parse state for saving", error);
            return;
        }

        this.saveInProgress = true;
        try {
            const csrfToken = getCsrfToken();
            const response = await fetch(this.saveUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
                },
                body: JSON.stringify({ state }),
            });

            if (!response.ok) {
                throw new Error(`Canvas state save failed with status ${response.status}`);
            }

            this.lastSavedState = stateToSave;
            if (this.pendingState === stateToSave) {
                this.pendingState = null;
            }
        } catch (error) {
            console.error("[workspace-tile-canvas] Failed to save state", error);
        } finally {
            this.saveInProgress = false;
        }
    };

    public initialize(): void {
        if (!this.element || this.root) return;

        if (!this.element.style.position) {
            this.element.style.position = "relative";
        }

        this.saveUrl = this.element.dataset.saveUrl || "";
        this.parseInitialState();
        if (this.saveUrl) {
            this.saveInterval = window.setInterval(() => {
                void this.savePendingState();
            }, SAVE_INTERVAL_MS);
        }

        this.root = createRoot(this.element);
        this.root.render(
            createElement(Excalidraw, {
                initialData: this.initialState || undefined,
                onChange: this.onExcalidrawChange,
            }),
        );
    }

    public destroy(): void {
        if (this.saveInterval !== null) {
            window.clearInterval(this.saveInterval);
            this.saveInterval = null;
        }

        if (this.root) {
            this.root.unmount();
            this.root = null;
        }

        this.pendingState = null;
        this.saveUrl = "";
        this.initialState = null;
        this.lastSavedState = "";

        super.destroy();
    }

}
