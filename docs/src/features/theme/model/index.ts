import {
  applyThemeMode,
  DARK_CLASS,
  normalizeStoredTheme,
  resolveThemeMode,
  THEME_STORAGE_KEY,
  type ThemeMode,
} from "@/shared/lib/theme";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

function readStoredTheme(): ThemeMode | null {
  try {
    return normalizeStoredTheme(localStorage.getItem(THEME_STORAGE_KEY));
  } catch {
    return null;
  }
}

function persistTheme(theme: ThemeMode): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Ignore storage errors (private mode / blocked storage).
  }
}

export function applyThemePreference(): void {
  const html = document.documentElement;
  const stored = readStoredTheme();
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyThemeMode(html, resolveThemeMode(stored, prefersDark));
}

export function initDarkModeToggle(): Cleanup {
  const html = document.documentElement;
  const button = document.querySelector<HTMLButtonElement>(".dark-mode-button");
  if (!button) return NOOP;

  const updateAria = () => {
    button.setAttribute("aria-pressed", html.classList.contains(DARK_CLASS) ? "true" : "false");
  };

  const onClick = () => {
    const nextTheme: ThemeMode = html.classList.contains(DARK_CLASS) ? "light" : "dark";
    applyThemeMode(html, nextTheme);
    persistTheme(nextTheme);
    updateAria();
  };

  updateAria();
  button.addEventListener("click", onClick);

  return () => {
    button.removeEventListener("click", onClick);
  };
}
