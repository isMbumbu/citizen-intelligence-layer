import type { Metadata } from "next";
import Script from "next/script";
import localFont from "next/font/local";
import "./globals.css";

// Fonts are bundled (SIL Open Font License, see app/fonts) so builds and
// deployments work without reaching Google Fonts.
const jakarta = localFont({ src: "./fonts/PlusJakartaSans-Variable.woff2", variable: "--font-jakarta", weight: "200 800", display: "swap" });
const jetBrains = localFont({ src: "./fonts/JetBrainsMono-Variable.woff2", variable: "--font-jetbrains", weight: "100 800", display: "swap" });

export const metadata: Metadata = {
  title: "Citizen Intelligence Layer",
  description:
    "Information for citizens about public spending, projects, evidence, and civic action.",
  icons: { icon: "/kenya-brush-favicon.png", apple: "/kenya-brush-favicon.png" },
  manifest: "/site.webmanifest",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${jakarta.variable} ${jetBrains.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <Script id="theme-init" strategy="beforeInteractive">
          {`try { const saved = localStorage.getItem("civicact-theme"); const theme = saved === "dark" || saved === "light" ? saved : (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); document.documentElement.dataset.theme = theme; } catch { document.documentElement.dataset.theme = "light"; }`}
        </Script>
        {children}
      </body>
    </html>
  );
}
