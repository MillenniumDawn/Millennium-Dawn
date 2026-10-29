export type ThemeMode = "dark" | "light";

export const THEME_STORAGE_KEY = "theme";
export const DARK_CLASS = "dark-mode";
export const LIGHT_CLASS = "light-mode";

export function normalizeStoredTheme(stored: string | null): ThemeMode | null {
  return stored === "dark" || stored === "light" ? stored : null;
}

export function resolveThemeMode(stored: ThemeMode | null, prefersDark: boolean): ThemeMode {
  return stored === "dark" || (!stored && prefersDark) ? "dark" : "light";
}

export function applyThemeMode(target: HTMLElement, mode: ThemeMode): void {
  target.classList.remove(DARK_CLASS, LIGHT_CLASS);
  target.classList.add(mode === "dark" ? DARK_CLASS : LIGHT_CLASS);
  target.style.colorScheme = mode;
}

export function buildThemeBootstrapScript(): string {
  return `(() => {
    const storageKey = ${JSON.stringify(THEME_STORAGE_KEY)};
    const darkClass = ${JSON.stringify(DARK_CLASS)};
    const lightClass = ${JSON.stringify(LIGHT_CLASS)};
    let stored = null;

    try {
      const raw = localStorage.getItem(storageKey);
      stored = raw === "dark" || raw === "light" ? raw : null;
    } catch {
      stored = null;
    }

    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const mode = stored === "dark" || (!stored && prefersDark) ? "dark" : "light";
    const html = document.documentElement;

    html.classList.remove(darkClass, lightClass);
    html.classList.add(mode === "dark" ? darkClass : lightClass);
    html.style.colorScheme = mode;
  })();`;
}
