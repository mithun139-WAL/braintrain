const withAlpha = (token: string) => `hsl(var(${token}) / <alpha-value>)`;

export const colors = {
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
