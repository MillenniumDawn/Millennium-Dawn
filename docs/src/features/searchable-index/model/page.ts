import { initCardIndex } from "./initCardIndex";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

let listenersRegistered = false;
let teardownPage: Cleanup = NOOP;

function cleanupPage(): void {
  teardownPage();
  teardownPage = NOOP;
}

function bootstrapPage(): void {
  cleanupPage();
  teardownPage = initCardIndex();
}

export function initCardIndexPage(): void {
  if (listenersRegistered) return;
  listenersRegistered = true;

  document.addEventListener("astro:before-swap", cleanupPage);
  document.addEventListener("astro:page-load", bootstrapPage);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapPage, { once: true });
  } else {
    bootstrapPage();
  }
}
