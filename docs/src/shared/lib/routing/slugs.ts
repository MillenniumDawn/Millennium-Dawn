export function stripMarkdownExt(id: string): string {
  return id.replace(/\.(md|mdx)$/i, "");
}

export function slugifyText(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function createUniqueSlugger(existingIds: Iterable<string> = []): (value: string, fallback?: string) => string {
  const used = new Set<string>();

  for (const existingId of existingIds) {
    const normalized = existingId.trim();
    if (normalized) used.add(normalized);
  }

  return (value: string, fallback = "section"): string => {
    const base = slugifyText(value) || slugifyText(fallback) || "section";
    let slug = base;
    let suffix = 2;

    while (used.has(slug)) {
      slug = `${base}-${suffix}`;
      suffix += 1;
    }

    used.add(slug);
    return slug;
  };
}
