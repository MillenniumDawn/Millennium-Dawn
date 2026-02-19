function initChangelogIndex() {
    var root = document.querySelector('[data-changelog-index]');
    if (!root) return;

    var cards = Array.prototype.slice.call(root.querySelectorAll('[data-changelog-card]'));
    if (!cards.length) return;

    var filterInput = root.querySelector('[data-changelog-filter]');
    var emptyState = root.querySelector('[data-changelog-empty]');
    var prevBtn = root.querySelector('[data-changelog-prev]');
    var nextBtn = root.querySelector('[data-changelog-next]');
    var status = root.querySelector('[data-changelog-status]');
    var pageSize = parseInt(root.getAttribute('data-page-size') || '6', 10);
    if (!Number.isFinite(pageSize) || pageSize < 1) pageSize = 6;

    var currentPage = 1;
    var activeQuery = '';

    function getMatches() {
        if (!activeQuery) return cards.slice();

        return cards.filter(function (card) {
            var haystack = (card.getAttribute('data-search') || '').toLowerCase();
            return haystack.indexOf(activeQuery) !== -1;
        });
    }

    function render() {
        var matches = getMatches();
        var totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
        if (currentPage > totalPages) currentPage = totalPages;
        if (currentPage < 1) currentPage = 1;

        var start = (currentPage - 1) * pageSize;
        var end = start + pageSize;

        cards.forEach(function (card) {
            card.hidden = true;
            card.style.display = 'none';
            card.setAttribute('aria-hidden', 'true');
        });
        matches.slice(start, end).forEach(function (card) {
            card.hidden = false;
            card.style.display = '';
            card.removeAttribute('aria-hidden');
        });

        if (emptyState) emptyState.hidden = matches.length > 0;
        if (prevBtn) prevBtn.disabled = currentPage <= 1 || matches.length === 0;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages || matches.length === 0;

        if (status) {
            if (matches.length) {
                status.textContent = 'Page ' + currentPage + ' of ' + totalPages + ' (' + matches.length + ' matches)';
            } else {
                status.textContent = 'No matches';
            }
        }
    }

    if (filterInput) {
        filterInput.addEventListener('input', function () {
            activeQuery = (filterInput.value || '').trim().toLowerCase();
            currentPage = 1;
            render();
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', function () {
            currentPage -= 1;
            render();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', function () {
            currentPage += 1;
            render();
        });
    }

    render();
}

export {
    initChangelogIndex
};
