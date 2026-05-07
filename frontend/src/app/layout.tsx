import type { Metadata } from "next";
import { Inter, Vazirmatn, Geist_Mono } from "next/font/google";
import "./globals.css";

import { AuthProvider } from "@/hooks/use-auth";
import { ThemeProvider } from "@/hooks/use-theme";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const vazirmatn = Vazirmatn({
  variable: "--font-vazirmatn",
  subsets: ["latin", "arabic"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Finance WebApp",
  description: "Professional financial analytics dashboard",
};

const themeScript = `(function(){try{var t=localStorage.getItem("app-theme");if(t==="light")document.documentElement.classList.remove("dark");else document.documentElement.classList.add("dark")}catch(e){document.documentElement.classList.add("dark")}})()`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${vazirmatn.variable} ${geistMono.variable} dark h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
