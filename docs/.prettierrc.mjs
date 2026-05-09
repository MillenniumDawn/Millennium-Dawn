/** @type {import("prettier").Config} */
export default {
  plugins: ["prettier-plugin-astro"],
  overrides: [
    {
      files: "*.astro",
      options: {
        parser: "astro",
      },
    },
    {
      files: "*.md",
      options: {
        proseWrap: "preserve",
        printWidth: 120,
      },
    },
  ],
  printWidth: 120,
};
