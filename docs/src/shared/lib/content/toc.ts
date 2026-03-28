export interface TocHeadingLike {
  depth: number;
  slug: string;
  text: string;
}

export interface TocTreeItem {
  id: string;
  text: string;
  depth: number;
  children: TocTreeItem[];
}

export interface TocBuildOptions {
  minDepth?: number;
  maxDepth?: number;
}

function normalizeHeadings(headings: TocHeadingLike[], options: TocBuildOptions): TocHeadingLike[] {
  const minDepth = options.minDepth ?? 2;
  const maxDepth = options.maxDepth ?? 6;

  return headings.filter((heading) => {
    const hasText = typeof heading.text === "string" && heading.text.trim().length > 0;
    const hasSlug = typeof heading.slug === "string" && heading.slug.trim().length > 0;
    return hasText && hasSlug && heading.depth >= minDepth && heading.depth <= maxDepth;
  });
}

export function buildTocTree(headings: TocHeadingLike[], options: TocBuildOptions = {}): TocTreeItem[] {
  const normalized = normalizeHeadings(headings, options);
  const tree: TocTreeItem[] = [];
  const stack: TocTreeItem[] = [];

  normalized.forEach((heading) => {
    const item: TocTreeItem = {
      id: heading.slug,
      text: heading.text.trim(),
      depth: heading.depth,
      children: [],
    };

    while (stack.length && stack[stack.length - 1].depth >= item.depth) {
      stack.pop();
    }

    if (!stack.length) {
      tree.push(item);
    } else {
      stack[stack.length - 1].children.push(item);
    }

    stack.push(item);
  });

  return tree;
}
