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
  const needsToc = document.body.dataset.toc !== "off" && !!document.getElementById("toc-sidebar");
  const needsCardIndex = !!document.querySelector("[data-card-index], [data-changelog-index]");

  const [headerNavModule, themeModule, uiHelpersModule, tocModule, cardIndexModule] = await Promise.all([
    import("./modules/header-nav"),
    import("./modules/theme"),
    import("./modules/ui-helpers"),
    needsToc ? import("./modules/toc") : Promise.resolve(null),
    needsCardIndex ? import("./modules/changelog-index") : Promise.resolve(null),
  ]);

  if (runId !== pageRunId) return;

  const cleanups: Cleanup[] = [];

  cleanups.push(headerNavModule.initHeaderHeightSync());
  themeModule.initDarkModeToggle();
  cleanups.push(headerNavModule.initMobileNavigation());
  if (tocModule) cleanups.push(tocModule.initToc());
  if (cardIndexModule) cardIndexModule.initCardIndex();
  cleanups.push(uiHelpersModule.initBackToTop());

  teardownPage = () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      if (cleanup) cleanup();
    }
  };
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
