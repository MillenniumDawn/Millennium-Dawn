import { initToc } from "./runtime";

type Cleanup = () => void;

let listenersRegistered = false;
let teardownPage: Cleanup = () => {};

function bootstrapPage(): void {
  teardownPage();
  teardownPage = initToc();
}

export function initTocPage(): void {
  if (listenersRegistered) return;
  listenersRegistered = true;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapPage, { once: true });
  } else {
    bootstrapPage();
  }
}
