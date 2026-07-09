import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
  weight: ["400", "500", "600", "700", "800"]
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
  weight: ["400", "500", "600", "700"]
});

export const metadata: Metadata = {
  title: "ModelTrace — ML Decision Operations",
  description:
    "Plataforma de observabilidade, auditoria e governança para decisões de Machine Learning. Predições append-only, drift, replay, what-if e bias analysis.",
  applicationName: "ModelTrace",
  authors: [{ name: "Diego Henrique Xavier" }],
  keywords: [
    "Machine Learning",
    "MLOps",
    "ML Observability",
    "Model Governance",
    "NoSQL",
    "Drift",
    "Audit",
    "Decision Logging"
  ]
};

export const viewport: Viewport = {
  themeColor: "#0a0c10",
  width: "device-width",
  initialScale: 1
};

interface RootLayoutProps {
  children: React.ReactNode;
}

// Constante: ler tema persistido antes do paint (anti-FOUC). Sem entrada do usuário.
const THEME_BOOT_SCRIPT = [
  "(function(){",
  "try{",
  "var s=localStorage.getItem('modeltrace_theme');",
  "var m=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches;",
  "var t=(s==='light'||s==='dark')?s:(m?'light':'dark');",
  "document.documentElement.dataset.theme=t;",
  "}catch(e){document.documentElement.dataset.theme='dark';}",
  "})();"
].join("");

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${ibmPlexMono.variable}`} data-theme="dark">
      <head>
        <Script id="modeltrace-theme-boot" strategy="beforeInteractive">
          {THEME_BOOT_SCRIPT}
        </Script>
      </head>
      <body>{children}</body>
    </html>
  );
}
