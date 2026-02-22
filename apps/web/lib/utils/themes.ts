export const themes = {
    light: "light",
    dark: "dark",
    system: "system",
} as const;

export type ThemeType = typeof themes[keyof typeof themes];
