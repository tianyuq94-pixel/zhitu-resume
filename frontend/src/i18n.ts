import { ref } from 'vue'
import chinese from './locales/zh.json'

export type Language = 'en' | 'zh'
const messages: Record<string, string> = chinese
const english = Object.fromEntries(Object.entries(messages).map(([key, value]) => [value, key]))
const escapePattern = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const templates = Object.entries(messages).filter(([key]) => /\$\{[\w.]+\}/.test(key)).map(([key, value]) => {
  const fields: string[] = []
  const pattern = key.split(/(\$\{[\w.]+\})/).map(part => {
    if (part.startsWith('${')) { fields.push(part.slice(2, -1)); return '(.+?)' }
    return escapePattern(part)
  }).join('')
  return { pattern: new RegExp(`^${pattern}$`), value, fields }
})
const storageKey = 'zhitu-language'

function initialLanguage(): Language {
  try { return localStorage.getItem(storageKey) === 'zh' ? 'zh' : 'en' } catch { return 'en' }
}

export const locale = ref<Language>(initialLanguage())

export function t(value: unknown): string {
  if (value == null) return ''
  const text = String(value)
  if (locale.value !== 'zh') return english[text] ?? text
  if (messages[text] != null) return messages[text]
  for (const template of templates) {
    const match = template.pattern.exec(text)
    if (match) return template.value.replace(/\$\{([\w.]+)\}/g, (_, name: string) => match[template.fields.indexOf(name) + 1] ?? '')
  }
  return text
}

export function setLanguage(language: Language) {
  locale.value = language
  document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en-GB'
  try { localStorage.setItem(storageKey, language) } catch { /* In-memory switching still works. */ }
}

setLanguage(locale.value)
