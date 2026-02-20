import {
    ensureHeadingIds,
    buildTree,
    renderNav,
    bindExpandButtons,
    toggleSublist
} from './render.js';
import {
    readCssMsVar,
    readCssPxVar,
    readCssStringVar
} from '../tokens.js';

function initToc() {
    var sidebar = document.getElementById('toc-sidebar');

    if (document.body.dataset.toc === 'off') {
        document.body.classList.remove('has-toc');
        if (sidebar) sidebar.hidden = true;
        return;
    }

    var scrollOffset = readCssPxVar('--toc-scroll-offset', 120);
    var drawerAnimMs = readCssMsVar('--duration-toc-drawer', 280);
    var wideMin = readCssStringVar('--bp-wide-min', '1100px');

    var panel = document.getElementById('toc-panel');
    var nav = document.getElementById('toc-nav');
    var toggle = document.getElementById('toc-toggle');
    var closeBtn = document.getElementById('toc-close');
    var backdrop = document.getElementById('toc-backdrop');
    var progress = document.getElementById('toc-progress');
    if (!sidebar || !panel || !nav) return;

    var content = document.querySelector('.main-content');
    if (!content) return;

    var headings = Array.prototype.slice.call(content.querySelectorAll('h2, h3, h4'));
    if (!headings.length) {
        document.body.classList.remove('has-toc');
        sidebar.hidden = true;
        return;
    }

    sidebar.hidden = false;
    document.body.classList.add('has-toc');

    ensureHeadingIds(headings);
    renderNav(nav, buildTree(headings));
    bindExpandButtons(nav);

    var allLinks = Array.prototype.slice.call(nav.querySelectorAll('.toc-sidebar__link'));
    var headingEntries = [];
    var entryById = {};
    var currentActive = null;

    allLinks.forEach(function (link) {
        var id = link.getAttribute('data-toc-id');
        var headingEl = document.getElementById(id);
        if (!headingEl) return;

        var entry = { el: headingEl, link: link };
        headingEntries.push(entry);
        entryById[id] = entry;
    });

    if (!headingEntries.length) return;

    function autoExpandAncestors(link) {
        var node = link.parentElement;
        while (node && node !== nav) {
            if (node.classList.contains('toc-sidebar__sublist') && !node.classList.contains('is-expanded')) {
                var idx = node.getAttribute('data-toc-sublist');
                var btn = nav.querySelector('[data-toc-expand="' + idx + '"]');
                if (btn) toggleSublist(btn, node, true);
            }
            node = node.parentElement;
        }
    }

    function scrollTocIntoView(link) {
        var navRect = nav.getBoundingClientRect();
        var linkRect = link.getBoundingClientRect();
        if (linkRect.top < navRect.top || linkRect.bottom > navRect.bottom) {
            link.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }

    function setActive(nextActive) {
        if (nextActive === currentActive) return;

        if (currentActive) {
            currentActive.link.classList.remove('is-active');
            currentActive.link.removeAttribute('aria-current');
        }

        currentActive = nextActive || null;

        if (currentActive) {
            currentActive.link.classList.add('is-active');
            currentActive.link.setAttribute('aria-current', 'location');
            autoExpandAncestors(currentActive.link);
            scrollTocIntoView(currentActive.link);
        }
    }

    function updateProgress() {
        if (!progress) return;
        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        var pct = docHeight > 0 ? Math.min(100, ((window.scrollY || 0) / docHeight) * 100) : 0;
        progress.style.width = pct + '%';
    }

    function findActiveFallback() {
        var active = null;
        for (var i = headingEntries.length - 1; i >= 0; i--) {
            if (headingEntries[i].el.getBoundingClientRect().top <= scrollOffset) {
                active = headingEntries[i];
                break;
            }
        }
        return active || headingEntries[0] || null;
    }

    var visibleHeadings = new Map();
    var observer = null;

    function pickVisibleActive() {
        if (!visibleHeadings.size) {
            if ((window.scrollY || 0) < 32) return headingEntries[0] || null;
            return currentActive || findActiveFallback();
        }

        var bestEntry = null;
        var bestDistance = Number.POSITIVE_INFINITY;

        visibleHeadings.forEach(function (top, id) {
            var entry = entryById[id];
            if (!entry) return;
            var distance = Math.abs(top - scrollOffset);
            if (distance < bestDistance) {
                bestDistance = distance;
                bestEntry = entry;
            }
        });

        return bestEntry || currentActive || findActiveFallback();
    }

    if (typeof IntersectionObserver !== 'undefined') {
        observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    visibleHeadings.set(entry.target.id, entry.boundingClientRect.top);
                } else {
                    visibleHeadings.delete(entry.target.id);
                }
            });
            setActive(pickVisibleActive());
        }, {
            root: null,
            rootMargin: '-' + scrollOffset + 'px 0px -55% 0px',
            threshold: [0, 1]
        });

        headingEntries.forEach(function (entry) {
            observer.observe(entry.el);
        });
        setActive(headingEntries[0]);
    } else {
        setActive(findActiveFallback());
    }

    var rafPending = false;
    function onScroll() {
        if (rafPending) return;
        rafPending = true;
        requestAnimationFrame(function () {
            rafPending = false;
            if (!observer) setActive(findActiveFallback());
            updateProgress();
        });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () {
        if (!observer) setActive(findActiveFallback());
        updateProgress();
    });
    updateProgress();

    var isDrawerOpen = false;
    var lastFocused = null;
    var desktopMQ = window.matchMedia('(min-width: ' + wideMin + ')');
    var focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
    var scrollY_saved = 0;

    function getFocusableEls() {
        return Array.prototype.slice.call(panel.querySelectorAll(focusableSelector))
            .filter(function (el) { return el.offsetParent !== null; });
    }

    function setPageInert(inert) {
        var elements = [
            document.getElementById('main-content'),
            document.querySelector('.site-header'),
            document.querySelector('.site-footer')
        ];

        elements.forEach(function (el) {
            if (!el) return;
            if (inert) {
                el.setAttribute('inert', '');
                el.setAttribute('aria-hidden', 'true');
            } else {
                el.removeAttribute('inert');
                el.removeAttribute('aria-hidden');
            }
        });
    }

    function openDrawer() {
        if (!toggle) return;
        lastFocused = document.activeElement;
        isDrawerOpen = true;

        scrollY_saved = window.scrollY || window.pageYOffset;
        sidebar.classList.add('is-open');
        toggle.setAttribute('aria-expanded', 'true');
        toggle.setAttribute('aria-label', 'Close table of contents');
        document.body.classList.add('toc-lock');
        document.body.style.top = '-' + scrollY_saved + 'px';
        setPageInert(true);

        setTimeout(function () {
            if (closeBtn) closeBtn.focus();
            else {
                var focusables = getFocusableEls();
                if (focusables.length) focusables[0].focus();
            }
        }, 40);
    }

    function closeDrawer(restoreFocus) {
        if (!toggle) return;
        isDrawerOpen = false;

        sidebar.classList.add('is-closing');
        sidebar.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-label', 'Open table of contents');
        document.body.classList.remove('toc-lock');
        document.body.style.top = '';
        window.scrollTo(0, scrollY_saved);
        setPageInert(false);

        setTimeout(function () {
            sidebar.classList.remove('is-closing');
        }, drawerAnimMs);

        if (restoreFocus !== false && lastFocused && typeof lastFocused.focus === 'function') {
            lastFocused.focus();
        }
    }

    function trapFocus(e) {
        if (!isDrawerOpen || e.key !== 'Tab') return;
        var focusables = getFocusableEls();
        if (!focusables.length) return;

        var first = focusables[0];
        var last = focusables[focusables.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    }

    if (toggle) toggle.addEventListener('click', function () { isDrawerOpen ? closeDrawer() : openDrawer(); });
    if (closeBtn) closeBtn.addEventListener('click', function () { closeDrawer(); });
    if (backdrop) backdrop.addEventListener('click', function () { if (isDrawerOpen) closeDrawer(); });

    nav.addEventListener('click', function (e) {
        if (e.target.closest('.toc-sidebar__link') && isDrawerOpen) closeDrawer(false);
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && isDrawerOpen) closeDrawer();
    });
    document.addEventListener('keydown', trapFocus);

    function onBreakpoint() {
        if (desktopMQ.matches && isDrawerOpen) closeDrawer(false);
    }

    if (typeof desktopMQ.addEventListener === 'function') {
        desktopMQ.addEventListener('change', onBreakpoint);
    } else if (typeof desktopMQ.addListener === 'function') {
        desktopMQ.addListener(onBreakpoint);
    }

    nav.addEventListener('click', function (e) {
        var link = e.target.closest('.toc-sidebar__link');
        if (!link) return;
        e.preventDefault();

        var targetId = link.getAttribute('data-toc-id');
        var target = document.getElementById(targetId);
        if (!target) return;

        var header = document.querySelector('.site-header');
        var offset = header ? header.offsetHeight + 16 : scrollOffset;
        var targetTop = target.getBoundingClientRect().top + window.pageYOffset - offset;
        var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({ top: targetTop, behavior: prefersReduced ? 'auto' : 'smooth' });

        if (history.replaceState) history.replaceState(null, '', '#' + targetId);

        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
    });

    if (window.location.hash) {
        try {
            var hashId = window.location.hash.slice(1);
            var hashLink = nav.querySelector('[data-toc-id="' + hashId + '"]');
            if (hashLink) autoExpandAncestors(hashLink);
        } catch (e) {
            // ignore invalid selectors
        }
    }
}

export {
    initToc
};
