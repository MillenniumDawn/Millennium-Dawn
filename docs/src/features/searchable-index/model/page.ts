import { initCardIndex } from "./initCardIndex";

type Cleanup = () => void;

let listenersRegistered = false;
let teardownPage: Cleanup = () => {};

function bootstrapPage(): void {
  teardownPage();
  teardownPage = initCardIndex();
}

export function initCardIndexPage(): void {
  if (listenersRegistered) return;
  listenersRegistered = true;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapPage, { once: true });
  } else {
    bootstrapPage();
  }
}
