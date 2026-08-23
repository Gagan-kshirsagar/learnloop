"use client";

import { use, useCallback, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Code2,
  Share2,
} from "lucide-react";

import { ExerciseWorkspace } from "@/components/exercise/ExerciseWorkspace";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useLessonDetailQuery } from "@/lib/query/catalog";
import { useCompleteLessonMutation, useExerciseQuery } from "@/lib/query/learning";

interface LessonPageProps {
  params: Promise<{ id: string }>;
}

export default function LessonPage({ params }: LessonPageProps) {
  const resolvedParams = use(params);
  const lessonId = resolvedParams.id;

  const [activeTab, setActiveTab] = useState<"reading" | "exercise">("reading");

  const { data: lesson, isLoading, error, refetch } = useLessonDetailQuery(lessonId);
  const { data: exercise } = useExerciseQuery(lessonId);
  const completeMutation = useCompleteLessonMutation();

  const handleLessonCompleted = useCallback(() => {
    completeMutation.mutate(lessonId);
  }, [lessonId, completeMutation]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-5 w-40 rounded-md" />
        <Skeleton className="h-10 w-3/4 rounded-md" />
        <div className="space-y-3 pt-4">
          <Skeleton className="h-4 w-full rounded-md" />
          <Skeleton className="h-4 w-5/6 rounded-md" />
          <Skeleton className="h-4 w-4/6 rounded-md" />
          <Skeleton className="h-48 w-full rounded-xl" />
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
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Top Navigation / Breadcrumbs */}
      <div className="flex items-center justify-between border-b border-subtle/60 pb-4">
        <Link
          href="/app/courses"
          className="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Courses</span>
        </Link>

        <div className="flex items-center gap-2">
          {/* View Tab Switcher */}
          {exercise && (
            <div className="flex items-center rounded-lg border border-subtle bg-surface-2 p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setActiveTab("reading")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "reading"
                    ? "bg-surface text-foreground font-semibold shadow-xs"
                    : "text-muted hover:text-foreground"
                }`}
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span>Reading</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("exercise")}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
                  activeTab === "exercise"
                    ? "bg-surface text-foreground font-semibold shadow-xs"
                    : "text-muted hover:text-foreground"
                }`}
              >
                <Code2 className="h-3.5 w-3.5 text-accent" />
                <span>Exercise</span>
                <Badge variant="outline" className="text-[9px] px-1 py-0 border-accent/40 text-accent">
                  Python
                </Badge>
              </button>
            </div>
          )}

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
            <span className="hidden sm:inline">Share</span>
          </Button>
        </div>
      </div>

      {/* Lesson Header */}
      <div className="space-y-1.5">
        <h1 className="text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">
          {lesson.title}
        </h1>
      </div>

      {/* Reading Tab View */}
      {activeTab === "reading" && (
        <div className="space-y-6">
          <Card className="border-subtle bg-surface shadow-xs overflow-hidden">
            <CardContent className="p-6 sm:p-10">
              <MarkdownRenderer content={lesson.content_md} />
            </CardContent>
          </Card>

          {/* Mark Completed & Next Steps */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-subtle bg-surface-2/40 p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-success-soft text-success shrink-0">
                <CheckCircle2 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-foreground">Finished reading this lesson?</p>
                <p className="text-[11px] text-muted">
                  {exercise
                    ? "Complete the coding challenge to reinforce your understanding."
                    : "Mark this lesson as completed to track your curriculum progress."}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {exercise ? (
                <Button
                  onClick={() => setActiveTab("exercise")}
                  className="font-semibold gap-1.5 text-xs"
                >
                  <Code2 className="h-3.5 w-3.5" />
                  <span>Start Coding Challenge</span>
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => completeMutation.mutate(lesson.id)}
                  disabled={completeMutation.isPending}
                  className="font-semibold gap-1.5 text-xs"
                >
                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                  <span>Mark as Completed</span>
                </Button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Coding Exercise Tab View */}
      {activeTab === "exercise" && exercise && (
        <ExerciseWorkspace
          key={exercise.id}
          exercise={exercise}
          onCompleted={handleLessonCompleted}
        />
      )}
    </div>
  );
}
