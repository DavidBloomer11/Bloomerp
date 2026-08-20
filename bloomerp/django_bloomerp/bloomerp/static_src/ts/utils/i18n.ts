type CatalogValue = string | string[];

interface DjangoCatalogResponse {
    catalog?: Record<string, CatalogValue>;
    plural?: string | null;
}

declare global {
    interface Window {
        BLOOMERP_I18N_CATALOG_URL?: string;
    }
}

let catalog: Record<string, CatalogValue> = {};
let pluralIndex = (count: number): number => count === 1 ? 0 : 1;

export async function loadTranslations(): Promise<void> {
    const url = window.BLOOMERP_I18N_CATALOG_URL;
    if (!url) return;
    const response = await fetch(url, { credentials: "same-origin" });
    if (!response.ok) throw new Error(`Could not load translations (${response.status})`);
    const payload = await response.json() as DjangoCatalogResponse;
    catalog = payload.catalog ?? {};
    if (payload.plural) {
        const evaluatePlural = new Function("n", `return Number(${payload.plural});`) as (count: number) => number;
        pluralIndex = (count: number) => evaluatePlural(count);
    }
}

export function t(message: string): string {
    const translated = catalog[message];
    return typeof translated === "string" ? translated : message;
}

export function tn(singular: string, plural: string, count: number): string {
    const translated = catalog[singular];
    if (Array.isArray(translated)) return translated[pluralIndex(count)] ?? (count === 1 ? singular : plural);
    return count === 1 ? singular : plural;
}

export function tp(context: string, message: string): string {
    const translated = catalog[`${context}\u0004${message}`];
    return typeof translated === "string" ? translated : message;
}
