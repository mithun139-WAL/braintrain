
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
  sm: "0 1px 2px hsl(var(--shadow) / 0.02)",
  md: "0 4px 12px -8px hsl(var(--shadow) / 0.08)",
  lg: "0 8px 24px -12px hsl(var(--shadow) / 0.1)",
  card: "0 1px 2px hsl(var(--shadow) / 0.02), 0 8px 24px -12px hsl(var(--shadow) / 0.08)",
  "card-hover": "0 1px 2px hsl(var(--shadow) / 0.03), 0 12px 28px -8px hsl(var(--shadow) / 0.1)",
  elevated: "0 12px 36px -14px hsl(var(--shadow) / 0.12)",
  "primary-sm": "none",
};

const typography: Record<
  string,
  | string
  | [string, string]
  | [string, { lineHeight?: string; letterSpacing?: string; fontWeight?: string | number }]
> = {
  "display-2xl": [
    "2.5rem",
    { lineHeight: "1.1", letterSpacing: "-0.03em", fontWeight: "600" },
  ],
  "display-xl": [
    "2.25rem",
    { lineHeight: "1.15", letterSpacing: "-0.025em", fontWeight: "600" },
  ],
  "display-lg": [
    "2rem",
    { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" },
  ],
  "display-md": [
    "1.75rem",
    { lineHeight: "1.25", letterSpacing: "-0.015em", fontWeight: "600" },
  ],
  "title-lg": [
    "1.375rem",
    { lineHeight: "1.3", letterSpacing: "-0.01em", fontWeight: "600" },
  ],
  "title-md": [
    "1.125rem",
    { lineHeight: "1.4", letterSpacing: "-0.005em", fontWeight: "500" },
  ],
  "body-lg": [
    "1.0625rem",
    { lineHeight: "1.65", letterSpacing: "0", fontWeight: "400" },
  ],
  "body-md": [
    "0.9375rem",
    { lineHeight: "1.6", letterSpacing: "0", fontWeight: "400" },
  ],
  "body-sm": [
    "0.875rem",
    { lineHeight: "1.55", letterSpacing: "0", fontWeight: "400" },
  ],
  "label-md": [
    "0.8125rem",
    { lineHeight: "1.4", letterSpacing: "0.01em", fontWeight: "500" },
  ],
  "label-sm": [
    "0.75rem",
    { lineHeight: "1.35", letterSpacing: "0.04em", fontWeight: "500" },
  ],
};

const fontFamilies = {
  sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
  display: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
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
