import { en } from "./locales/en";
import { zh } from "./locales/zh";

export type Locale = "en" | "zh";

const LOCALE_STORAGE_KEY = "nyx_locale";

const dictionaries: Record<Locale, Record<string, string>> = {
  en,
  zh,
};

export function getStoredLocale(): Locale {
  if (typeof window === "undefined") return "en";
  const raw = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  if (raw === "en" || raw === "zh") return raw;
  return "en";
}

export function storeLocale(locale: Locale) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
}

export function translate(key: string, vars: Record<string, string | number> | undefined, locale: Locale): string {
  const dict = dictionaries[locale] ?? dictionaries.en;
  const template = dict[key] ?? dictionaries.en[key] ?? key;
  if (!vars) return template;
  return template.replace(/\{\{(\w+)\}\}/g, (_, name) => {
    const value = vars[name];
    return value === undefined || value === null ? "" : String(value);
  });
}
