/** Split a space-separated class string (e.g. Tailwind bundles) into tokens for `classList`. */
export function splitClassList(classString: string): string[] {
  return classString.split(" ").filter(Boolean);
}
