export const typography = {
  "display-2xl": [
    "3.75rem",
    { lineHeight: "0.96", letterSpacing: "-0.045em", fontWeight: "700" },
  ],
  "display-xl": [
    "3rem",
    { lineHeight: "1.02", letterSpacing: "-0.04em", fontWeight: "700" },
  ],
  "display-lg": [
    "2.25rem",
    { lineHeight: "1.08", letterSpacing: "-0.035em", fontWeight: "700" },
  ],
  "display-md": [
    "1.875rem",
    { lineHeight: "1.12", letterSpacing: "-0.03em", fontWeight: "700" },
  ],
  "title-lg": [
    "1.5rem",
    { lineHeight: "1.2", letterSpacing: "-0.025em", fontWeight: "650" },
  ],
  "title-md": [
    "1.25rem",
    { lineHeight: "1.3", letterSpacing: "-0.02em", fontWeight: "650" },
  ],
  "body-lg": [
    "1.125rem",
    { lineHeight: "1.75", letterSpacing: "-0.015em", fontWeight: "500" },
  ],
  "body-md": [
    "1rem",
    { lineHeight: "1.65", letterSpacing: "-0.012em", fontWeight: "500" },
  ],
  "body-sm": [
    "0.9375rem",
    { lineHeight: "1.6", letterSpacing: "-0.01em", fontWeight: "500" },
  ],
  "label-md": [
    "0.8125rem",
    { lineHeight: "1.4", letterSpacing: "0.015em", fontWeight: "600" },
  ],
  "label-sm": [
    "0.75rem",
    { lineHeight: "1.35", letterSpacing: "0.08em", fontWeight: "600" },
  ],
} satisfies Record<
  string,
  | string
  | [string, string]
  | [string, { lineHeight?: string; letterSpacing?: string; fontWeight?: string | number }]
>;

export const fontFamilies = {
  sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
  display: ["var(--font-space-grotesk)", "var(--font-inter)", "system-ui", "sans-serif"],
  mono: ["ui-monospace", "SFMono-Regular", "SF Mono", "monospace"],
};
