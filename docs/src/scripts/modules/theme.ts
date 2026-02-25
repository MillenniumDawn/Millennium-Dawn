const DARK_CLASS = "dark-mode";
const LIGHT_CLASS = "light-mode";

function persistTheme(theme: "dark" | "light"): void {
  try {
    localStorage.setItem("theme", theme);
  } catch {
    // Ignore storage errors (private mode / blocked storage).
  }
}

export function initDarkModeToggle(): void {
  const html = document.documentElement;
  const button = document.querySelector<HTMLButtonElement>(".dark-mode-button");
  if (!button) return;

  const updateAria = () => {
    button.setAttribute("aria-pressed", html.classList.contains(DARK_CLASS) ? "true" : "false");
  };

  updateAria();

  button.addEventListener("click", () => {
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
  });
}
