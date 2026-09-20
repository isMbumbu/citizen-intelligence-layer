import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Citizen Intelligence Layer",
  description:
    "Citizen-first intelligence for public spending, projects, evidence, and civic action.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
