export function resolveToc(raw: string | undefined): "auto" | "off" {
  return raw === "off" ? "off" : "auto";
}
