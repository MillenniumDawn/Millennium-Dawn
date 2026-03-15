import { SITE_REPO_EDIT_BASE } from "../config/site";

export function getArticleFooterProps(entry: { id: string; data: { last_updated?: Date } }): {
  lastUpdated?: Date;
  editUrl?: string;
} {
  const lastUpdated = entry.data.last_updated;
  const editUrl = `${SITE_REPO_EDIT_BASE}/src/content/${entry.id}`;
  return { lastUpdated, editUrl };
}
