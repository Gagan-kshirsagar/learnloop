import { DemoCard } from "@/components/DemoCard";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ArrowRight, BookOpen, BrainCircuit, ShieldCheck } from "lucide-react";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-6 sm:p-12 md:p-20">
      <header className="flex w-full max-w-5xl items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-foreground font-bold text-sm">
            LL
          </div>
          <span className="text-lg font-bold tracking-tight text-foreground">
            LearnLoop
          </span>
        </div>
        <ThemeToggle />
      </header>

      <section className="flex w-full max-w-3xl flex-col items-center gap-8 py-16 text-center sm:py-24">
        <div className="inline-flex items-center gap-2 rounded-full border border-subtle bg-surface px-3 py-1 text-xs font-medium text-muted shadow-sm">
          <span className="h-2 w-2 rounded-full bg-success" aria-hidden="true" />
          <span>Slice-0 Foundation Ready</span>
        </div>

        <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
          AI-native learning built for{" "}
          <span className="bg-gradient-to-r from-accent to-accent-2 bg-clip-text text-transparent">
            senior standards
          </span>
        </h1>

        <p className="max-w-xl text-lg text-muted">
          Multi-tenant architecture, PostgreSQL RLS isolation, sub-200ms API fast
          path, and purposeful motion crafted with Next.js App Router &amp; FastAPI.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <a
            href="#explore"
            className="inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-accent px-6 text-sm font-medium text-accent-foreground shadow-sm transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-ring active:scale-[0.98]"
          >
            <span>Explore Platform</span>
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </a>
          <a
            href="https://github.com/Gagan-kshirsagar/learnloop"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-11 items-center justify-center rounded-lg border border-subtle bg-surface px-6 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-ring active:scale-[0.98]"
          >
            Documentation
          </a>
        </div>

        <div className="w-full max-w-md pt-4">
          <DemoCard />
        </div>
      </section>

      <footer className="grid w-full max-w-5xl grid-cols-1 gap-4 border-t border-subtle pt-8 sm:grid-cols-3">
        <div className="flex items-center gap-3 rounded-lg p-3 text-left">
          <ShieldCheck className="h-5 w-5 text-accent" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-foreground">Postgres RLS Multi-Tenancy</p>
            <p className="text-xs text-muted">Rigid tenant context per request</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg p-3 text-left">
          <BrainCircuit className="h-5 w-5 text-accent" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-foreground">AI-Native Async Pipeline</p>
            <p className="text-xs text-muted">Fast sync path + background workers</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg p-3 text-left">
          <BookOpen className="h-5 w-5 text-accent" aria-hidden="true" />
          <div>
            <p className="text-sm font-medium text-foreground">Modular Monolith</p>
            <p className="text-xs text-muted">Strict api.py boundaries enforced in CI</p>
          </div>
        </div>
      </footer>
    </main>
  );
}
