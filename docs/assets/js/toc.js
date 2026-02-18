(function (global) {
    'use strict';

    var MDSite = global.MDSite = global.MDSite || {};

    function runIfFn(fn) {
        if (typeof fn === 'function') fn();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            runIfFn(MDSite.initToc);
        });
    } else {
        runIfFn(MDSite.initToc);
    }
})(window);
