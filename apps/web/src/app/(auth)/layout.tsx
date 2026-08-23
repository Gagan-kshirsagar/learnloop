import type { ReactNode } from "react";
import { Navbar } from "@/components/navigation/Navbar";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative flex min-h-screen flex-col">
      {/* Dynamic Ambient backdrop glow */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
        <div className="absolute left-1/2 top-1/4 h-[650px] w-[650px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-br from-accent/15 via-accent-2/10 to-transparent blur-3xl opacity-80" />
        <div className="absolute bottom-0 right-10 h-[450px] w-[450px] rounded-full bg-gradient-to-tl from-accent/10 to-transparent blur-3xl opacity-60" />
      </div>

      {/* Unified top Navbar matching landing page */}
      <Navbar showNavLinks={false} />

      {/* Auth Content Card Area */}
      <main className="flex flex-1 items-center justify-center px-4 pb-16 pt-8 sm:px-6">
        {children}
      </main>
    </div>
  );
}
