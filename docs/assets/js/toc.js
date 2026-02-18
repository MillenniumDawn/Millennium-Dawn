(function () {
    'use strict';

    function escapeHtml(str) {
        var d = document.createElement('div');
        d.appendChild(document.createTextNode(str));
        return d.innerHTML;
    }

    function initToc() {
        var SCROLL_OFFSET = 120;
        var DRAWER_ANIM = 280;

        // DOM refs
        var sidebar = document.getElementById('toc-sidebar');
        var panel = document.getElementById('toc-panel');
        var nav = document.getElementById('toc-nav');
        var toggle = document.getElementById('toc-toggle');
        var closeBtn = document.getElementById('toc-close');
        var backdrop = document.getElementById('toc-backdrop');
        var progress = document.getElementById('toc-progress');
        if (!sidebar || !nav) return;

        // Collect headings
        var content = document.querySelector('.main-content');
        if (!content) return;

        var headings = content.querySelectorAll('h2, h3, h4');

        // Keep TOC hidden on pages without section headings.
        if (!headings.length) {
            document.body.classList.remove('has-toc');
            return;
        }

        sidebar.hidden = false;
        document.body.classList.add('has-toc');

        // Ensure every heading has an id
        headings.forEach(function (h, i) {
            if (!h.id) h.id = 'heading-' + i;
        });

        // Build nested tree (h2 -> h3 -> h4)
        var tree = [];
        var currentH2 = null;
        var currentH3 = null;

        headings.forEach(function (h) {
            var level = parseInt(h.tagName.charAt(1), 10);
            var item = { id: h.id, text: h.textContent.trim(), level: level, children: [] };

            if (level === 2) {
                currentH2 = item;
                currentH3 = null;
                tree.push(item);
            } else if (level === 3) {
                currentH3 = item;
                (currentH2 ? currentH2.children : tree).push(item);
            } else if (level === 4) {
                (currentH3 || currentH2 ? (currentH3 || currentH2).children : tree).push(item);
            }
        });

        // Render
        var sectionIdx = 0;

        function renderList(items, depth) {
            var cls = depth === 0 ? 'toc-sidebar__list' : 'toc-sidebar__sublist';
            var attrs = '';

            if (depth > 0) {
                attrs = ' data-toc-sublist="' + sectionIdx + '"';
                sectionIdx++;
            }

            var html = '<ul class="' + cls + '" role="list"' + attrs + '>';

            items.forEach(function (item) {
                var hasKids = item.children && item.children.length > 0;
                var itemCls = 'toc-sidebar__item';
                if (hasKids) itemCls += ' toc-sidebar__item--parent';

                var linkCls = 'toc-sidebar__link';
                if (depth === 1) linkCls += ' toc-sidebar__sublink';
                if (depth >= 2) linkCls += ' toc-sidebar__sublink toc-sidebar__sublink--deep';

                html += '<li class="' + itemCls + '" role="listitem">';

                if (hasKids) {
                    var idx = sectionIdx;
                    html += '<div class="toc-sidebar__row">';
                    html += '<a href="#' + item.id + '" class="' + linkCls + '"'
                        + ' data-toc-id="' + item.id + '"'
                        + ' title="' + escapeHtml(item.text) + '">'
                        + escapeHtml(item.text) + '</a>';
                    html += '<button class="toc-sidebar__expand"'
                        + ' aria-expanded="false"'
                        + ' aria-label="Expand: ' + escapeHtml(item.text) + '"'
                        + ' data-toc-expand="' + idx + '"'
                        + ' type="button">'
                        + '<svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12">'
                        + '<path d="M4.5 2l4 4-4 4" stroke="currentColor" stroke-width="1.5"'
                        + ' fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                        + '</svg></button>';
                    html += '</div>';
                    html += renderList(item.children, depth + 1);
                } else {
                    html += '<a href="#' + item.id + '" class="' + linkCls + '"'
                        + ' data-toc-id="' + item.id + '"'
                        + ' title="' + escapeHtml(item.text) + '">'
                        + escapeHtml(item.text) + '</a>';
                }

                html += '</li>';
            });

            html += '</ul>';
            return html;
        }

        nav.innerHTML = renderList(tree, 0);

        // Expand / collapse with measured height
        function toggleSublist(btn, sublist, open) {
            if (!sublist) return;
            btn.setAttribute('aria-expanded', open ? 'true' : 'false');

            if (open) {
                sublist.classList.add('is-expanded');
                sublist.style.maxHeight = sublist.scrollHeight + 'px';
                sublist.style.opacity = '1';

                var onEnd = function () {
                    sublist.style.maxHeight = 'none';
                    sublist.removeEventListener('transitionend', onEnd);
                };
                sublist.addEventListener('transitionend', onEnd);
            } else {
                sublist.style.maxHeight = sublist.scrollHeight + 'px';
                void sublist.offsetHeight; // force reflow
                sublist.style.maxHeight = '0';
                sublist.style.opacity = '0';

                var onEnd2 = function () {
                    sublist.classList.remove('is-expanded');
                    sublist.removeEventListener('transitionend', onEnd2);
                };
                sublist.addEventListener('transitionend', onEnd2);
            }
        }

        nav.querySelectorAll('.toc-sidebar__expand').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                var idx = btn.getAttribute('data-toc-expand');
                var sublist = nav.querySelector('[data-toc-sublist="' + idx + '"]');
                var isOpen = btn.getAttribute('aria-expanded') === 'true';
                toggleSublist(btn, sublist, !isOpen);
            });
        });

        // Scroll spy
        var allLinks = nav.querySelectorAll('.toc-sidebar__link');
        var headingEls = [];
        var currentActive = null;
        var rafPending = false;

        allLinks.forEach(function (a) {
            var el = document.getElementById(a.getAttribute('data-toc-id'));
            if (el) headingEls.push({ el: el, link: a });
        });

        function autoExpandAncestors(link) {
            var node = link.parentElement;
            while (node && node !== nav) {
                if (node.classList.contains('toc-sidebar__sublist')
                    && !node.classList.contains('is-expanded')) {
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

        function updateActive() {
            var active = null;
            for (var i = headingEls.length - 1; i >= 0; i--) {
                if (headingEls[i].el.getBoundingClientRect().top <= SCROLL_OFFSET) {
                    active = headingEls[i];
                    break;
                }
            }

            if (active === currentActive) return;

            if (currentActive) {
                currentActive.link.classList.remove('is-active');
                currentActive.link.removeAttribute('aria-current');
            }

            currentActive = active;

            if (active) {
                active.link.classList.add('is-active');
                active.link.setAttribute('aria-current', 'location');
                autoExpandAncestors(active.link);
                scrollTocIntoView(active.link);
            }
        }

        function updateProgress() {
            if (!progress) return;
            var docH = document.documentElement.scrollHeight - window.innerHeight;
            var pct = docH > 0 ? Math.min(100, ((window.scrollY || 0) / docH) * 100) : 0;
            progress.style.width = pct + '%';
        }

        function onScroll() {
            if (rafPending) return;
            rafPending = true;
            requestAnimationFrame(function () {
                rafPending = false;
                updateActive();
                updateProgress();
            });
        }

        window.addEventListener('scroll', onScroll, { passive: true });
        updateActive();
        updateProgress();

        // Mobile drawer
        var isDrawerOpen = false;
        var lastFocused = null;
        var desktopMQ = window.matchMedia('(min-width: 1100px)');
        var FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
        var scrollY_saved = 0;

        function getFocusableEls() {
            return Array.prototype.slice.call(panel.querySelectorAll(FOCUSABLE))
                .filter(function (el) { return el.offsetParent !== null; });
        }

        function openDrawer() {
            lastFocused = document.activeElement;
            isDrawerOpen = true;

            // Save scroll position for iOS scroll lock
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
                    var f = getFocusableEls();
                    if (f.length) f[0].focus();
                }
            }, 50);
        }

        function closeDrawer(restoreFocus) {
            isDrawerOpen = false;

            sidebar.classList.add('is-closing');
            sidebar.classList.remove('is-open');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-label', 'Open table of contents');
            document.body.classList.remove('toc-lock');
            document.body.style.top = '';
            // Restore scroll position
            window.scrollTo(0, scrollY_saved);

            setPageInert(false);

            setTimeout(function () {
                sidebar.classList.remove('is-closing');
            }, DRAWER_ANIM);

            if (restoreFocus !== false && lastFocused && lastFocused.focus) {
                lastFocused.focus();
            }
        }

        function setPageInert(inert) {
            var els = [
                document.getElementById('main-content'),
                document.querySelector('.site-header'),
                document.querySelector('.site-footer')
            ];
            els.forEach(function (el) {
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

        // Focus trap
        function trapFocus(e) {
            if (!isDrawerOpen || e.key !== 'Tab') return;
            var f = getFocusableEls();
            if (!f.length) return;

            var first = f[0];
            var last = f[f.length - 1];

            if (e.shiftKey) {
                if (document.activeElement === first) { e.preventDefault(); last.focus(); }
            } else {
                if (document.activeElement === last) { e.preventDefault(); first.focus(); }
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

        // Auto-close on breakpoint change
        function onBreakpoint() {
            if (desktopMQ.matches && isDrawerOpen) closeDrawer(false);
        }
        if (typeof desktopMQ.addEventListener === 'function') {
            desktopMQ.addEventListener('change', onBreakpoint);
        } else if (typeof desktopMQ.addListener === 'function') {
            desktopMQ.addListener(onBreakpoint);
        }

        // Smooth scroll for TOC links
        nav.addEventListener('click', function (e) {
            var link = e.target.closest('.toc-sidebar__link');
            if (!link) return;
            e.preventDefault();

            var targetId = link.getAttribute('data-toc-id');
            var target = document.getElementById(targetId);
            if (!target) return;

            var header = document.querySelector('.site-header');
            var offset = header ? header.offsetHeight + 16 : 80;
            var targetTop = target.getBoundingClientRect().top + window.pageYOffset - offset;

            var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            window.scrollTo({ top: targetTop, behavior: prefersReduced ? 'auto' : 'smooth' });

            if (history.replaceState) history.replaceState(null, '', '#' + targetId);

            target.setAttribute('tabindex', '-1');
            target.focus({ preventScroll: true });
        });

        // Expand section matching URL hash on load
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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initToc);
    } else {
        initToc();
    }
})();
