// @ts-check

import { defineConfig } from "eslint/config";
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import eslintPluginAstro from "eslint-plugin-astro";
import globals from "globals";

export default defineConfig(
  // ── Base JS rules ──────────────────────────────────────────────
  eslint.configs.recommended,

  // ── TypeScript (type-checked) ──────────────────────────────────
  tseslint.configs.recommendedTypeChecked,
  tseslint.configs.stylisticTypeChecked,
  {
    files: ["**/*.{ts,tsx,mts,cts}"],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // ── Astro ──────────────────────────────────────────────────────
  ...eslintPluginAstro.configs.recommended,
  {
    files: ["**/*.astro"],
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // ── Global settings ────────────────────────────────────────────
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  // ── Rule overrides ─────────────────────────────────────────────
  {
    rules: {
      // Allow unused vars when prefixed with _
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
      // Allow empty arrow functions (NOOP pattern)
      "@typescript-eslint/no-empty-function": "off",
      // Overly strict for a docs site
      "@typescript-eslint/no-floating-promises": "off",
      "@typescript-eslint/no-misused-promises": "off",
    },
  },

  // ── Astro-specific overrides ──────────────────────────────────
  {
    files: ["**/*.astro"],
    rules: {
      // Astro JSX .map() returns trigger false positives
      "@typescript-eslint/no-unsafe-return": "off",
      "@typescript-eslint/no-unsafe-assignment": "off",
    },
  },

  // ── Disable type-checked rules for JS config files ────────────
  {
    files: ["**/*.js", "**/*.mjs"],
    ...tseslint.configs.disableTypeChecked,
  },

  // ── Ignores ────────────────────────────────────────────────────
  {
    ignores: ["dist/", "_site/", ".astro/", "node_modules/", "scripts/"],
  },
);
