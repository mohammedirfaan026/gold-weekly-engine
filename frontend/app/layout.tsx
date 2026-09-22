import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Gold Research Terminal | Institutional Quant System",
  description:
    "Private institutional gold research engine on Oracle ARM64 Always Free & GCP Ephemeral burst compute.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-terminal-bg text-terminal-text antialiased selection:bg-gold-500/30 selection:text-gold-200">
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-1 max-w-[1700px] w-full mx-auto p-4 md:p-6 space-y-6">
            {children}
          </main>
          <footer className="border-t border-terminal-border/60 bg-terminal-panel/40 py-3 px-6 text-center text-xs font-mono text-terminal-dim">
            <div className="max-w-[1700px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
              <div>
                <span>GOLD RESEARCH TERMINAL </span>
                <span className="text-terminal-muted">| Pure Point-in-Time | Zero Lookahead | Strict Sample Sizes</span>
              </div>
              <div className="flex items-center gap-3">
                <span>Infra: Oracle Cloud ARM64 (4 vCPU / 24GB RAM)</span>
                <span>•</span>
                <span>Compute: Ephemeral GCP Worker</span>
                <span>•</span>
                <span>Network: Private Tailscale VPN</span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
