"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Bot, LogOut, Sparkles, User as UserIcon } from "lucide-react";

import { ThemeToggle } from "@/components/ThemeToggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLogoutMutation, useMeQuery } from "@/lib/query/auth";
import { useAuthStore } from "@/stores/authStore";

export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const status = useAuthStore((state) => state.status);
  const user = useAuthStore((state) => state.user);
  const tenant = useAuthStore((state) => state.tenant);
  const logoutMutation = useLogoutMutation();

  // Trigger MeQuery to ensure latest server state
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

  // While checking bootstrap / restoring tokens, show a sized skeleton to prevent flash
  if (status === "loading") {
    return (
      <div className="min-h-screen bg-background p-6 space-y-6">
        <div className="flex items-center justify-between border-b pb-4">
          <Skeleton className="h-8 w-40" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <Skeleton className="h-36 w-full rounded-xl" />
          <Skeleton className="h-36 w-full rounded-xl" />
          <Skeleton className="h-36 w-full rounded-xl" />
        </div>
        <Skeleton className="h-96 w-full rounded-xl" />
      </div>
    );
  }

  if (status === "unauthenticated") {
    return null;
  }

  const isGuest = status === "guest" || user?.role === "student" && user?.email.includes("@guest");

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight">LearnLoop</span>
              <span className="text-muted-foreground text-xs">/</span>
              <span className="text-xs font-semibold text-foreground truncate max-w-[150px] sm:max-w-[200px]">
                {tenant?.name || "Workspace"}
              </span>
            </div>

            {isGuest ? (
              <Badge variant="outline" className="border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400 font-medium text-[11px] gap-1">
                <Sparkles className="h-3 w-3" />
                Demo Sandbox
              </Badge>
            ) : (
              <Badge variant="secondary" className="text-[11px] font-medium uppercase tracking-wider">
                {tenant?.plan || "Free"}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground bg-muted/40 px-2.5 py-1 rounded-md border border-border/40">
              <UserIcon className="h-3.5 w-3.5" />
              <span className="font-medium text-foreground">{user?.name}</span>
              <span className="text-muted-foreground">({user?.role})</span>
            </div>

            <ThemeToggle />

            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-foreground h-8 px-2.5"
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
            >
              <LogOut className="h-4 w-4 sm:mr-1.5" />
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
