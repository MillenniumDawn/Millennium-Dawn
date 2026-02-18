(function (global) {
    'use strict';

    var MDSite = global.MDSite = global.MDSite || {};

    MDSite.initCodeHighlightingFallback = function initCodeHighlightingFallback() {
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
    };
})(window);
