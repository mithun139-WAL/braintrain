import type { Metadata } from "next";
import { ThemeProvider } from "@/core/components/providers/ThemeProvider";
import { QueryProvider } from "@/core/components/providers/QueryProvider";
import { Inter, Space_Grotesk } from "next/font/google";
import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk" });

export const metadata: Metadata = {
    title: "BrainTrain | AI Interview Training",
    description: "Master your interview skills with AI-driven coaching and personalised training paths.",
    icons: {
        icon: [
            { url: "/favicon.ico" },
            { url: "/icon.png", type: "image/png" }
        ],
        shortcut: "/favicon.ico",
        apple: "/icon.png",
    },
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <head>
                <link
                    rel="stylesheet"
                    href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap"
                />
            </head>
            <body
                className={`${inter.variable} ${spaceGrotesk.variable} font-sans antialiased min-h-screen bg-background text-foreground`}
            >
                <ThemeProvider
                    attribute="class"
                    defaultTheme="system"
                    enableSystem
                    disableTransitionOnChange
                >
                    <QueryProvider>{children}</QueryProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}
