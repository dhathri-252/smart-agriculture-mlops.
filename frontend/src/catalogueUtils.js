/**
 * Pure catalogue helpers — no React, no DOM. Tested with `node --test`.
 * Mirrors the backend's search/fallback rules so the UI behaves identically.
 */

export const LANGS = ['en', 'te', 'hi', 'ta', 'kn', 'ml', 'mr', 'bn']

/** Display name in `lang` with fallback to English; reports if fallback/missing. */
export function displayName(item, lang) {
  const names = item.names || {}
  if (lang === 'en' || !names[lang]) {
    return { text: item.name_en, lang: 'en', fallback: lang !== 'en', missing: !names[lang] && lang !== 'en' }
  }
  const status = (item.name_status || {})[lang]
  return { text: names[lang], lang, fallback: false, missing: false, unverified: status === 'unverified' }
}

/** True if `query` matches English or any local-language name (case-insensitive). */
export function matchesSearch(item, query) {
  const q = String(query || '').trim().toLowerCase()
  if (!q) return true
  const hay = [item.name_en, ...Object.values(item.names || {})]
  return hay.some((n) => String(n).toLowerCase().includes(q))
}

export function filterCatalogue(items, { category = '', search = '', modelOnly = false } = {}) {
  return (items || []).filter((c) => {
    if (category && !(c.categories || []).includes(category)) return false
    if (modelOnly && !c.model_supported) return false
    return matchesSearch(c, search)
  })
}

/** Language persistence helpers (same key as the app's LanguageContext). */
export const LANG_STORAGE_KEY = 'sa_language'
export const SUPPORTED_LANGS = new Set(LANGS)
export function normalizeLang(value) {
  return SUPPORTED_LANGS.has(value) ? value : 'en'
}
