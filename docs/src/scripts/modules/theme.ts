const DARK_CLASS = "dark-mode";
const LIGHT_CLASS = "light-mode";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

function readStoredTheme(): "dark" | "light" | null {
  try {
    const stored = localStorage.getItem("theme");
    return stored === "dark" || stored === "light" ? stored : null;
  } catch {
    return null;
  }
}

function persistTheme(theme: "dark" | "light"): void {
  try {
    localStorage.setItem("theme", theme);
  } catch {
    // Ignore storage errors (private mode / blocked storage).
  }
}

export function applyThemePreference(): void {
  const html = document.documentElement;
  const stored = readStoredTheme();
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;

  html.classList.remove(DARK_CLASS, LIGHT_CLASS);
  if (stored === "dark" || (!stored && prefersDark)) {
    html.classList.add(DARK_CLASS);
    return;
  }

  if (stored === "light") {
    html.classList.add(LIGHT_CLASS);
  }
}

export function initDarkModeToggle(): Cleanup {
  const html = document.documentElement;
  const button = document.querySelector<HTMLButtonElement>(".dark-mode-button");
  if (!button) return NOOP;

  const updateAria = () => {
    button.setAttribute("aria-pressed", html.classList.contains(DARK_CLASS) ? "true" : "false");
  };

  const onClick = () => {
    const wasDark = html.classList.contains(DARK_CLASS);
    html.classList.toggle(DARK_CLASS);
    html.classList.remove(LIGHT_CLASS);

    if (wasDark) {
      html.classList.add(LIGHT_CLASS);
      persistTheme("light");
    } else {
      persistTheme("dark");
    }

    updateAria();
  };

  updateAria();
  button.addEventListener("click", onClick);

  return () => {
    button.removeEventListener("click", onClick);
  };
}
