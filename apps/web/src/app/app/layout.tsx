"use client";

import { useEffect, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, GraduationCap, LayoutDashboard, LogOut, Sparkles, User as UserIcon } from "lucide-react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLogoutMutation, useMeQuery } from "@/lib/query/auth";
import { useAuthStore } from "@/stores/authStore";

export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const status = useAuthStore((state) => state.status);
  const user = useAuthStore((state) => state.user);
  const tenant = useAuthStore((state) => state.tenant);
  const logoutMutation = useLogoutMutation();

  useMeQuery();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  const handleLogout = () => {
    logoutMutation.mutate(undefined, {
      onSettled: () => {
        router.replace("/login");
      },
    });
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-background p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-subtle pb-4">
          <Skeleton className="h-8 w-40 rounded-xl" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-24 rounded-xl" />
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <Skeleton className="h-36 w-full rounded-2xl" />
          <Skeleton className="h-36 w-full rounded-2xl" />
          <Skeleton className="h-36 w-full rounded-2xl" />
        </div>
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (status === "unauthenticated") {
    return null;
  }

  const isGuest = status === "guest" || (user?.role === "student" && user?.email.includes("@guest"));
  const canTeach = user?.role === "owner" || user?.role === "instructor";

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col antialiased">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-subtle bg-background/80 backdrop-blur-md transition-colors">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-4 sm:gap-6">
            <Link href="/app" className="flex items-center gap-2.5 group">
              <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-accent text-xs font-bold text-accent-foreground shadow-xs transition-transform group-hover:scale-105">
                LL
              </div>
              <span className="font-bold text-sm tracking-tight hidden sm:inline text-foreground">
                LearnLoop
              </span>
            </Link>

            {/* Breadcrumb Tenant Badge */}
            <div className="flex items-center gap-2">
              <span className="text-muted/60 text-xs hidden sm:inline">/</span>
              <span className="text-xs font-semibold text-foreground truncate max-w-[120px] sm:max-w-[180px]">
                {tenant?.name || "Workspace"}
              </span>
              {isGuest ? (
                <Badge variant="outline" className="border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400 font-medium text-[10px] gap-1 px-2 py-0.5 rounded-md">
                  <Sparkles className="h-2.5 w-2.5" />
                  Sandbox
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-[10px] font-medium uppercase tracking-wider px-2 py-0.5 rounded-md border border-subtle">
                  {tenant?.plan || "Free"}
                </Badge>
              )}
            </div>

            {/* Nav Links */}
            <nav className="flex items-center gap-1 text-xs font-medium">
              <Link
                href="/app"
                className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 transition-all ${
                  pathname === "/app"
                    ? "bg-surface-2 text-foreground font-semibold shadow-xs"
                    : "text-muted hover:text-foreground hover:bg-surface-2/60"
                }`}
              >
                <LayoutDashboard className="h-3.5 w-3.5" />
                <span className="hidden md:inline">Dashboard</span>
              </Link>
              <Link
                href="/app/courses"
                className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 transition-all ${
                  pathname.startsWith("/app/courses") || pathname.startsWith("/app/lessons")
                    ? "bg-surface-2 text-foreground font-semibold shadow-xs"
                    : "text-muted hover:text-foreground hover:bg-surface-2/60"
                }`}
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span>Courses</span>
              </Link>
              {canTeach && (
                <Link
                  href="/app/teach"
                  className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 transition-all ${
                    pathname.startsWith("/app/teach")
                      ? "bg-surface-2 text-foreground font-semibold shadow-xs"
                      : "text-muted hover:text-foreground hover:bg-surface-2/60"
                  }`}
                >
                  <GraduationCap className="h-3.5 w-3.5" />
                  <span>Teach</span>
                </Link>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-muted bg-surface-2/70 px-2.5 py-1 rounded-xl border border-subtle">
              <UserIcon className="h-3 w-3 text-muted" />
              <span className="font-medium text-foreground">{user?.name}</span>
              <span className="text-faint text-[11px]">({user?.role})</span>
            </div>

            <ThemeToggle />

            <Button
              variant="ghost"
              size="sm"
              className="text-muted hover:text-foreground h-8 px-2.5 rounded-xl"
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
            >
              <LogOut className="h-3.5 w-3.5 sm:mr-1.5" />
              <span className="hidden sm:inline text-xs">Sign out</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content View */}
      <main className="flex-1 mx-auto w-full max-w-7xl p-4 sm:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
}
