import { isAbsolute, relative, resolve } from "node:path";

/** True if `candidate` is a path strictly inside `root` (no `..` escape). */
export function isContainedInRoot(root: string, candidate: string): boolean {
  const rel = relative(resolve(root), resolve(candidate));
  return rel !== "" && !rel.startsWith("..") && !isAbsolute(rel);
}
