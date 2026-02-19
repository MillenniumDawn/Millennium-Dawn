function escapeHtml(str) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}

function ensureHeadingIds(headings) {
    headings.forEach(function (heading, index) {
        if (!heading.id) heading.id = 'heading-' + index;
    });
}

function buildTree(headings) {
    var tree = [];
    var currentH2 = null;
    var currentH3 = null;

    headings.forEach(function (heading) {
        var level = parseInt(heading.tagName.charAt(1), 10);
        var item = {
            id: heading.id,
            text: heading.textContent.trim(),
            level: level,
            children: []
        };

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

    return tree;
}

function renderNav(nav, tree) {
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
}

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

function bindExpandButtons(nav) {
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
}

export {
    ensureHeadingIds,
    buildTree,
    renderNav,
    toggleSublist,
    bindExpandButtons
};
