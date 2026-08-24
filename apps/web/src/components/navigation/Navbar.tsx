"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ThemeToggle";

interface NavbarProps {
  showNavLinks?: boolean;
}

export function Navbar({ showNavLinks = true }: NavbarProps) {
  const pathname = usePathname();
  const isAuthPage = pathname === "/login" || pathname === "/register";

  return (
    <header className="sticky top-0 z-50 w-full border-b border-subtle bg-background/80 backdrop-blur-md transition-colors">
      <nav
        aria-label="Main navigation"
        className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 sm:px-6"
      >
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-accent text-xs font-bold text-accent-foreground shadow-xs transition-transform group-hover:scale-105">
            LL
          </div>
          <span className="text-sm font-semibold tracking-tight text-foreground">
            LearnLoop
          </span>
        </Link>

        {/* Center Nav Links (Desktop) */}
        {showNavLinks && (
          <div className="hidden md:flex items-center gap-6 text-xs font-medium text-muted">
            <Link
              href="/#features"
              className="transition-colors hover:text-foreground"
            >
              Features
            </Link>
            <Link
              href="/#how-it-works"
              className="transition-colors hover:text-foreground"
            >
              How it works
            </Link>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <ThemeToggle />

          {!isAuthPage && (
            <Link
              href="/login"
              className="hidden sm:inline-flex text-xs font-medium text-muted transition-colors hover:text-foreground"
            >
              Sign in
            </Link>
          )}

          <Link
            href="/register"
            className="inline-flex h-8 items-center justify-center rounded-xl bg-accent px-3.5 text-xs font-semibold text-accent-foreground shadow-xs transition-all hover:bg-accent-hover active:scale-[0.98]"
          >
            {isAuthPage ? "Sign Up" : "Get Started"}
          </Link>
        </div>
      </nav>
    </header>
  );
}
