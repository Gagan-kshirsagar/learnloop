"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Loader2, Play } from "lucide-react";
import Link from "next/link";

import { useGuestMutation } from "@/lib/query/auth";

export function HeroActions() {
  const router = useRouter();
  const guestMutation = useGuestMutation();

  const handleDemo = () => {
    guestMutation.mutate(undefined, {
      onSuccess: () => router.push("/app"),
    });
  };

  return (
    <div className="flex flex-col items-center gap-3 sm:flex-row sm:gap-4">
      <Link
        href="/register"
        className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-accent px-8 text-sm font-semibold text-accent-foreground shadow-md transition-all hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-ring active:scale-[0.97] sm:w-auto"
      >
        Get started free
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </Link>
      <button
        type="button"
        onClick={handleDemo}
        disabled={guestMutation.isPending}
        className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl border border-subtle bg-surface px-8 text-sm font-semibold text-foreground shadow-sm transition-all hover:bg-surface-2 hover:border-strong focus-visible:outline-2 focus-visible:outline-ring active:scale-[0.97] disabled:opacity-50 sm:w-auto"
      >
        {guestMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Launching demo…
          </>
        ) : (
          <>
            <Play className="h-3.5 w-3.5" aria-hidden="true" />
            Try live demo
          </>
        )}
      </button>
    </div>
  );
}
