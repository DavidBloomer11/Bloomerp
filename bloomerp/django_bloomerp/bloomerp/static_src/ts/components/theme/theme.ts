export const THEME_STORAGE_KEY = 'bloomerp_theme_preference';

export const THEME_PREFERENCES = ['light', 'dark', 'auto'] as const;

export type ThemePreference = typeof THEME_PREFERENCES[number];
export type EffectiveTheme = Exclude<ThemePreference, 'auto'>;

export function normalizeThemePreference(value: string | null): ThemePreference {
    return THEME_PREFERENCES.includes(value as ThemePreference)
        ? value as ThemePreference
        : 'auto';
}

export function resolveEffectiveTheme(
    preference: ThemePreference,
    systemPrefersDark: boolean,
): EffectiveTheme {
    if (preference === 'auto') {
        return systemPrefersDark ? 'dark' : 'light';
    }
    return preference;
}
