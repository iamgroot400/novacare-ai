import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";
import { SupportProvider } from "@/components/SupportProvider";

export const metadata: Metadata = {
  title: "NovaStore — Technology made simpler",
  description:
    "NovaStore is a fictional Nepal-based electronics store showcasing NovaCare AI, an agentic customer-support agent with chat and in-browser voice.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <SupportProvider>
          <div className="flex min-h-screen flex-col">
            <Nav />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </SupportProvider>
      </body>
    </html>
  );
}
