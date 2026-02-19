import {
    readCssMsVar,
    readCssStringVar
} from './tokens.js';

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
        var observer = new ResizeObserver(update);
        observer.observe(header);
    }
}

function initMobileNavigation() {
    var toggle = document.querySelector('.nav-toggle');
    var nav = document.getElementById('main-nav');
    var header = document.querySelector('.site-header');
    if (!toggle || !nav || !header) return;

    var tabletMin = readCssStringVar('--bp-tablet-min', '769px');
    var desktopMQ = window.matchMedia('(min-width: ' + tabletMin + ')');
    var focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
    var closeAnimMs = readCssMsVar('--duration-nav-close', 320);
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
        return Array.prototype.slice.call(nav.querySelectorAll(focusableSelector))
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
        closeTimer = window.setTimeout(finishClose, closeAnimMs);

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

export {
    initHeaderHeightSync,
    initMobileNavigation
};
