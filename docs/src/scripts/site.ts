import { applyThemePreference, initDarkModeToggle } from "../features/theme/model";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

let listenersRegistered = false;
let teardownPage: Cleanup = NOOP;
let pageRunId = 0;

function cleanupPage(): void {
  pageRunId += 1;
  teardownPage();
  teardownPage = NOOP;
}

async function bootstrapPageAsync(): Promise<void> {
  cleanupPage();
  const runId = pageRunId;
  applyThemePreference();

  const cleanups: Cleanup[] = [];
  cleanups.push(initDarkModeToggle());
  teardownPage = () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      if (cleanup) cleanup();
    }
  };

  const needsToc = document.body.dataset.toc !== "off" && !!document.getElementById("toc-sidebar");
  const needsCardIndex = !!document.querySelector("[data-card-index]");

  const [headerNavModule, uiHelpersModule, tocModule, cardIndexModule] = await Promise.all([
    import("./modules/header-nav"),
    import("./modules/ui-helpers"),
    needsToc ? import("../features/toc/model") : Promise.resolve(null),
    needsCardIndex ? import("../features/searchable-index/model") : Promise.resolve(null),
  ]);

  if (runId !== pageRunId) return;

  cleanups.push(headerNavModule.initHeaderHeightSync());
  cleanups.push(headerNavModule.initMobileNavigation());
  if (tocModule) cleanups.push(tocModule.initToc());
  if (cardIndexModule) cleanups.push(cardIndexModule.initCardIndex());
  cleanups.push(uiHelpersModule.initBackToTop());
}

function bootstrapPage(): void {
  void bootstrapPageAsync();
}

export function initSite(): void {
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
