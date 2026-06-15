import { applyThemePreference, initDarkModeToggle } from "@/features/theme/model";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

let listenersRegistered = false;
let teardownPage: Cleanup = NOOP;

async function bootstrapPageAsync(): Promise<void> {
  teardownPage();
  teardownPage = NOOP;
  applyThemePreference();

  const cleanups: Cleanup[] = [];
  cleanups.push(initDarkModeToggle());
  teardownPage = () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      if (cleanup) cleanup();
    }
  };

  const [headerNavModule, uiHelpersModule, imageLightboxModule] = await Promise.all([
    import("@/scripts/modules/header-nav"),
    import("@/scripts/modules/ui-helpers"),
    import("@/features/image-lightbox"),
  ]);

  cleanups.push(headerNavModule.initHeaderHeightSync());
  cleanups.push(headerNavModule.initMobileNavigation());
  cleanups.push(uiHelpersModule.initBackToTop());
  cleanups.push(imageLightboxModule.initImageLightbox());
}

function bootstrapPage(): void {
  void bootstrapPageAsync();
}

export function initSite(): void {
  if (listenersRegistered) return;
  listenersRegistered = true;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapPage, { once: true });
  } else {
    bootstrapPage();
  }
}
