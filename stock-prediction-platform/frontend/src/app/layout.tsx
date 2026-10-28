import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StockTrade - AI Stock Market & Trading Platform",
  description: "AI-driven stock market prediction and portfolio trading platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
