import React, { createContext, useContext, useMemo, useState } from "react";
import type { Locale } from "./i18nCore";
import { getStoredLocale, storeLocale, translate } from "./i18nCore";

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nContextValue>({
  locale: "en",
  setLocale: () => {},
  t: (key: string) => key,
});

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locale, setLocaleState] = useState<Locale>(() => getStoredLocale());

  const setLocale = (next: Locale) => {
    setLocaleState(next);
    storeLocale(next);
  };

  const t = useMemo(
    () => (key: string, vars?: Record<string, string | number>) => translate(key, vars, locale),
    [locale],
  );

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
};

export const useI18n = () => useContext(I18nContext);
