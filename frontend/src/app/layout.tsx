import type { Metadata } from "next";
import { Inter, Vazirmatn, Geist_Mono } from "next/font/google";
import "./globals.css";

import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/hooks/use-auth";
import { ThemeProvider } from "@/hooks/use-theme";
import { LocaleProvider } from "@/hooks/use-locale";

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

const initScript = `(function(){try{var t=localStorage.getItem("app-theme");if(t==="light")document.documentElement.classList.remove("dark");else document.documentElement.classList.add("dark")}catch(e){document.documentElement.classList.add("dark")}try{var l=localStorage.getItem("app-locale");if(l==="fa"){document.documentElement.lang="fa";document.documentElement.dir="rtl"}else{document.documentElement.lang="en";document.documentElement.dir="ltr"}}catch(e){}})()`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      dir="ltr"
      className={`${inter.variable} ${vazirmatn.variable} ${geistMono.variable} dark antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: initScript }} />
      </head>
      <body>
        <ThemeProvider>
          <LocaleProvider>
            <AuthProvider>{children}</AuthProvider>
            <Toaster position="bottom-right" duration={3000} />
          </LocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
