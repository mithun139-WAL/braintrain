import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./providers/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                background: "var(--background)",
                foreground: "var(--foreground)",
                primary: {
                    DEFAULT: "#4f46e5", // Indigo 600
                    dark: "#4338ca",    // Indigo 700
                    light: "#eef2ff",   // Indigo 50
                },
                gray: {
                    50: '#f9fafb',
                    100: '#f3f4f6',
                    200: '#e5e7eb',
                    300: '#d1d5db',
                    400: '#9ca3af',
                    500: '#6b7280',
                    600: '#4b5563',
                    700: '#374151',
                    800: '#1f2937',
                    900: '#111827',
                }
            },
            borderRadius: {
                'xl': '1rem',    // 16px
                '2xl': '1.5rem',  // 24px
            },
            fontFamily: {
                display: ["var(--font-inter)", "sans-serif"],
            },
            boxShadow: {
                'premium': '0 4px 24px rgba(0, 0, 0, 0.04)',
            }
        },
    },
    plugins: [],
};
export default config;
