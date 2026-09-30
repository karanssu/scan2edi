import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Scan2EDI",
  description: "Invoice extraction, review and EDI/CSV export"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <Link className="brand" href="/">Scan2EDI</Link>
          <nav>
            <Link href="/">Invoices</Link>
            <Link href="/mappings">Mappings</Link>
          </nav>
        </header>
        <main className="shell">{children}</main>
      </body>
    </html>
  );
}
