import assert from 'node:assert/strict';
import test from 'node:test';

import { normalizeThemePreference, resolveEffectiveTheme } from './theme.ts';

test('normalizes supported and invalid stored preferences', () => {
    assert.equal(normalizeThemePreference('light'), 'light');
    assert.equal(normalizeThemePreference('dark'), 'dark');
    assert.equal(normalizeThemePreference('auto'), 'auto');
    assert.equal(normalizeThemePreference('sepia'), 'auto');
    assert.equal(normalizeThemePreference(null), 'auto');
});

test('resolves explicit themes independently of the system preference', () => {
    assert.equal(resolveEffectiveTheme('light', true), 'light');
    assert.equal(resolveEffectiveTheme('dark', false), 'dark');
});

test('resolves automatic theme from the current system preference', () => {
    assert.equal(resolveEffectiveTheme('auto', true), 'dark');
    assert.equal(resolveEffectiveTheme('auto', false), 'light');
});
