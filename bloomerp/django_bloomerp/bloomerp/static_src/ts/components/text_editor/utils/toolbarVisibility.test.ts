import assert from 'node:assert/strict';
import test from 'node:test';

import {
    createToolbarVisibilityCookie,
    isToolbarHiddenFromCookie,
    TEXT_EDITOR_TOOLBAR_HIDDEN_COOKIE,
} from './toolbarVisibility.ts';

test('reads the hidden preference from a cookie string', () => {
    assert.equal(isToolbarHiddenFromCookie('session=abc; bloomerp-text-editor-toolbar-hidden=true'), true);
    assert.equal(isToolbarHiddenFromCookie('bloomerp-text-editor-toolbar-hidden=false'), false);
    assert.equal(isToolbarHiddenFromCookie('session=abc'), false);
});

test('creates a persistent cookie for the shared toolbar preference', () => {
    assert.equal(
        createToolbarVisibilityCookie(true),
        `${TEXT_EDITOR_TOOLBAR_HIDDEN_COOKIE}=true; path=/; max-age=31536000; SameSite=Lax`,
    );
});
