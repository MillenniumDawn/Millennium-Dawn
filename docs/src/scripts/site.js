import {
    applyInitialTheme,
    initDarkModeToggle
} from './modules/theme.js';
import {
    initHeaderHeightSync,
    initMobileNavigation
} from './modules/header-nav.js';
import {
    initBackToTop,
    initResponsiveTables
} from './modules/ui-helpers.js';
import { initToc } from './modules/toc/index.js';

var MDSite = window.MDSite || {};
var hasStarted = false;
var initPromise = null;

function runIfFn(fn) {
    if (typeof fn === 'function') fn();
}

function runSafe(label, fn) {
    try {
        runIfFn(fn);
    } catch (error) {
        console.error('MDSite module failed (' + label + '):', error);
    }
}

function importAndInit(label, importer, initFnName) {
    return importer()
        .then(function (module) {
            runSafe(label, module[initFnName]);
        })
        .catch(function (error) {
            console.error('MDSite lazy module failed (' + label + '):', error);
        });
}

async function init() {
    if (hasStarted) return initPromise;
    hasStarted = true;

    initPromise = (async function () {
        runSafe('theme.bootstrap', applyInitialTheme);
        runSafe('header.height-sync', initHeaderHeightSync);
        runSafe('theme.toggle', initDarkModeToggle);
        runSafe('header.mobile-nav', initMobileNavigation);
        runSafe('ui.responsive-tables', initResponsiveTables);
        runSafe('ui.back-to-top', initBackToTop);

        if (document.body.dataset.toc !== 'off' && document.getElementById('toc-sidebar')) {
            runSafe('toc.runtime', initToc);
        }

        var lazyTasks = [];

        if (document.querySelector('pre > code.language-hoiscript')) {
            lazyTasks.push(
                importAndInit(
                    'code.highlight',
                    function () { return import('./modules/code-highlight.js'); },
                    'initCodeHighlightingFallback'
                )
            );
        }

        if (document.querySelector('[data-card-index], [data-changelog-index]')) {
            lazyTasks.push(
                importAndInit(
                    'card.index',
                    function () { return import('./modules/changelog-index.js'); },
                    'initCardIndex'
                )
            );
        }

        await Promise.all(lazyTasks);
    })();

    return initPromise;
}

MDSite.init = init;
MDSite.version = '2.0.0';
window.MDSite = MDSite;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
        init().catch(function (error) {
            console.error('MDSite initialization failed:', error);
        });
    });
} else {
    init().catch(function (error) {
        console.error('MDSite initialization failed:', error);
    });
}
