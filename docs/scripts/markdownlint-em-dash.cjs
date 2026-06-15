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
 * Disable per-line with `<!-- markdownlint-disable MD9999 -->`.
 */
"use strict";

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
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      let column = line.indexOf("—");
      while (column !== -1) {
        onError({
          lineNumber: i + 1,
          detail: "Em dash (—) at column " + (column + 1) + ". Replace with a period, comma, or parentheses.",
          context: line.trim(),
          severity: "warning",
        });
        column = line.indexOf("—", column + 1);
      }
    }
  },
};
