export interface DevDiaryVersionParts {
  major: number;
  minor: number;
}

const VERSION_RE = /^v(\d+)\.(\d+)$/;

export function parseDevDiaryVersion(version: string): DevDiaryVersionParts {
  const match = VERSION_RE.exec(version);
  if (!match) {
    throw new Error(`Invalid dev diary version: ${version}`);
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
  };
}

/** Negative when `a` sorts before `b` in descending semver order. */
export function compareDevDiaryVersionsDesc(a: string, b: string): number {
  const va = parseDevDiaryVersion(a);
  const vb = parseDevDiaryVersion(b);
  if (va.major !== vb.major) {
    return vb.major - va.major;
  }
  return vb.minor - va.minor;
}
