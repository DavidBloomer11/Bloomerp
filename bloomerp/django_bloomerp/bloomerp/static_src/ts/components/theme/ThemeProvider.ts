import BaseComponent from '../BaseComponent';
import {
    normalizeThemePreference,
    resolveEffectiveTheme,
    THEME_STORAGE_KEY,
    type ThemePreference,
} from './theme';

export default class ThemeProvider extends BaseComponent {
    private readonly mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    private preference: ThemePreference = 'auto';
    private optionButtons: HTMLButtonElement[] = [];
    private readonly optionHandlers = new Map<HTMLButtonElement, EventListener>();

    private readonly handleSystemThemeChange = (): void => {
        if (this.preference === 'auto') this.applyTheme();
    };

    private readonly handleStorageChange = (event: StorageEvent): void => {
        if (event.key !== THEME_STORAGE_KEY) return;
        this.preference = normalizeThemePreference(event.newValue);
        this.applyTheme();
    };

    public initialize(): void {
        if (!this.element) return;

        this.optionButtons = Array.from(
            this.element.querySelectorAll<HTMLButtonElement>('[data-theme-option]'),
        );
        this.preference = this.readPreference();

        this.optionButtons.forEach((button) => {
            const handler = (): void => {
                this.setPreference(normalizeThemePreference(button.dataset.themeOption ?? null));
            };
            this.optionHandlers.set(button, handler);
            button.addEventListener('click', handler);
        });

        this.mediaQuery.addEventListener('change', this.handleSystemThemeChange);
        window.addEventListener('storage', this.handleStorageChange);
        this.applyTheme();
    }

    public destroy(): void {
        this.optionHandlers.forEach((handler, button) => {
            button.removeEventListener('click', handler);
        });
        this.optionHandlers.clear();
        this.mediaQuery.removeEventListener('change', this.handleSystemThemeChange);
        window.removeEventListener('storage', this.handleStorageChange);
    }

    private readPreference(): ThemePreference {
        try {
            return normalizeThemePreference(window.localStorage.getItem(THEME_STORAGE_KEY));
        } catch (_error) {
            return 'auto';
        }
    }

    private setPreference(preference: ThemePreference): void {
        this.preference = preference;
        try {
            window.localStorage.setItem(THEME_STORAGE_KEY, preference);
        } catch (_error) {
            // Apply the preference for this page even when storage is unavailable.
        }
        this.applyTheme();
    }

    private applyTheme(): void {
        const effectiveTheme = resolveEffectiveTheme(this.preference, this.mediaQuery.matches);
        const root = document.documentElement;
        root.classList.toggle('dark', effectiveTheme === 'dark');
        root.dataset.theme = effectiveTheme;
        root.dataset.themePreference = this.preference;
        root.style.colorScheme = effectiveTheme;

        this.optionButtons.forEach((button) => {
            const selected = button.dataset.themeOption === this.preference;
            button.setAttribute('aria-checked', selected.toString());
            button.querySelector<HTMLElement>('[data-theme-check]')
                ?.classList.toggle('opacity-0', !selected);
        });

        window.dispatchEvent(new CustomEvent('bloomerp:theme-change', {
            detail: { preference: this.preference, theme: effectiveTheme },
        }));
    }
}
