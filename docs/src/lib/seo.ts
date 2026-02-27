import { toAbsolute, withBase } from "./urls";

export type SeoImage = {
  path: string;
  width?: number;
  height?: number;
  alt?: string;
};

export type SeoMeta = {
  title: string;
  description: string;
  canonical: string;
  robots?: string;
  image?: SeoImage;
  seoEnabled: boolean;
};

const DEFAULT_DESCRIPTION =
  "Documentation for the Millennium Dawn: A Modern Day mod for the game Hearts of Iron IV.";

const DEFAULT_IMAGE: SeoImage = {
  path: "/assets/images/seo/og-image.png",
  width: 1200,
  height: 630,
  alt: "Millennium Dawn logo banner",
};

export function buildSeoMeta(input: {
  title: string;
  description?: string;
  canonicalPath: string;
  robots?: string;
  seo?: boolean;
  image?: SeoImage;
}): SeoMeta {
  const canonicalPath = input.canonicalPath || "/";
  return {
    title: input.title,
    description: input.description || DEFAULT_DESCRIPTION,
    canonical: toAbsolute(canonicalPath),
    robots: input.robots,
    seoEnabled: input.seo !== false,
    image: input.image
      ? { ...input.image, path: withBase(input.image.path) }
      : { ...DEFAULT_IMAGE, path: withBase(DEFAULT_IMAGE.path) },
  };
}
