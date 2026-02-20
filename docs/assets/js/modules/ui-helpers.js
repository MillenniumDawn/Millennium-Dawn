import { readCssPxVar } from './tokens.js';

function initBackToTop() {
    var btn = document.querySelector('.back-to-top');
    if (!btn) return;

    var threshold = readCssPxVar('--back-to-top-threshold', 400);

    function check() {
        btn.classList.toggle('is-visible', window.scrollY > threshold);
    }

    window.addEventListener('scroll', check, { passive: true });
    check();

    btn.addEventListener('click', function () {
        var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
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

export {
    initBackToTop,
    initResponsiveTables
};
