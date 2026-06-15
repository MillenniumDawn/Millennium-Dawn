import { SITE_REPO_EDIT_BASE } from "@/shared/config/site";

const CONTENT_FILE_EXT = /\.(md|mdx)$/i;

function contentPathForEdit(collection: string, entryId: string, filePath?: string): string {
  if (filePath) {
    return filePath.replace(/\\/g, "/");
  }

  const filename = CONTENT_FILE_EXT.test(entryId) ? entryId : `${entryId}.md`;
  return `src/content/${collection}/${filename}`;
}

export function buildGitHubEditUrl(collection: string, entryId: string, filePath?: string): string {
  return `${SITE_REPO_EDIT_BASE}/${contentPathForEdit(collection, entryId, filePath)}`;
}

export function getArticleFooterProps(entry: {
  id: string;
  collection: string;
  filePath?: string;
  data: { last_updated?: Date };
}): {
  lastUpdated?: Date;
  editUrl: string;
} {
  return {
    lastUpdated: entry.data.last_updated,
    editUrl: buildGitHubEditUrl(entry.collection, entry.id, entry.filePath),
  };
}
