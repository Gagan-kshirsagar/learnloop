"use client";

import { use, useCallback, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Code2,
  Share2,
  Sparkles,
} from "lucide-react";

import { ExerciseWorkspace } from "@/components/exercise/ExerciseWorkspace";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { TutorPanel } from "@/components/tutor/TutorPanel";
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

  const [activeTab, setActiveTab] = useState<"reading" | "exercise" | "tutor">("reading");

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
          <div className="flex items-center rounded-xl border border-subtle bg-surface-2 p-1 text-xs shadow-xs">
            <button
              type="button"
              onClick={() => setActiveTab("reading")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "reading"
                  ? "bg-surface text-foreground font-semibold shadow-xs"
                  : "text-muted hover:text-foreground"
              }`}
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Reading</span>
            </button>
            {exercise && (
              <button
                type="button"
                onClick={() => setActiveTab("exercise")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeTab === "exercise"
                    ? "bg-surface text-foreground font-semibold shadow-xs"
                    : "text-muted hover:text-foreground"
                }`}
              >
                <Code2 className="h-3.5 w-3.5 text-accent" />
                <span>Exercise</span>
                <Badge variant="outline" className="text-[9px] px-1.5 py-0 border-accent/40 text-accent font-mono rounded">
                  Python
                </Badge>
              </button>
            )}
            <button
              type="button"
              onClick={() => setActiveTab("tutor")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "tutor"
                  ? "bg-surface text-foreground font-semibold shadow-xs"
                  : "text-muted hover:text-foreground"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5 text-accent" />
              <span>Ask Tutor</span>
            </button>
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2.5 text-xs text-muted hover:text-foreground rounded-xl"
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

      {/* Reading Tab View */}
      {activeTab === "reading" && (
        <div className="space-y-6">
          <div className="space-y-2 border-b border-subtle pb-4">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] font-mono rounded-md px-2 py-0.5 border-subtle bg-surface-2 text-muted font-medium">
                Lesson #{lesson.position}
              </Badge>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              {lesson.title}
            </h1>
          </div>

          <Card className="border-subtle bg-surface shadow-xs">
            <CardContent className="p-6 sm:p-8">
              <MarkdownRenderer content={lesson.content_md} />
            </CardContent>
          </Card>

          {/* Lesson Completion / Next CTA Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 rounded-2xl border border-subtle bg-surface-2/60 p-4 shadow-xs">
            <div className="text-xs text-muted">
              {exercise
                ? "This lesson includes an interactive coding exercise to test your understanding."
                : "Finished reviewing the concepts in this lesson?"}
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setActiveTab("tutor")}
                className="gap-1.5 text-xs rounded-xl"
              >
                <Sparkles className="h-3.5 w-3.5 text-accent" />
                <span>Ask Question</span>
              </Button>
              {exercise ? (
                <Button
                  size="sm"
                  onClick={() => setActiveTab("exercise")}
                  className="bg-accent text-accent-foreground font-semibold gap-1.5 text-xs rounded-xl shadow-xs"
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
                  className="font-semibold gap-1.5 text-xs rounded-xl shadow-xs"
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

      {/* Ask Tutor Tab View */}
      {activeTab === "tutor" && (
        <TutorPanel
          lessonId={lesson.id}
          lessonTitle={lesson.title}
          exerciseId={exercise?.id}
        />
      )}
    </div>
  );
}
