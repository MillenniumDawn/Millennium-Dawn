function readCssVar(name, fallback) {
    var root = document.documentElement;
    if (!root) return fallback;

    var value = getComputedStyle(root).getPropertyValue(name).trim();
    return value || fallback;
}

function parseMs(value, fallback) {
    if (typeof value !== 'string' || !value) return fallback;

    var normalized = value.trim().toLowerCase();
    if (normalized.endsWith('ms')) {
        var ms = parseFloat(normalized.slice(0, -2));
        return Number.isFinite(ms) ? ms : fallback;
    }

    if (normalized.endsWith('s')) {
        var seconds = parseFloat(normalized.slice(0, -1));
        return Number.isFinite(seconds) ? seconds * 1000 : fallback;
    }

    var raw = parseFloat(normalized);
    return Number.isFinite(raw) ? raw : fallback;
}

function parsePx(value, fallback) {
    if (typeof value !== 'string' || !value) return fallback;
    var px = parseFloat(value);
    return Number.isFinite(px) ? px : fallback;
}

function readCssMsVar(name, fallback) {
    return parseMs(readCssVar(name, ''), fallback);
}

function readCssPxVar(name, fallback) {
    return parsePx(readCssVar(name, ''), fallback);
}

function readCssStringVar(name, fallback) {
    return readCssVar(name, fallback);
}

export {
    readCssMsVar,
    readCssPxVar,
    readCssStringVar
};
