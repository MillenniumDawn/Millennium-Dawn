import { readCssPxVar } from "./tokens";

export function initBackToTop(): void {
  const button = document.querySelector<HTMLButtonElement>(".back-to-top");
  if (!button) return;

  const threshold = readCssPxVar("--back-to-top-threshold", 400);

  const check = () => {
    button.classList.toggle("is-visible", window.scrollY > threshold);
  };

  window.addEventListener("scroll", check, { passive: true });
  check();

  button.addEventListener("click", () => {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" });
  });
}
