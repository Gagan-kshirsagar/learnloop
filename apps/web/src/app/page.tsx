import Link from "next/link";
import {
  BrainCircuit,
  BookOpen,
  Terminal,
  Upload,
  Code2,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  FileCode2,
  Check,
} from "lucide-react";

import { Navbar } from "@/components/navigation/Navbar";
import { HeroActions } from "@/components/landing/HeroActions";
import { TutorPreview } from "@/components/landing/TutorPreview";
import {
  MotionStagger,
  MotionFadeUp,
  MotionHoverCard,
} from "@/components/landing/MotionStagger";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* ── Clean Sticky Navigation ── */}
      <Navbar showNavLinks={true} />

      <main className="flex-1">
        {/* ── Hero Section ── */}
        <section className="relative overflow-hidden pt-10 pb-16 sm:pt-16 sm:pb-24">
          {/* Subtle Ambient Glow */}
          <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden" aria-hidden="true">
            <div className="absolute left-1/2 top-0 h-[450px] w-[850px] -translate-x-1/2 rounded-full bg-gradient-to-br from-accent/15 via-accent-2/10 to-transparent blur-3xl opacity-65" />
          </div>

          <div className="mx-auto max-w-5xl px-4 sm:px-6">
            <div className="grid items-center gap-10 lg:grid-cols-2 lg:gap-12">
              <MotionStagger className="flex flex-col items-center text-center lg:items-start lg:text-left">
                {/* Hero Badge */}
                <MotionFadeUp>
                  <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-subtle bg-surface/80 px-3 py-1 text-xs font-medium text-muted shadow-xs backdrop-blur-sm">
                    <span className="h-1.5 w-1.5 rounded-full bg-success" />
                    <span>AI-Native CS Learning Platform</span>
                  </div>
                </MotionFadeUp>

                {/* Hero Headline */}
                <MotionFadeUp>
                  <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-foreground sm:text-4xl lg:text-5xl">
                    Learn to code with a tutor that{" "}
                    <span className="bg-gradient-to-r from-accent to-accent-2 bg-clip-text text-transparent">
                      guides, not answers.
                    </span>
                  </h1>
                </MotionFadeUp>

                {/* Hero Subhead */}
                <MotionFadeUp>
                  <p className="mt-4 max-w-md text-base leading-relaxed text-muted sm:text-lg">
                    The modern platform for computer science education. Socratic
                    tutoring that asks guiding questions, runs code in safe
                    sandboxes, and aligns with your curriculum.
                  </p>
                </MotionFadeUp>

                {/* Hero CTAs */}
                <MotionFadeUp className="mt-7 w-full sm:w-auto">
                  <HeroActions />
                </MotionFadeUp>
              </MotionStagger>

              {/* Code & Socratic Dialogue Preview */}
              <div id="demo" className="flex justify-center lg:justify-end">
                <TutorPreview />
              </div>
            </div>
          </div>
        </section>

        {/* ── Attractive Features Section ── */}
        <section id="features" className="border-t border-subtle/60 bg-surface-2/30 py-16 sm:py-24">
          <div className="mx-auto max-w-5xl px-4 sm:px-6">
            <div className="mx-auto mb-12 max-w-lg text-center">
              <div className="mb-2 inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-accent">
                <Sparkles className="h-3 w-3" />
                Core Capabilities
              </div>
              <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                Built for deep conceptual mastery
              </h2>
              <p className="mt-2 text-sm text-muted">
                Replace generic chatbots with pedagogical tools designed specifically for programming courses.
              </p>
            </div>

            <MotionStagger className="grid gap-6 sm:grid-cols-3">
              {/* Feature 1 */}
              <MotionHoverCard>
                <div className="flex h-full flex-col justify-between rounded-2xl border border-subtle bg-surface p-6 shadow-xs transition-all hover:border-strong hover:shadow-md">
                  <div>
                    <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
                      <BrainCircuit className="h-5 w-5" />
                    </div>
                    <h3 className="text-base font-semibold text-foreground">
                      Socratic AI Guidance
                    </h3>
                    <p className="mt-2 text-xs sm:text-sm leading-relaxed text-muted">
                      Prompts students to deduce solutions through guided questions rather than dumping full answers.
                    </p>
                  </div>

                  {/* Micro Visual Card */}
                  <div className="mt-5 rounded-xl border border-accent/20 bg-accent-soft/50 p-3 text-[11px] leading-relaxed text-foreground">
                    <span className="font-semibold text-accent block mb-1">Tutor Nudge:</span>
                    &ldquo;What happens when <code className="rounded bg-surface px-1 font-mono text-[10px]">left == right</code>? Which index is checked?&rdquo;
                  </div>
                </div>
              </MotionHoverCard>

              {/* Feature 2 */}
              <MotionHoverCard>
                <div className="flex h-full flex-col justify-between rounded-2xl border border-subtle bg-surface p-6 shadow-xs transition-all hover:border-strong hover:shadow-md">
                  <div>
                    <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
                      <BookOpen className="h-5 w-5" />
                    </div>
                    <h3 className="text-base font-semibold text-foreground">
                      Curriculum Grounded
                    </h3>
                    <p className="mt-2 text-xs sm:text-sm leading-relaxed text-muted">
                      Tuned strictly to your university or bootcamp syllabus, lecture slides, and assignment rubrics.
                    </p>
                  </div>

                  {/* Micro Visual Card */}
                  <div className="mt-5 space-y-1.5 rounded-xl border border-subtle bg-surface-2/60 p-3 text-[11px]">
                    <div className="flex items-center gap-1.5 text-foreground font-medium">
                      <Check className="h-3 w-3 text-accent" />
                      <span>Lecture 04: Binary Search</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-foreground font-medium">
                      <Check className="h-3 w-3 text-accent" />
                      <span>Homework 2 Guidelines</span>
                    </div>
                  </div>
                </div>
              </MotionHoverCard>

              {/* Feature 3 */}
              <MotionHoverCard>
                <div className="flex h-full flex-col justify-between rounded-2xl border border-subtle bg-surface p-6 shadow-xs transition-all hover:border-strong hover:shadow-md">
                  <div>
                    <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
                      <Terminal className="h-5 w-5" />
                    </div>
                    <h3 className="text-base font-semibold text-foreground">
                      Instant Code Sandbox
                    </h3>
                    <p className="mt-2 text-xs sm:text-sm leading-relaxed text-muted">
                      Runs student code in isolated sandbox environments with sub-second feedback and automated unit tests.
                    </p>
                  </div>

                  {/* Micro Visual Card */}
                  <div className="mt-5 rounded-xl border border-subtle bg-surface-2/60 p-3 font-mono text-[11px] text-muted space-y-1">
                    <div className="flex items-center justify-between text-success font-semibold">
                      <span>✓ test_target_found</span>
                      <span>0.8ms</span>
                    </div>
                    <div className="flex items-center justify-between text-success font-semibold">
                      <span>✓ test_boundary_keys</span>
                      <span>1.1ms</span>
                    </div>
                  </div>
                </div>
              </MotionHoverCard>
            </MotionStagger>
          </div>
        </section>

        {/* ── Attractive How It Works Stepper ── */}
        <section id="how-it-works" className="border-t border-subtle/60 py-16 sm:py-24">
          <div className="mx-auto max-w-5xl px-4 sm:px-6">
            <div className="mx-auto mb-14 max-w-lg text-center">
              <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                How LearnLoop works
              </h2>
              <p className="mt-2 text-sm text-muted">
                A seamless 3-step learning loop for educators and students.
              </p>
            </div>

            <MotionStagger className="grid gap-6 sm:grid-cols-3">
              {/* Step 1 */}
              <MotionFadeUp>
                <div className="relative flex h-full flex-col justify-between rounded-2xl border border-subtle bg-surface p-6 shadow-xs">
                  <div>
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-accent">
                        <Upload className="h-5 w-5" />
                      </div>
                      <span className="font-mono text-xs font-bold text-accent">STEP 01</span>
                    </div>
                    <h3 className="text-base font-semibold text-foreground">
                      Connect Curriculum
                    </h3>
                    <p className="mt-2 text-xs sm:text-sm leading-relaxed text-muted">
                      Upload course slides, syllabus, and assignment specifications.
                    </p>
                  </div>

                  <div className="mt-5 flex items-center gap-2 rounded-lg border border-subtle bg-surface-2/50 px-3 py-2 text-[11px] text-muted">
                    <FileCode2 className="h-3.5 w-3.5 text-accent" />
                    <span>syllabus_cs101.pdf</span>
                  </div>
                </div>
              </MotionFadeUp>

              {/* Step 2 */}
              <MotionFadeUp>
                <div className="relative flex h-full flex-col justify-between rounded-2xl border border-subtle bg-surface p-6 shadow-xs">
                  <div>
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-accent">
                        <Code2 className="h-5 w-5" />
                      </div>
                      <span className="font-mono text-xs font-bold text-accent">STEP 02</span>
                    </div>
                    <h3 className="text-base font-semibold text-foreground">
                      Code with Socratic Hints
                    </h3>
                    <p className="mt-2 text-xs sm:text-sm leading-relaxed text-muted">
                      Students code with real-time hints that guide thinking without spoiling answers.
                    </p>
                  </div>

                  <div className="mt-5 rounded-lg border border-accent/20 bg-accent-soft/40 px-3 py-2 text-[11px] text-foreground">
                    <span className="font-medium text-accent">Hint: </span>
                    Check loop termination bounds.
                  </div>
                </div>
              </MotionFadeUp>

              {/* Step 3 */}
              <MotionFadeUp>
                <div className="relative flex h-full flex-col justify-between rounded-2xl border border-subtle bg-surface p-6 shadow-xs">
                  <div>
                    <div className="mb-4 flex items-center justify-between">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-soft text-accent">
                        <CheckCircle2 className="h-5 w-5" />
                      </div>
                      <span className="font-mono text-xs font-bold text-accent">STEP 03</span>
                    </div>
                    <h3 className="text-base font-semibold text-foreground">
                      Instant Verification
                    </h3>
                    <p className="mt-2 text-xs sm:text-sm leading-relaxed text-muted">
                      Automated unit tests execute in hardened sandboxes with immediate feedback.
                    </p>
                  </div>

                  <div className="mt-5 flex items-center justify-between rounded-lg border border-subtle bg-surface-2/50 px-3 py-2 text-[11px] text-success font-medium">
                    <span>100% Tests Passing</span>
                    <span className="text-[10px] text-muted font-mono">14ms</span>
                  </div>
                </div>
              </MotionFadeUp>
            </MotionStagger>
          </div>
        </section>

        {/* ── Clean CTA Banner ── */}
        <section className="border-t border-subtle/60 bg-surface-2/40 py-16 text-center">
          <div className="mx-auto max-w-2xl px-4 sm:px-6">
            <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Ready to try LearnLoop?
            </h2>
            <p className="mt-3 text-sm text-muted">
              Start free with your team or explore the live demo instantly.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/register"
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-accent px-6 text-xs font-semibold text-accent-foreground shadow-sm transition-all hover:bg-accent-hover active:scale-95"
              >
                Get started free
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <Link
                href="/login"
                className="inline-flex h-10 items-center justify-center rounded-lg border border-subtle bg-surface px-6 text-xs font-semibold text-foreground shadow-xs transition-all hover:bg-surface-2 active:scale-95"
              >
                Sign in to workspace
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* ── Minimal Footer ── */}
      <footer className="border-t border-subtle/70 bg-surface py-8">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 px-4 text-xs text-muted sm:flex-row sm:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded bg-accent text-[9px] font-bold text-accent-foreground">
              LL
            </div>
            <span className="font-semibold text-foreground">LearnLoop</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/#features" className="transition-colors hover:text-foreground">
              Features
            </Link>
            <Link href="/#how-it-works" className="transition-colors hover:text-foreground">
              How it works
            </Link>
            <Link href="/login" className="transition-colors hover:text-foreground">
              Sign in
            </Link>
            <Link href="/register" className="transition-colors hover:text-foreground">
              Get started
            </Link>
          </div>
          <span>© {new Date().getFullYear()} LearnLoop.</span>
        </div>
      </footer>
    </div>
  );
}
