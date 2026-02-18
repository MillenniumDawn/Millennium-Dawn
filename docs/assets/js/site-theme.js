(function (global) {
    'use strict';

    var MDSite = global.MDSite = global.MDSite || {};

    MDSite.applyInitialTheme = function applyInitialTheme() {
        var html = document.documentElement;
        var stored = null;

        try {
            stored = localStorage.getItem('theme');
        } catch (e) {
            stored = null;
        }

        if (stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            html.classList.add('dark-mode');
        } else if (stored === 'light') {
            html.classList.add('light-mode');
        }
    };

    MDSite.initDarkModeToggle = function initDarkModeToggle() {
        var html = document.documentElement;
        var btn = document.querySelector('.dark-mode-button');
        if (!btn) return;

        function updateAria() {
            btn.setAttribute('aria-pressed', html.classList.contains('dark-mode') ? 'true' : 'false');
        }

        updateAria();

        btn.addEventListener('click', function () {
            var wasDark = html.classList.contains('dark-mode');
            html.classList.toggle('dark-mode');
            html.classList.remove('light-mode');

            if (wasDark) {
                try {
                    localStorage.setItem('theme', 'light');
                } catch (e) {
                    // ignore storage errors (private mode, blocked storage)
                }
                html.classList.add('light-mode');
            } else {
                try {
                    localStorage.setItem('theme', 'dark');
                } catch (e) {
                    // ignore storage errors (private mode, blocked storage)
                }
            }

            updateAria();
        });
    };
})(window);
