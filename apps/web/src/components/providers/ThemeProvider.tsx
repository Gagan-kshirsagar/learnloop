"use client";

import {
  createContext,
  useCallback,
  useContext,
  useSyncExternalStore,
  type ReactNode,
} from "react";

export type Theme = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
}

const STORAGE_KEY = "learnloop.theme";

const ThemeContext = createContext<ThemeContextValue | null>(null);

export const themeNoFlashScript = `(function() {
  try {
    var stored = localStorage.getItem("${STORAGE_KEY}");
    var theme = stored || "system";
    var isDark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    var root = document.documentElement;
    if (isDark) {
      root.classList.add("dark");
      root.style.colorScheme = "dark";
    } else {
      root.classList.remove("dark");
      root.style.colorScheme = "light";
    }
  } catch (e) {}
})();`;

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  let mediaQuery: MediaQueryList | null = null;
  if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", callback);
  }
  return () => {
    window.removeEventListener("storage", callback);
    mediaQuery?.removeEventListener("change", callback);
  };
}

function getStoredThemeSnapshot(): Theme {
  try {
    return (localStorage.getItem(STORAGE_KEY) as Theme) || "system";
  } catch {
    return "system";
  }
}

function getServerThemeSnapshot(): Theme {
  return "system";
}

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useSyncExternalStore(
    subscribe,
    getStoredThemeSnapshot,
    getServerThemeSnapshot
  );

  const resolvedTheme: ResolvedTheme =
    theme === "dark" || (theme === "system" && getSystemTheme() === "dark")
      ? "dark"
      : "light";

  const setTheme = useCallback((newTheme: Theme) => {
    try {
      localStorage.setItem(STORAGE_KEY, newTheme);
    } catch {
      // Storage unavailable
    }
    const isDark =
      newTheme === "dark" || (newTheme === "system" && getSystemTheme() === "dark");
    const root = document.documentElement;
    const resolved: ResolvedTheme = isDark ? "dark" : "light";
    root.style.colorScheme = resolved;
    if (isDark) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    window.dispatchEvent(new Event("storage"));
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
