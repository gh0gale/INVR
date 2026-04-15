import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Stock — Institutional-Grade AI Investment Intelligence",
  description:
    "Privacy-aware, personalized stock analysis and contextual financial education — powered by AI. Professional-grade scoring across macro, fundamental, technical, and risk metrics.",
  keywords: [
    "AI",
    "stock analysis",
    "investment intelligence",
    "fintech",
    "financial education",
    "portfolio analysis",
  ],
  openGraph: {
    title: "AI Stock — Think Like an Investor, Powered by AI",
    description:
      "Privacy-aware, personalized stock analysis and contextual financial education—without linking your brokerage accounts.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
      <body>{children}</body>
    </html>
  );
}
