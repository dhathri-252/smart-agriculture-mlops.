import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { translations } from './translations.js'

const STORAGE_KEY = 'sa_language'
/** All interface languages supported by the catalogue UI. */
export const SUPPORTED_LANGS = ['en', 'te', 'hi', 'ta', 'kn', 'ml', 'mr', 'bn']
const LanguageContext = createContext(null)

function detectInitialLanguage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (SUPPORTED_LANGS.includes(stored)) return stored
  } catch { /* storage unavailable — fall through */ }
  return 'en'
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(detectInitialLanguage)

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, lang) } catch { /* ignore */ }
    document.documentElement.lang = lang
  }, [lang])

  const value = useMemo(() => {
    const dict = translations[lang] || {}
    const enDict = translations.en || {}
    return {
      lang,
      setLang: (next) => setLang(SUPPORTED_LANGS.includes(next) ? next : 'en'),
      t: (key) => dict[key] ?? enDict[key] ?? key,
      /** Pick the active language from a bilingual/multilingual {en, te, ...} object. */
      pick: (obj) => {
        if (!obj) return ''
        if (typeof obj === 'string') return obj
        if (obj[lang]) return obj[lang]
        return obj.en ?? Object.values(obj).find(Boolean) ?? ''
      },
      /** Crop display name in the active language, with fallback info. */
      cropName: (item) => {
        if (!item) return { text: '', fallback: false, unverified: false, missing: false }
        const names = item.names || {}
        if (lang === 'en' || !names[lang]) {
          return {
            text: item.name_en || '',
            fallback: lang !== 'en',
            missing: lang !== 'en',
            unverified: false,
          }
        }
        const status = (item.name_status || {})[lang]
        return { text: names[lang], fallback: false, missing: false, unverified: status === 'unverified' }
      },
    }
  }, [lang])

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useTranslation() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useTranslation must be used inside <LanguageProvider>')
  return ctx
}
