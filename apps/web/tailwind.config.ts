
import type { Config } from "tailwindcss";

const withAlpha = (token: string) => `hsl(var(${token}) / <alpha-value>)`;

const colors = {
  background: {
    DEFAULT: withAlpha("--background"),
    light: withAlpha("--background-light"),
    dark: withAlpha("--background-dark"),
    elevated: withAlpha("--background-elevated"),
  },
  foreground: withAlpha("--foreground"),
  card: {
    DEFAULT: withAlpha("--card"),
    foreground: withAlpha("--card-foreground"),
  },
  muted: {
    DEFAULT: withAlpha("--muted"),
    foreground: withAlpha("--muted-foreground"),
  },
  border: {
    DEFAULT: withAlpha("--border"),
    subtle: withAlpha("--border-subtle"),
  },
  primary: {
    DEFAULT: withAlpha("--primary"),
    dark: withAlpha("--primary-strong"),
    foreground: withAlpha("--primary-foreground"),
  },
  emerald: withAlpha("--emerald"),
  ruby: withAlpha("--ruby"),
  gold: withAlpha("--gold"),
  sky: withAlpha("--sky"),
  violet: withAlpha("--violet"),
  charcoal: withAlpha("--charcoal"),
  white: "#ffffff",
  black: "#050816",
};

const spacing = {
  18: "4.5rem",
  22: "5.5rem",
  30: "7.5rem",
  gutter: "1.25rem",
  shell: "1.5rem",
  section: "2rem",
};

const radii = {
  md: "0.75rem",
  lg: "1rem",
  xl: "1.25rem",
  "2xl": "1.5rem",
  "3xl": "1.875rem",
  panel: "1.75rem",
  full: "9999px",
};

const shadows = {
  sm: "0 1px 2px hsl(var(--shadow) / 0.06)",
  md: "0 8px 24px -16px hsl(var(--shadow) / 0.22)",
  lg: "0 16px 48px -24px hsl(var(--shadow) / 0.24)",
  card: "0 1px 2px hsl(var(--shadow) / 0.05), 0 18px 48px -28px hsl(var(--shadow) / 0.18)",
  "card-hover": "0 1px 2px hsl(var(--shadow) / 0.06), 0 24px 56px -24px hsl(var(--shadow) / 0.24)",
  elevated: "0 24px 72px -28px hsl(var(--shadow) / 0.28)",
  "primary-sm": "0 16px 40px -24px hsl(var(--primary) / 0.7)",
};

const typography: Record<
  string,
  | string
  | [string, string]
  | [string, { lineHeight?: string; letterSpacing?: string; fontWeight?: string | number }]
> = {
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
};

const fontFamilies = {
  sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
  display: ["var(--font-space-grotesk)", "var(--font-inter)", "system-ui", "sans-serif"],
  mono: ["ui-monospace", "SFMono-Regular", "SF Mono", "monospace"],
};

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./core/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors,
      spacing,
      borderRadius: radii,
      boxShadow: shadows,
      fontSize: typography,
      fontFamily: fontFamilies,
      maxWidth: {
        content: "78rem",
        reading: "48rem",
        shell: "90rem",
      },
    },
  },
  plugins: [],
};

export default config;
