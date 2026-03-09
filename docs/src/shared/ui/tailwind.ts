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
  "transition-[background-color,box-shadow,transform,border-color]",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
  FOCUS_RING_CLASS,
].join(" ");

export const BUTTON_PRIMARY_CLASS = [
  BUTTON_BASE_CLASS,
  "border-2",
  "border-primary",
  "bg-primary",
  "text-text-inverse",
  "shadow-md",
  "hover:-translate-y-0.5",
  "hover:border-primary-hover",
  "hover:bg-primary-hover",
  "hover:text-text-inverse",
  "hover:no-underline",
  "hover:shadow-sm",
  "active:translate-y-0",
].join(" ");

export const BUTTON_SECONDARY_CLASS = [
  BUTTON_BASE_CLASS,
  "bg-text-muted",
  "text-text-inverse",
  "hover:-translate-y-0.5",
  "hover:bg-text-secondary",
  "hover:text-text-inverse",
  "hover:no-underline",
  "hover:shadow-sm",
  "active:translate-y-0",
].join(" ");

export const BUTTON_OUTLINE_CLASS = [
  BUTTON_BASE_CLASS,
  "border-2",
  "border-overlay-inverse-30",
  "bg-transparent",
  "text-text-inverse",
  "hover:-translate-y-0.5",
  "hover:border-text-inverse",
  "hover:bg-overlay-inverse-10",
  "hover:text-text-inverse",
  "hover:no-underline",
  "hover:shadow-sm",
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
  "grid",
  "gap-[0.4rem]",
  "p-md",
  "transition-[transform,box-shadow,border-color]",
  "duration-[var(--transition-speed)]",
  "ease-[var(--transition-fn)]",
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

export const SEARCH_INDEX_LABEL_CLASS = [
  "text-[0.95rem]",
  "font-semibold",
  "text-text-secondary",
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

export const SEARCH_INDEX_PAGINATION_CLASS = [
  "mt-sm",
  "flex",
  "flex-wrap",
  "items-center",
  "gap-sm",
].join(" ");

export const SEARCH_INDEX_STATUS_CLASS = [
  "min-w-[8.5rem]",
  "text-[0.95rem]",
  "text-text-secondary",
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
