import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: "AIAPICaba!",
  description: "Advanced terminal interface for exploring and analyzing HyperLiquid API data",
  icons: {
    icon: "/favicon.ico",
  },
  keywords: "API, blockchain, data analytics, terminal",
  authors: [{ name: "npc Team" }],
  openGraph: {
    title: "Terminal",
    description: "Advanced terminal interface for exploring and analyzing API data",
    type: "website",
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
