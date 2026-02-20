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
        html.classList.remove('light-mode');
    } else if (stored === 'light') {
        html.classList.add('light-mode');
        html.classList.remove('dark-mode');
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
            html.classList.add('light-mode');
            try {
                localStorage.setItem('theme', 'light');
            } catch (e) {
                // ignore storage errors
            }
        } else {
            try {
                localStorage.setItem('theme', 'dark');
            } catch (e) {
                // ignore storage errors
            }
        }

        updateAria();
    });
}

export {
    applyInitialTheme,
    initDarkModeToggle
};
