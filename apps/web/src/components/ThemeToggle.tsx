"use client";

import { useTheme } from "@/components/providers/ThemeProvider";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} theme`}
      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-subtle bg-surface text-muted shadow-xs transition-colors hover:bg-surface-2 hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring active:scale-95"
    >
      {resolvedTheme === "dark" ? (
        <Sun className="h-4 w-4 text-amber-400 transition-transform" aria-hidden="true" />
      ) : (
        <Moon className="h-4 w-4 text-slate-700 transition-transform" aria-hidden="true" />
      )}
    </button>
  );
}
