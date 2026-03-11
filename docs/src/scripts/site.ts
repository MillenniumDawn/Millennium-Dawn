import { applyThemePreference, initDarkModeToggle } from "@/features/theme/model";

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
  applyThemePreference();

  const cleanups: Cleanup[] = [];
  cleanups.push(initDarkModeToggle());
  teardownPage = () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      if (cleanup) cleanup();
    }
  };

  const runId = pageRunId;
  const [headerNavModule, uiHelpersModule] = await Promise.all([
    import("@/scripts/modules/header-nav"),
    import("@/scripts/modules/ui-helpers"),
  ]);

  if (runId !== pageRunId) return;

  cleanups.push(headerNavModule.initHeaderHeightSync());
  cleanups.push(headerNavModule.initMobileNavigation());
  cleanups.push(uiHelpersModule.initBackToTop());

  if (document.body.dataset.page === "dev-diary") {
    const contentMediaModule = await import("@/features/content-media/model");
    if (runId !== pageRunId) return;
    cleanups.push(contentMediaModule.initContentMediaLightbox());
  }
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
