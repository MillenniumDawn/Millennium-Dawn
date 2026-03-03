export function stripMarkdownExt(id: string): string {
  return id.replace(/\.(md|mdx)$/i, "");
}
