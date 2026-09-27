import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Scan2EDI",
  description: "Private on-premise invoice to EDI processing"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
