import { createHash } from "node:crypto";
import { buildThemeBootstrapScript } from "@/shared/lib/theme";

function sha256Base64(value: string): string {
  return createHash("sha256").update(value).digest("base64");
}

export function buildContentSecurityPolicy(): string {
  const themeScriptHash = sha256Base64(buildThemeBootstrapScript());

  return [
    "default-src 'self'",
    `script-src 'self' 'sha256-${themeScriptHash}'`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self'",
    "base-uri 'self'",
    "form-action 'none'",
    "frame-ancestors 'none'",
    "object-src 'none'",
  ].join("; ");
}
