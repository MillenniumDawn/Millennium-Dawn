(function () {
    'use strict';

    function applyInitialTheme() {
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
    }

    function initHeaderHeightSync() {
        var root = document.documentElement;
        var header = document.querySelector('.site-header');
        if (!root || !header) return;

        function update() {
            var height = Math.ceil(header.getBoundingClientRect().height);
            if (height > 0) root.style.setProperty('--header-height', height + 'px');
        }

        update();
        window.addEventListener('load', update);
        window.addEventListener('resize', update);
        header.addEventListener('navstatechange', update);

        if (typeof ResizeObserver !== 'undefined') {
            new ResizeObserver(update).observe(header);
        }
    }

    function initDarkModeToggle() {
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
    }

    function initMobileNavigation() {
        var toggle = document.querySelector('.nav-toggle');
        var nav = document.getElementById('main-nav');
        var header = document.querySelector('.site-header');
        if (!toggle || !nav || !header) return;

        var desktopMQ = window.matchMedia('(min-width: 769px)');
        var FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
        var CLOSE_ANIM_MS = 320;
        var closeTimer = null;

        function isDesktop() {
            return desktopMQ.matches;
        }

        function isOpen() {
            return nav.classList.contains('is-open');
        }

        function dispatchHeaderState() {
            header.dispatchEvent(new CustomEvent('navstatechange'));
        }

        function setToggleState(open) {
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            toggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
        }

        function setNavHidden(hidden) {
            if (hidden) {
                nav.setAttribute('hidden', '');
                nav.setAttribute('aria-hidden', 'true');
                nav.setAttribute('inert', '');
            } else {
                nav.removeAttribute('hidden');
                nav.removeAttribute('aria-hidden');
                nav.removeAttribute('inert');
            }
        }

        function finishClose() {
            nav.classList.remove('is-closing');
            if (!isDesktop() && !isOpen()) setNavHidden(true);
        }

        function getFocusableNavEls() {
            return Array.prototype.slice.call(nav.querySelectorAll(FOCUSABLE))
                .filter(function (el) { return el.offsetParent !== null; });
        }

        function openNav() {
            if (isDesktop()) return;

            if (closeTimer) {
                clearTimeout(closeTimer);
                closeTimer = null;
            }

            nav.classList.remove('is-closing');
            setNavHidden(false);

            requestAnimationFrame(function () {
                nav.classList.add('is-open');
            });

            header.classList.add('nav-is-open');
            document.body.classList.add('nav-lock');
            setToggleState(true);
            dispatchHeaderState();

            setTimeout(function () {
                var focusables = getFocusableNavEls();
                if (focusables.length) focusables[0].focus();
            }, 30);
        }

        function closeNav(restoreFocus) {
            nav.classList.remove('is-open');
            nav.classList.add('is-closing');
            header.classList.remove('nav-is-open');
            document.body.classList.remove('nav-lock');
            setToggleState(false);
            dispatchHeaderState();

            if (closeTimer) clearTimeout(closeTimer);
            closeTimer = window.setTimeout(finishClose, CLOSE_ANIM_MS);

            if (restoreFocus) toggle.focus();
        }

        function trapFocus(e) {
            if (isDesktop() || !isOpen() || e.key !== 'Tab') return;

            var focusables = getFocusableNavEls();
            if (!focusables.length) return;

            var first = focusables[0];
            var last = focusables[focusables.length - 1];

            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }

        function syncByViewport() {
            if (closeTimer) {
                clearTimeout(closeTimer);
                closeTimer = null;
            }

            if (isDesktop()) {
                nav.classList.remove('is-open', 'is-closing');
                header.classList.remove('nav-is-open');
                document.body.classList.remove('nav-lock');
                setNavHidden(false);
                setToggleState(false);
                dispatchHeaderState();
                return;
            }

            if (!isOpen()) {
                nav.classList.remove('is-closing');
                setNavHidden(true);
                setToggleState(false);
                header.classList.remove('nav-is-open');
                document.body.classList.remove('nav-lock');
                dispatchHeaderState();
            }
        }

        toggle.addEventListener('click', function () {
            isOpen() ? closeNav(false) : openNav();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && isOpen()) closeNav(true);
        });

        document.addEventListener('keydown', trapFocus);

        document.addEventListener('click', function (e) {
            if (isOpen() && !nav.contains(e.target) && !toggle.contains(e.target)) {
                closeNav(false);
            }
        });

        nav.addEventListener('click', function (e) {
            if (e.target.closest('a') && isOpen()) closeNav(false);
        });

        nav.addEventListener('transitionend', function (e) {
            if (e.propertyName === 'max-height' && !isOpen() && !isDesktop()) {
                finishClose();
            }
        });

        if (typeof desktopMQ.addEventListener === 'function') {
            desktopMQ.addEventListener('change', syncByViewport);
        } else if (typeof desktopMQ.addListener === 'function') {
            desktopMQ.addListener(syncByViewport);
        }

        syncByViewport();
    }

    function initBackToTop() {
        var btn = document.querySelector('.back-to-top');
        if (!btn) return;

        function check() {
            btn.classList.toggle('is-visible', window.scrollY > 400);
        }

        window.addEventListener('scroll', check, { passive: true });
        check();

        btn.addEventListener('click', function () {
            var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
        });
    }

    function initCodeHighlightingFallback() {
        var blocks = document.querySelectorAll('pre > code.language-hoiscript');
        if (!blocks.length) return;

        var KEYWORDS = {
            if: true, else: true, else_if: true, limit: true, hidden_effect: true,
            trigger: true, effect: true, random_list: true, random_owned_state: true,
            every_country: true, any_country: true, every_state: true, any_state: true,
            every_owned_state: true, any_owned_state: true, every_unit_leader: true,
            any_unit_leader: true, set_variable: true, add_to_variable: true,
            subtract_from_variable: true, multiply_variable: true, divide_variable: true,
            set_temp_variable: true, country_event: true, state_event: true,
            add_dynamic_modifier: true, remove_dynamic_modifier: true
        };
        var BUILTINS = {
            ROOT: true, FROM: true, PREV: true, THIS: true,
            yes: true, no: true, always: true
        };
        var TOKEN_RE = /#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b\d+(?:\.\d+)?\b|[{}()[\],]|=|\b[A-Za-z_][A-Za-z0-9_.-]*\b/gm;

        function escapeHtml(str) {
            return str
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }

        function classifyWord(word, source, endIdx) {
            if (BUILTINS[word]) return 'builtin';
            if (KEYWORDS[word.toLowerCase()]) return 'keyword';
            if (/^\d/.test(word)) return 'number';
            if (/^\s*=/.test(source.slice(endIdx))) return 'property';
            return 'name';
        }

        function highlightHoiscript(source) {
            var out = '';
            var lastIdx = 0;
            var match;

            TOKEN_RE.lastIndex = 0;
            while ((match = TOKEN_RE.exec(source)) !== null) {
                var token = match[0];
                var start = match.index;
                var end = TOKEN_RE.lastIndex;
                var type = '';

                out += escapeHtml(source.slice(lastIdx, start));

                if (token.charAt(0) === '#') {
                    type = 'comment';
                } else if (token.charAt(0) === '"' || token.charAt(0) === '\'') {
                    type = 'string';
                } else if (/^\d/.test(token)) {
                    type = 'number';
                } else if (token === '=') {
                    type = 'operator';
                } else if (/^[{}()[\],]$/.test(token)) {
                    type = 'punct';
                } else {
                    type = classifyWord(token, source, end);
                }

                out += '<span class="tok tok-' + type + '">' + escapeHtml(token) + '</span>';
                lastIdx = end;
            }

            out += escapeHtml(source.slice(lastIdx));
            return out;
        }

        blocks.forEach(function (code) {
            if (code.dataset.syntaxDone === '1') return;
            if (code.querySelector('span')) return;

            var raw = code.textContent || '';
            if (!raw.trim()) return;

            code.innerHTML = highlightHoiscript(raw);
            code.dataset.syntaxDone = '1';
        });
    }

    function initResponsiveTables() {
        var content = document.querySelector('.main-content');
        if (!content) return;

        var tables = content.querySelectorAll('table');
        tables.forEach(function (table) {
            if (table.closest('.table-wrapper') || !table.parentNode) return;

            var wrapper = document.createElement('div');
            wrapper.className = 'table-wrapper';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        });
    }
    function init() {
        initHeaderHeightSync();
        initDarkModeToggle();
        initMobileNavigation();
        initResponsiveTables();
        initCodeHighlightingFallback();
        initBackToTop();
    }

    applyInitialTheme();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
