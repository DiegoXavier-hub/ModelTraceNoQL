"use client";

import type { Locale } from "@/lib/i18n";

interface LanguageToggleProps {
  locale: Locale;
  onChange: (locale: Locale) => void;
}

export function LanguageToggle({ locale, onChange }: LanguageToggleProps) {
  const nextLocale: Locale = locale === "pt-BR" ? "en" : "pt-BR";
  const label =
    locale === "pt-BR"
      ? "Idioma: Português. Alternar para inglês"
      : "Language: English. Switch to Portuguese";

  return (
    <button
      type="button"
      className="language-toggle"
      aria-label={label}
      aria-pressed={locale === "en"}
      title={label}
      onClick={() => onChange(nextLocale)}
    >
      <span className={locale === "pt-BR" ? "active" : ""} aria-hidden="true">
        PT
      </span>
      <span className={locale === "en" ? "active" : ""} aria-hidden="true">
        EN
      </span>
    </button>
  );
}
