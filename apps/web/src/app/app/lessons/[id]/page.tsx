"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, CheckCircle2, Share2 } from "lucide-react";

import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useLessonDetailQuery } from "@/lib/query/catalog";

interface LessonPageProps {
  params: Promise<{ id: string }>;
}

export default function LessonPage({ params }: LessonPageProps) {
  const resolvedParams = use(params);
  const lessonId = resolvedParams.id;

  const { data: lesson, isLoading, error, refetch } = useLessonDetailQuery(lessonId);

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <Skeleton className="h-5 w-40 rounded-md" />
        <Skeleton className="h-10 w-3/4 rounded-md" />
        <div className="space-y-3 pt-4">
          <Skeleton className="h-4 w-full rounded-md" />
          <Skeleton className="h-4 w-5/6 rounded-md" />
          <Skeleton className="h-4 w-4/6 rounded-md" />
          <Skeleton className="h-32 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="max-w-xl mx-auto rounded-2xl border border-danger/30 bg-danger-soft p-8 text-center">
        <p className="text-sm font-semibold text-danger">Lesson not found</p>
        <p className="mt-1 text-xs text-muted">
          This lesson may not exist or is not available in your organization.
        </p>
        <div className="mt-4 flex items-center justify-center gap-3">
          <Link
            href="/app/courses"
            className="rounded-lg bg-surface px-4 py-1.5 text-xs font-semibold text-foreground border border-subtle shadow-xs hover:bg-surface-2"
          >
            Back to Courses
          </Link>
          <button
            type="button"
            onClick={() => refetch()}
            className="rounded-lg bg-accent px-4 py-1.5 text-xs font-semibold text-accent-foreground shadow-xs hover:bg-accent-hover"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 pb-16">
      {/* Top Navigation / Breadcrumbs */}
      <div className="flex items-center justify-between border-b border-subtle/60 pb-4">
        <Link
          href="/app/courses"
          className="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Catalog</span>
        </Link>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2.5 text-xs text-muted hover:text-foreground"
            onClick={() => {
              if (navigator.clipboard) {
                navigator.clipboard.writeText(window.location.href);
              }
            }}
          >
            <Share2 className="h-3 w-3 mr-1" />
            <span>Share</span>
          </Button>
        </div>
      </div>

      {/* Lesson Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-medium text-accent">
          <BookOpen className="h-3.5 w-3.5" />
          <span>Lesson Outline</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
          {lesson.title}
        </h1>
      </div>

      {/* Lesson Body Content (Server Markdown Rendered) */}
      <Card className="border-subtle bg-surface shadow-xs overflow-hidden">
        <CardContent className="p-6 sm:p-10">
          <MarkdownRenderer content={lesson.content_md} />
        </CardContent>
      </Card>

      {/* Next Step / Complete Leaf */}
      <div className="flex items-center justify-between rounded-2xl border border-subtle bg-surface-2/40 p-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-success-soft text-success">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs font-bold text-foreground">Finished reading this lesson?</p>
            <p className="text-[11px] text-muted">Ready to practice exercises or proceed to the next topic.</p>
          </div>
        </div>

        <Link href="/app/courses">
          <Button size="sm" variant="outline" className="text-xs font-medium">
            Continue Learning
          </Button>
        </Link>
      </div>
    </div>
  );
}
