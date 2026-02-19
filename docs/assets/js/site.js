(function (global) {
    'use strict';

    var MDSite = global.MDSite = global.MDSite || {};

    function runIfFn(fn) {
        if (typeof fn === 'function') fn();
    }

    function init() {
        runIfFn(MDSite.initHeaderHeightSync);
        runIfFn(MDSite.initDarkModeToggle);
        runIfFn(MDSite.initMobileNavigation);
        runIfFn(MDSite.initResponsiveTables);
        runIfFn(MDSite.initCodeHighlightingFallback);
        runIfFn(MDSite.initBackToTop);
    }

    runIfFn(MDSite.applyInitialTheme);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(window);
