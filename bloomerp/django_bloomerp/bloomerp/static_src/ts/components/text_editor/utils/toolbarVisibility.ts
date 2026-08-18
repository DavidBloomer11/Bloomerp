export const TEXT_EDITOR_TOOLBAR_HIDDEN_COOKIE = "bloomerp-text-editor-toolbar-hidden";
export const TEXT_EDITOR_TOOLBAR_VISIBILITY_EVENT = "bloomerp:text-editor-toolbar-visibility-change";

const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;

export function isToolbarHiddenFromCookie(cookie: string): boolean {
    return cookie.split(";").some((entry) => {
        const separatorIndex = entry.indexOf("=");

        if (separatorIndex === -1) {
            return false;
        }

        const name = entry.slice(0, separatorIndex).trim();
        const value = entry.slice(separatorIndex + 1).trim();

        return name === TEXT_EDITOR_TOOLBAR_HIDDEN_COOKIE && value === "true";
    });
}

export function createToolbarVisibilityCookie(hidden: boolean): string {
    return `${TEXT_EDITOR_TOOLBAR_HIDDEN_COOKIE}=${hidden ? "true" : "false"}; path=/; max-age=${COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
}
