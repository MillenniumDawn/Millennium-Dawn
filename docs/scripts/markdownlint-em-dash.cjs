/**
 * Custom markdownlint rule: MD9999 (em-dash).
 *
 * Em dashes (—) are banned across the docs site. The team's voice rules
 * (AGENTS.md, "Writing voice") forbid them, and the changelog guide
 * (docs/src/content/resources/changelog-guide.md) already enforces the
 * rule for changelog entries. This rule extends the same check to all
 * Markdown content.
 *
 * Exempt: country content under docs/src/content/countries/ (long-form
 * descriptions use em dashes for literary effect) and dev diaries under
 * docs/src/content/devDiaries/ (human-authored, original voice). The team
 * has not agreed to scrub those. Tracked as a follow-up.
 *
 * Code is exempt: em dashes inside fenced blocks and inline code spans are
 * sample text, not prose, and are skipped.
 *
 * Disable per-line with `<!-- markdownlint-disable MD9999 -->`.
 */
"use strict";

// A fence opens with 3+ of ` or ~; the close must use the same char and be at
// least as long, so a shorter run inside the block doesn't close it.
const FENCE_RE = /^\s*(`{3,}|~{3,})/;
const INLINE_CODE_RE = /`+[^`\n]*`+/g;

// Blank out inline code spans, keeping length so em-dash columns stay accurate.
function maskInlineCode(line) {
  return line.replace(INLINE_CODE_RE, (match) => " ".repeat(match.length));
}

/** @type {import("markdownlint").Rule} */
module.exports = {
  names: ["MD9999", "no-em-dash"],
  description: "Em dashes (—) are banned. Use periods, commas, or parentheses instead.",
  tags: ["custom"],
  function: function MD9999(params, onError) {
    const name = params.name || "";
    // Exempt: country content (long-form literary descriptions) and dev
    // diaries (human-authored, Okazaki voice). Tracked as a follow-up.
    if (name.includes("/countries/") || name.startsWith("countries/")) return;
    if (name.includes("/devDiaries/") || name.startsWith("devDiaries/")) return;
    const lines = params.lines;
    let fence = null; // the open fence marker, e.g. "```" or "~~~~"
    for (let i = 0; i < lines.length; i++) {
      const fenceMatch = FENCE_RE.exec(lines[i]);
      if (fenceMatch) {
        const marker = fenceMatch[1];
        if (fence === null) {
          fence = marker;
        } else if (marker[0] === fence[0] && marker.length >= fence.length) {
          fence = null;
        }
        continue;
      }
      if (fence !== null) continue;
      const line = maskInlineCode(lines[i]);
      let column = line.indexOf("—");
      while (column !== -1) {
        onError({
          lineNumber: i + 1,
          detail: "Em dash (—) at column " + (column + 1) + ". Replace with a period, comma, or parentheses.",
          context: lines[i].trim(),
        });
        column = line.indexOf("—", column + 1);
      }
    }
  },
};
