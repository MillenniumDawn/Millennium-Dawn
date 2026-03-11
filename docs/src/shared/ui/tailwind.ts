export const FOCUS_RING_CLASS = [
  "focus-visible:[outline:var(--focus-ring-width)_solid_var(--focus-ring-color)]",
  "focus-visible:[outline-offset:var(--focus-ring-offset)]",
].join(" ");

export const INVERSE_FOCUS_RING_CLASS = [
  "focus-visible:[outline:var(--focus-ring-width)_solid_var(--color-text-inverse)]",
  "focus-visible:[outline-offset:var(--focus-ring-offset)]",
].join(" ");

export const LAYOUT_CONTAINER_CLASS = [
  "mx-auto",
  "w-full",
  "max-w-[var(--container-max-width)]",
  "px-container",
  "phone:px-4",
].join(" ");

export const BASE_LINK_CLASS = [
  "text-primary",
  "underline-offset-2",
  "transition-colors",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
  "hover:text-primary-hover",
  "hover:underline",
  FOCUS_RING_CLASS,
].join(" ");

export const INHERIT_LINK_CLASS = [
  "text-inherit",
  "underline-offset-2",
  "transition-colors",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
  "hover:underline",
  FOCUS_RING_CLASS,
].join(" ");

export const PAGE_TITLE_CLASS = [
  "mb-lg",
  "border-b-[3px]",
  "border-primary",
  "pb-sm",
  "text-[clamp(1.75rem,2.5vw+1rem,2.5rem)]",
  "font-bold",
  "leading-heading",
  "text-text",
].join(" ");

export const SECTION_TITLE_CLASS = [
  "mt-xl",
  "mb-md",
  "text-[clamp(1.4rem,2vw+0.5rem,2rem)]",
  "font-bold",
  "leading-heading",
  "text-text",
].join(" ");

export const SUBSECTION_TITLE_CLASS = [
  "mb-md",
  "text-[clamp(1.15rem,1.5vw+0.3rem,1.5rem)]",
  "font-bold",
  "leading-heading",
  "text-text-secondary",
].join(" ");

export const MINOR_HEADING_CLASS = [
  "mb-md",
  "text-[1.15rem]",
  "font-bold",
  "leading-heading",
  "text-text-secondary",
].join(" ");

export const SMALL_HEADING_CLASS = [
  "mb-md",
  "text-base",
  "font-bold",
  "leading-heading",
  "text-text-secondary",
].join(" ");

export const BODY_TEXT_CLASS = [
  "mb-md",
  "text-[clamp(1rem,0.5vw+0.9rem,1.1rem)]",
  "leading-base",
  "text-text",
].join(" ");

export const LEAD_TEXT_CLASS = [
  "mt-0",
  "mb-md",
  "text-[1.03rem]",
  "leading-base",
  "text-text-secondary",
].join(" ");

export const MUTED_TEXT_CLASS = [
  "text-text-muted",
].join(" ");

export const LIST_CLASS = [
  "mb-md",
  "ml-lg",
  "list-disc",
].join(" ");

export const ORDERED_LIST_CLASS = [
  "mb-md",
  "ml-lg",
  "list-decimal",
].join(" ");

export const LIST_ITEM_CLASS = [
  "mb-xs",
  "text-[clamp(1rem,0.5vw+0.9rem,1.1rem)]",
  "leading-base",
  "text-text",
].join(" ");

export const BUTTON_BASE_CLASS = [
  "inline-flex",
  "min-h-11",
  "items-center",
  "justify-center",
  "gap-sm",
  "rounded",
  "border-0",
  "px-lg",
  "py-3",
  "text-[0.95rem]",
  "font-semibold",
  "no-underline",
  "transition-all",
  "duration-200",
  "ease-out",
  FOCUS_RING_CLASS,
].join(" ");

export const BUTTON_PRIMARY_CLASS = [
  BUTTON_BASE_CLASS,
  "border-2",
  "border-primary",
  "bg-primary",
  "text-text-inverse",
  "shadow-sm",
  "hover:-translate-y-0.5",
  "hover:border-primary-hover",
  "hover:opacity-90",
  "hover:text-text-inverse",
  "hover:no-underline",
  "hover:shadow-md",
  "active:translate-y-0",
].join(" ");

export const BUTTON_SECONDARY_CLASS = [
  BUTTON_BASE_CLASS,
  "bg-bg",
  "border",
  "border-border",
  "text-text",
  "shadow-sm",
  "hover:-translate-y-0.5",
  "hover:border-border-light",
  "hover:opacity-90",
  "hover:no-underline",
  "hover:shadow-md",
  "active:translate-y-0",
].join(" ");

export const BUTTON_OUTLINE_CLASS = [
  BUTTON_BASE_CLASS,
  "border-2",
  "border-border",
  "bg-transparent",
  "text-text",
  "shadow-sm",
  "hover:-translate-y-0.5",
  "hover:border-primary",
  "hover:text-primary",
  "hover:no-underline",
  "hover:shadow-md",
  "active:translate-y-0",
].join(" ");

export const PANEL_SURFACE_CLASS = [
  "rounded-lg",
  "border",
  "border-border-light",
  "bg-[radial-gradient(circle_at_top_left,var(--color-surface-muted-overlay),transparent_55%),var(--color-surface)]",
  "shadow-sm",
].join(" ");

export const CONTENT_GRID_CLASS = [
  "mt-md",
  "mb-xl",
  "grid",
  "grid-cols-[repeat(auto-fill,minmax(240px,1fr))]",
  "gap-md",
].join(" ");

export const CONTENT_CARD_CLASS = [
  PANEL_SURFACE_CLASS,
  "flex",
  "flex-col",
  "h-full",
  "gap-[0.4rem]",
  "p-md",
  "transition-all",
  "duration-200",
  "ease-out",
  "hover:-translate-y-0.5",
  "hover:border-border",
  "hover:shadow-md",
].join(" ");

export const CONTENT_CARD_KIND_CLASS = [
  "m-0",
  "text-[0.74rem]",
  "font-bold",
  "uppercase",
  "tracking-[0.06em]",
  "text-text-muted",
].join(" ");

export const CONTENT_CARD_TITLE_CLASS = [
  "m-0",
  "text-[1.06rem]",
  "font-bold",
  "leading-[1.3]",
  "text-text",
].join(" ");

export const CONTENT_CARD_TITLE_LINK_CLASS = [
  "text-inherit",
  "no-underline",
  "transition-colors",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
  "hover:text-primary",
  "hover:no-underline",
  FOCUS_RING_CLASS,
].join(" ");

export const CONTENT_CARD_DESCRIPTION_CLASS = [
  "m-0",
  "text-[0.94rem]",
  "leading-[1.6]",
  "text-text-secondary",
].join(" ");

export const CONTENT_CARD_META_CLASS = [
  "m-0",
  "text-[0.82rem]",
  "text-text-muted",
].join(" ");

export const SEARCH_INDEX_ROOT_CLASS = [
  "mt-lg",
  "grid",
  "gap-md",
].join(" ");

export const SEARCH_INDEX_PAGINATION_CLASS = [
  "mt-sm",
  "grid",
  "gap-sm",
  "rounded-lg",
  "border",
  "border-border-light",
  "bg-[linear-gradient(180deg,color-mix(in_srgb,var(--color-surface)_96%,transparent),color-mix(in_srgb,var(--color-primary-light)_22%,var(--color-surface)))]",
  "p-md",
  "shadow-sm",
  "phone:gap-3",
  "phone:p-[0.85rem]",
].join(" ");

export const SEARCH_INDEX_PAGINATION_SUMMARY_CLASS = [
  "flex",
  "flex-wrap",
  "items-center",
  "justify-between",
  "gap-x-sm",
  "gap-y-xs",
  "phone:flex-col",
  "phone:items-stretch",
].join(" ");

export const SEARCH_INDEX_PAGINATION_STATUS_CLASS = [
  "inline-flex",
  "min-h-8",
  "items-center",
  "justify-center",
  "whitespace-nowrap",
  "rounded-full",
  "bg-[color-mix(in_srgb,var(--color-primary-light)_72%,var(--color-surface))]",
  "px-[0.7rem]",
  "py-1",
  "text-[0.92rem]",
  "font-bold",
  "text-text",
  "phone:justify-center",
  "phone:text-center",
].join(" ");

export const SEARCH_INDEX_PAGINATION_RESULTS_CLASS = [
  "text-[0.88rem]",
  "text-text-secondary",
  "phone:text-center",
].join(" ");

export const SEARCH_INDEX_PAGINATION_CONTROLS_CLASS = [
  "grid",
  "grid-cols-[auto_1fr_auto]",
  "items-center",
  "gap-sm",
  "phone:grid-cols-1",
].join(" ");

export const SEARCH_INDEX_PAGINATION_PAGES_CLASS = [
  "flex",
  "min-w-0",
  "flex-wrap",
  "items-center",
  "justify-center",
  "gap-[0.35rem]",
  "phone:order-[-1]",
].join(" ");

export const SEARCH_INDEX_PAGINATION_NAV_BUTTON_CLASS = [
  "min-w-[7.5rem]",
  "justify-center",
  "whitespace-nowrap",
  "phone:w-full",
  "phone:min-w-0",
].join(" ");

export const SEARCH_INDEX_PAGINATION_PAGE_BUTTON_CLASS = [
  "inline-flex",
  "min-h-10",
  "min-w-10",
  "items-center",
  "justify-center",
  "rounded-full",
  "border",
  "border-border",
  "bg-surface",
  "px-[0.65rem]",
  "py-[0.35rem]",
  "text-[0.92rem]",
  "font-bold",
  "text-text-secondary",
  "shadow-sm",
  "transition-[transform,border-color,background-color,color,box-shadow]",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
  "hover:-translate-y-px",
  "hover:border-primary",
  "hover:text-primary",
  "aria-[current=page]:border-primary",
  "aria-[current=page]:bg-primary",
  "aria-[current=page]:text-text-inverse",
  "aria-[current=page]:shadow-md",
  "aria-[current=page]:hover:translate-y-0",
  "aria-[current=page]:hover:text-text-inverse",
  "focus-visible:[outline:var(--focus-ring-width)_solid_var(--color-primary)]",
  "focus-visible:[outline-offset:2px]",
  "phone:min-h-[2.35rem]",
  "phone:min-w-[2.35rem]",
  "phone:px-[0.55rem]",
].join(" ");

export const SEARCH_INDEX_PAGINATION_ELLIPSIS_CLASS = [
  "inline-flex",
  "min-h-10",
  "min-w-10",
  "items-center",
  "justify-center",
  "rounded-full",
  "px-[0.65rem]",
  "py-[0.35rem]",
  "text-[0.92rem]",
  "font-bold",
  "text-text-muted",
  "phone:min-h-[2.35rem]",
  "phone:min-w-[2.35rem]",
  "phone:px-[0.55rem]",
].join(" ");

export const SEARCH_INDEX_LABEL_CLASS = [
  "text-[0.95rem]",
  "font-semibold",
  "text-text-secondary",
].join(" ");

export const TRANSLATION_LIST_CLASS = [
  "m-0",
  "flex",
  "list-none",
  "flex-wrap",
  "gap-sm",
  "p-0",
].join(" ");

export const TRANSLATION_LINK_CLASS = [
  "inline-flex",
  "items-center",
  "gap-xs",
  "rounded",
  "border",
  "border-border-light",
  "bg-surface",
  "px-md",
  "py-2",
  "text-[0.875rem]",
  "font-medium",
  "text-text-secondary",
  "no-underline",
  "shadow-sm",
  "transition-[transform,border-color,color,box-shadow]",
  "duration-200",
  "ease-out",
  "hover:-translate-y-0.5",
  "hover:border-primary",
  "hover:text-primary",
  "hover:no-underline",
  "hover:shadow-md",
  FOCUS_RING_CLASS,
].join(" ");

export const SEARCH_INDEX_INPUT_CLASS = [
  "w-full",
  "max-w-[560px]",
  "rounded",
  "border",
  "border-border",
  "bg-surface",
  "px-[0.85rem]",
  "py-[0.65rem]",
  "text-text",
  "placeholder:text-text-muted",
  "shadow-sm",
  "transition-[border-color,box-shadow]",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
  "focus:border-primary",
  "focus:outline-none",
  "focus:ring-2",
  "focus:ring-primary-light",
].join(" ");

export const LIGHTBOX_LOCK_BODY_CLASS = [
  "fixed",
  "inset-x-0",
  "top-[var(--lightbox-scroll-top)]",
  "w-full",
  "overflow-hidden",
  "pr-[var(--lightbox-scrollbar-compensation)]",
  "touch-none",
].join(" ");

export const LIGHTBOX_TRIGGER_IMAGE_CLASS = [
  "cursor-zoom-in",
  "transition-[transform,opacity,box-shadow]",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
  "hover:opacity-95",
  FOCUS_RING_CLASS,
].join(" ");

export const LIGHTBOX_OVERLAY_CLASS = [
  "group",
  "fixed",
  "inset-0",
  "z-[4000]",
  "grid",
  "place-items-center",
  "overflow-hidden",
  "bg-[rgba(10,14,22,0.9)]",
  "opacity-0",
  "backdrop-blur-[8px]",
  "transition-opacity",
  "duration-[180ms]",
  "ease-out",
  "data-[state=open]:opacity-100",
].join(" ");

export const LIGHTBOX_CLOSE_BUTTON_CLASS = [
  "absolute",
  "right-4",
  "top-4",
  "z-[2]",
  "inline-flex",
  "min-h-11",
  "min-w-11",
  "items-center",
  "justify-center",
  "rounded-full",
  "border",
  "border-[color-mix(in_srgb,var(--color-border-light)_50%,transparent)]",
  "bg-[color-mix(in_srgb,var(--color-surface)_22%,transparent)]",
  "text-text-inverse",
  "shadow-sm",
  "opacity-0",
  "[transform:translateY(-0.5rem)_scale(0.96)]",
  "transition-[transform,opacity,background-color]",
  "duration-[180ms]",
  "ease-out",
  "group-data-[state=open]:opacity-100",
  "group-data-[state=open]:[transform:translateY(0)_scale(1)]",
  "hover:bg-[color-mix(in_srgb,var(--color-surface)_30%,transparent)]",
  FOCUS_RING_CLASS,
].join(" ");

export const LIGHTBOX_VIEWPORT_CLASS = [
  "grid",
  "h-screen",
  "w-screen",
  "place-items-center",
  "overflow-hidden",
  "p-[clamp(1rem,2vw,2rem)]",
  "touch-none",
].join(" ");

export const LIGHTBOX_CONTENT_CLASS = [
  "grid",
  "max-h-full",
  "max-w-full",
  "place-items-center",
  "opacity-0",
  "[transform:scale(0.985)]",
  "transition-[opacity,transform]",
  "duration-[180ms]",
  "ease-out",
  "will-change-[opacity,transform]",
  "group-data-[state=open]:opacity-100",
  "group-data-[state=open]:[transform:scale(1)]",
  "group-data-[state=closing]:opacity-0",
  "group-data-[state=closing]:[transform:scale(0.985)]",
].join(" ");

export const LIGHTBOX_IMAGE_CLASS = [
  "h-auto",
  "max-h-[92vh]",
  "w-auto",
  "max-w-[min(96vw,1600px)]",
  "select-none",
  "object-contain",
  "[-webkit-user-drag:none]",
  "[transform:translate3d(0,0,0)_scale(1)]",
  "[transform-origin:center_center]",
  "transition-none",
  "will-change-transform",
  "group-data-[zoomed=true]:cursor-grab",
  "group-data-[zoomed=false]:cursor-zoom-out",
].join(" ");

export const MARKDOWN_CLASSNAMES = {
  h1: PAGE_TITLE_CLASS,
  h2: SECTION_TITLE_CLASS,
  h3: SUBSECTION_TITLE_CLASS,
  h4: MINOR_HEADING_CLASS,
  h5: SMALL_HEADING_CLASS,
  h6: SMALL_HEADING_CLASS,
  p: BODY_TEXT_CLASS,
  a: BASE_LINK_CLASS,
  ul: LIST_CLASS,
  ol: ORDERED_LIST_CLASS,
  li: LIST_ITEM_CLASS,
  hr: "my-xl border-0 border-t border-border-light",
  blockquote: [
    "my-lg",
    "rounded-r",
    "border-l-4",
    "border-primary",
    "bg-primary-light",
    "px-lg",
    "py-md",
    "text-text-secondary",
  ].join(" "),
  inlineCode: [
    "inline-block",
    "max-w-full",
    "break-words",
    "rounded-[3px]",
    "bg-inline-code-bg",
    "px-[0.4em]",
    "py-[0.15em]",
    "font-mono",
    "text-[0.875em]",
    "text-inline-code-text",
    "hyphens-auto",
  ].join(" "),
  codeBlock: [
    "rounded-none",
    "bg-transparent",
    "p-0",
    "font-mono",
    "text-[0.875rem]",
    "text-code-text",
  ].join(" "),
  pre: [
    "mb-lg",
    "overflow-x-auto",
    "rounded",
    "border",
    "border-code-border",
    "bg-code-bg",
    "p-lg",
    "leading-[1.5]",
    "print:break-inside-avoid",
  ].join(" "),
  details: [
    "my-md",
    "rounded-lg",
    "border",
    "border-border",
    "bg-surface",
    "shadow-sm",
    "transition-[box-shadow,border-color]",
    "duration-[var(--transition-speed)]",
    "ease-[var(--transition-fn)]",
    "hover:border-text-muted",
    "open:border-text-muted",
    "open:shadow-md",
  ].join(" "),
  summary: [
    "flex",
    "cursor-pointer",
    "list-none",
    "items-center",
    "gap-sm",
    "rounded-lg",
    "border-b",
    "border-b-transparent",
    "bg-transparent",
    "px-lg",
    "py-md",
    "text-base",
    "font-semibold",
    "leading-[1.5]",
    "text-text",
    "marker:content-none",
    "[&::-webkit-details-marker]:hidden",
    "select-none",
    "transition-[background-color,border-color,color]",
    "duration-200",
    "ease-[var(--transition-fn)]",
    "hover:bg-[var(--surface-hover-current)]",
    "active:bg-[var(--surface-active-current)]",
    "[details[open]>&]:rounded-b-none",
    "[details[open]>&]:border-b-border",
    "[details[open]>&]:text-primary",
    FOCUS_RING_CLASS,
  ].join(" "),
  tableWrapper: [
    "table-wrapper",
    "mb-lg",
    "w-full",
    "overflow-x-auto",
    "[-webkit-overflow-scrolling:touch]",
    "mobile:[&>table]:min-w-full",
    "mobile:[&>table]:w-max",
  ].join(" "),
  table: [
    "w-full",
    "border",
    "border-table-border",
    "text-left",
    "text-[0.95rem]",
    "print:break-inside-avoid",
  ].join(" "),
  thead: "bg-table-header-bg",
  th: [
    "border",
    "border-table-border",
    "px-md",
    "py-3",
    "text-left",
    "font-bold",
    "text-text",
  ].join(" "),
  td: [
    "border",
    "border-border-light",
    "px-md",
    "py-3",
    "align-top",
  ].join(" "),
  image: [
    "h-auto",
    "max-w-full",
    "rounded",
    "print:break-inside-avoid",
  ].join(" "),
} as const;

export const INLINE_CODE_CLASS = MARKDOWN_CLASSNAMES.inlineCode;

export const SITE_HEADER_CLASS = [
  "site-header",
  "sticky",
  "top-0",
  "z-header",
  "w-full",
  "bg-surface",
  "border-b",
  "border-border-light",
  "py-4",
  "text-text",
  "shadow-sm",
  "backdrop-blur-[6px]",
  "backdrop-saturate-[1.2]",
  "transition-[box-shadow,background-color,padding]",
  "duration-[220ms]",
  "ease-[var(--transition-fn)]",
  "print:hidden",
].join(" ");

export const BACK_TO_TOP_CLASS = [
  "back-to-top",
  "fixed",
  "bottom-[calc(var(--space-xl)+60px)]",
  "right-lg",
  "z-back-to-top",
  "hidden",
  "size-12", // Guarantee 48x48 on mobile default
  "items-center",
  "justify-center",
  "rounded-full",
  "bg-primary",
  "text-text-inverse",
  "shadow-sm",
  "transition-[background,transform,opacity]",
  "duration-200",
  "ease-[var(--transition-fn)]",
  "hover:scale-[1.06]",
  "hover:shadow-md",
  "hover:bg-primary-hover",
  "[html.dark-mode_&]:bg-[linear-gradient(135deg,var(--color-header-bg),var(--color-header-bg-end))]",
  "[html.dark-mode_&]:hover:bg-[linear-gradient(135deg,var(--color-header-bg-end),var(--color-header-bg))]",
  "active:scale-95",
  "narrow:bottom-[calc(var(--space-xl)+60px)]",
  "narrow:right-lg",
  "wide:bottom-xl",
  "wide:right-xl",
  "wide:size-11", // On desktop 44x44 is enough
  "wide:hover:scale-100",
  "[&.is-visible]:flex",
  "print:hidden",
  INVERSE_FOCUS_RING_CLASS,
].join(" ");

export const TOC_SIDEBAR_CLASS = [
  "toc-sidebar",
  "fixed",
  "left-0",
  "top-0",
  "z-toc",
  "h-screen",
  "w-0",
  "pointer-events-none",
  "wide:relative",
  "wide:z-[1]",
  "wide:h-auto",
  "wide:w-[260px]",
  "wide:shrink-0",
  "wide:pointer-events-auto",
  "print:hidden",
].join(" ");

export const TOC_BACKDROP_CLASS = [
  "fixed",
  "inset-x-0",
  "bottom-0",
  "top-[var(--header-height)]",
  "z-toc-fab",
  "bg-overlay-scrim-45",
  "opacity-0",
  "pointer-events-none",
  "transition-opacity",
  "duration-toc",
  "ease-[cubic-bezier(0.4,0,0.2,1)]",
  "[.toc-sidebar.is-open_&]:pointer-events-auto",
  "[.toc-sidebar.is-open_&]:opacity-100",
  "[html.dark-mode_&]:bg-overlay-scrim-60",
  "wide:hidden",
].join(" ");

export const TOC_TOGGLE_CLASS = [
  "group",
  "fixed",
  "bottom-[calc(var(--space-xl)+60px)]",
  "left-lg",
  "z-toc-fab",
  "flex",
  "size-12",
  "items-center",
  "justify-center",
  "rounded-full",
  "border",
  "border-border",
  "bg-surface",
  "text-text",
  "shadow-sm",
  "transition-all",
  "duration-200",
  "ease-out",
  "hover:-translate-y-0.5",
  "hover:border-border",
  "hover:text-primary",
  "hover:shadow-md",
  "active:translate-y-0",
  "active:scale-95",
  "data-[nav-hidden=true]:pointer-events-none",
  "data-[nav-hidden=true]:opacity-0",
  "wide:hidden",
  FOCUS_RING_CLASS,
].join(" ");

export const TOC_PANEL_CLASS = [
  "fixed",
  "left-0",
  "top-[var(--header-height)]",
  "z-toc-panel",
  "flex",
  "h-[calc(100dvh-var(--header-height))]",
  "w-[260px]",
  "translate-x-[-100%]",
  "flex-col",
  "border-r",
  "border-border-light",
  "bg-surface",
  "transition-[transform,box-shadow]",
  "duration-toc",
  "ease-[cubic-bezier(0.4,0,0.2,1)]",
  "[.toc-sidebar.is-open_&]:translate-x-0",
  "[.toc-sidebar.is-open_&]:shadow-lg",
  "wide:sticky",
  "wide:top-[calc(var(--header-height)+1rem)]",
  "wide:h-[calc(100vh-var(--header-height)-1rem)]",
  "wide:w-full",
  "wide:translate-x-0",
  "wide:rounded-t-lg",
  "wide:shadow-none",
].join(" ");

export const TOC_NAV_CLASS = [
  "flex-1",
  "overflow-x-hidden",
  "overflow-y-auto",
  "py-sm",
  "[scrollbar-color:var(--color-border)_transparent]",
  "[scrollbar-width:thin]",
  "motion-reduce:scroll-auto",
  "[&::-webkit-scrollbar]:w-1",
  "[&::-webkit-scrollbar-thumb]:rounded",
  "[&::-webkit-scrollbar-thumb]:bg-border",
  "[&::-webkit-scrollbar-track]:bg-transparent",
].join(" ");

export const COUNTRY_CARD_ARTICLE_CLASS = [
  "relative",
  "isolate",
  "flex",
  "flex-col",
  "h-full",
  "min-h-[104px]",
  "gap-[0.25rem]",
  "overflow-hidden",
  "rounded-lg",
  "border",
  "border-border-light",
  "bg-surface",
  "p-md",
  "shadow-sm",
  "transition-all",
  "duration-200",
  "ease-out",
  "hover:-translate-y-0.5",
  "hover:border-border",
  "hover:shadow-md",
  "before:absolute",
  "before:inset-0",
  "before:-z-[1]",
  "before:bg-[linear-gradient(180deg,var(--color-focus-card-grad-1)_0%,var(--color-focus-card-grad-2)_42%,var(--color-focus-card-grad-3)_72%,var(--color-focus-card-grad-4)_100%)]",
].join(" ");

export const COUNTRY_FLAG_OVERLAY_CLASS = [
  "pointer-events-none",
  "absolute",
  "inset-0",
  "-z-[2]",
  "opacity-100",
  "[background-image:linear-gradient(135deg,var(--color-surface-muted-overlay)_0%,transparent_50%),var(--country-flag-image)]",
  "[background-position:center,center]",
  "[background-repeat:no-repeat,no-repeat]",
  "[background-size:cover,cover]",
  "[mask-image:linear-gradient(180deg,var(--color-mask-solid)_0%,var(--color-mask-mid)_70%,var(--color-mask-fade)_100%)]",
  "[html.dark-mode_&]:opacity-[0.8]",
].join(" ");
