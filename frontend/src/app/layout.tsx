import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import SessionProvider from "@/components/providers/SessionProvider";
import { ToastProvider } from "@/components/providers/ToastProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Bkmrk'd - Your Digital Bookshelf",
  description: "Discover, organize, and explore your favorite books with AI-powered recommendations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SessionProvider>
          <ToastProvider>
            <main className="min-h-screen bg-gray-50">
              {children}
            </main>
          </ToastProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
