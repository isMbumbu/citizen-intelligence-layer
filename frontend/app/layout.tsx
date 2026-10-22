import type { Metadata } from "next";
import Script from "next/script";
import { JetBrains_Mono, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({ variable: "--font-jakarta", subsets: ["latin"] });
const jetBrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Citizen Intelligence Layer",
  description:
    "Information for citizens about public spending, projects, evidence, and civic action.",
  icons: { icon: "/kenya-brush-flag.png", apple: "/kenya-brush-flag.png" },
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
