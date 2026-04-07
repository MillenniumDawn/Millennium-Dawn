import type { OgPageData } from "./og-pages";
import type { BrandingAssets } from "./og-assets";
import { OG_FONT_FAMILY } from "./og-assets";
import { SITE_BRAND_TAGLINE, SITE_ORGANIZATION_NAME, SITE_TITLE } from "@/shared/config/site";

const OG_THEME = {
  overlayGradient:
    "linear-gradient(to bottom, rgba(26,32,44,0.40) 0%, rgba(26,32,44,0.78) 48%, rgba(26,32,44,0.96) 100%)",
  colors: {
    primaryText: "#ffffff",
    secondaryText: "#cbd5e0",
    tertiaryText: "#94a3b8",
  },
  spacing: {
    pagePadding: "60px 70px",
    homeGap: "20px",
    titleMarginBottom: "20px",
    footerMarginTop: "30px",
  },
  fontSizes: {
    // bumped all values to improve readability on social previews
    homeTitle: "72px",
    homeSubtitle: "40px",
    pageTitle: {
      default: "75px",
      compact: "52px",
    },
    pageDescription: "32px",
    footer: "24px",
  },
} as const;

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 1) + "…";
}

function buildHomeContent(logo: string) {
  return [
    {
      type: "div" as const,
      props: {
        style: {
          display: "flex",
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column" as const,
          gap: OG_THEME.spacing.homeGap,
        },
        children: [
          {
            type: "img" as const,
            props: {
              src: logo,
              width: 180,
              height: 180,
              style: { objectFit: "contain" as const },
            },
          },
          {
            type: "div" as const,
            props: {
              style: {
                fontSize: OG_THEME.fontSizes.homeTitle,
                fontWeight: 700,
                textAlign: "center" as const,
                lineHeight: 1.2,
              },
              children: SITE_ORGANIZATION_NAME,
            },
          },
          {
            type: "div" as const,
            props: {
              style: {
                fontSize: OG_THEME.fontSizes.homeSubtitle,
                fontWeight: 400,
                color: OG_THEME.colors.secondaryText,
                textAlign: "center" as const,
              },
              children: SITE_BRAND_TAGLINE,
            },
          },
        ],
      },
    },
  ];
}

function buildPageContent(logo: string, title: string, description: string) {
  const titleSize = title.length > 40 ? OG_THEME.fontSizes.pageTitle.compact : OG_THEME.fontSizes.pageTitle.default;

  return [
    {
      type: "div" as const,
      props: {
        style: {
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "flex-start",
        },
        children: {
          type: "img" as const,
          props: {
            src: logo,
            width: 72,
            height: 72,
            style: { objectFit: "contain" as const },
          },
        },
      },
    },
    {
      type: "div" as const,
      props: {
        style: { display: "flex", flex: 1 },
        children: [],
      },
    },
    {
      type: "div" as const,
      props: {
        style: {
          fontSize: titleSize,
          fontWeight: 700,
          lineHeight: 1.2,
          marginBottom: OG_THEME.spacing.titleMarginBottom,
        },
        children: title,
      },
    },
    {
      type: "div" as const,
      props: {
        style: {
          fontSize: OG_THEME.fontSizes.pageDescription,
          fontWeight: 400,
          color: OG_THEME.colors.secondaryText,
          lineHeight: 1.4,
        },
        children: description,
      },
    },
    {
      type: "div" as const,
      props: {
        style: {
          display: "flex",
          marginTop: OG_THEME.spacing.footerMarginTop,
          fontSize: OG_THEME.fontSizes.footer,
          color: OG_THEME.colors.tertiaryText,
        },
        children: SITE_TITLE,
      },
    },
  ];
}

export function buildOgMarkup(page: OgPageData, assets: BrandingAssets) {
  const isHome = page.slug === "index";
  const title = truncate(page.title, 80);
  const description = truncate(page.description, 160);

  return {
    type: "div" as const,
    props: {
      style: {
        width: "100%",
        height: "100%",
        display: "flex",
        backgroundImage: `url("${assets.hero}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      },
      children: {
        type: "div" as const,
        props: {
          style: {
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column" as const,
            backgroundImage: OG_THEME.overlayGradient,
            padding: OG_THEME.spacing.pagePadding,
            fontFamily: OG_FONT_FAMILY,
            color: OG_THEME.colors.primaryText,
          },
          children: isHome ? buildHomeContent(assets.logo) : buildPageContent(assets.logo, title, description),
        },
      },
    },
  };
}
