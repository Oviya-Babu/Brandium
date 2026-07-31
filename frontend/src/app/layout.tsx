import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BrandGuard AI",
  description: "Enterprise Brand Decision Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
