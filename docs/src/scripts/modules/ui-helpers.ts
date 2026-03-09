import { readCssPxVar } from "../../shared/lib/tokens";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

export function initBackToTop(): Cleanup {
  const button = document.querySelector<HTMLButtonElement>(".back-to-top");
  if (!button) return NOOP;

  const threshold = readCssPxVar("--back-to-top-threshold", 400);

  const check = () => {
    button.classList.toggle("is-visible", window.scrollY > threshold);
  };

  const onClick = () => {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: prefersReduced ? "auto" : "smooth" });
  };

  window.addEventListener("scroll", check, { passive: true });
  check();
  button.addEventListener("click", onClick);

  return () => {
    window.removeEventListener("scroll", check);
    button.removeEventListener("click", onClick);
  };
}
