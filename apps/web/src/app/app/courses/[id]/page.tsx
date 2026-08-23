"use client";

import { use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  FileText,
  GraduationCap,
  Layers,
  Loader2,
  Play,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useCourseDetailQuery } from "@/lib/query/catalog";
import { useEnrollInCourseMutation, useMyEnrollmentsQuery } from "@/lib/query/learning";

interface CourseDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CourseDetailPage({ params }: CourseDetailPageProps) {
  const resolvedParams = use(params);
  const courseId = resolvedParams.id;

  const { data: course, isLoading, error, refetch } = useCourseDetailQuery(courseId);
  const { data: enrollments } = useMyEnrollmentsQuery();
  const enrollMutation = useEnrollInCourseMutation();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-32 rounded-md" />
        <div className="rounded-2xl border border-subtle bg-surface p-8 space-y-4">
          <Skeleton className="h-8 w-2/3 rounded-md" />
          <Skeleton className="h-16 w-full rounded-md" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-32 w-full rounded-2xl" />
          <Skeleton className="h-32 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger-soft p-8 text-center">
        <p className="text-sm font-semibold text-danger">Course not found or unavailable</p>
        <p className="mt-1 text-xs text-muted">
          This course may be unpublished or does not exist in your organization.
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

  const userEnrollment = enrollments?.find((e) => e.course_id === course.id);
  const isEnrolled = !!userEnrollment;

  const firstLesson = course.modules?.[0]?.lessons?.[0];
  const totalLessons = course.modules?.reduce((acc, m) => acc + m.lessons.length, 0) || 0;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-muted">
        <Link href="/app/courses" className="flex items-center gap-1 hover:text-foreground transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>All Courses</span>
        </Link>
        <span>/</span>
        <span className="text-foreground font-medium truncate max-w-xs">{course.title}</span>
      </div>

      {/* Course Banner Card */}
      <Card className="border-subtle bg-surface shadow-xs">
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                {isEnrolled && (
                  <Badge className="bg-success-soft text-success border-success/30 gap-1 text-[11px] font-bold">
                    <CheckCircle2 className="h-3 w-3" />
                    Enrolled ({userEnrollment.progress_percentage}% Completed)
                  </Badge>
                )}
              </div>
              <CardTitle className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                {course.title}
              </CardTitle>
              <p className="text-sm leading-relaxed text-muted max-w-2xl">
                {course.description || "No description provided for this course."}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {isEnrolled ? (
                firstLesson && (
                  <Link href={`/app/lessons/${firstLesson.id}`}>
                    <Button className="font-semibold gap-2 shadow-xs">
                      <Play className="h-3.5 w-3.5 fill-current" />
                      <span>Continue Learning</span>
                    </Button>
                  </Link>
                )
              ) : (
                <Button
                  onClick={() => enrollMutation.mutate(course.id)}
                  disabled={enrollMutation.isPending}
                  className="font-semibold gap-2 shadow-xs"
                >
                  {enrollMutation.isPending ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Enrolling…</span>
                    </>
                  ) : (
                    <>
                      <GraduationCap className="h-4 w-4" />
                      <span>Enroll in Course</span>
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-muted border-t border-subtle/60 pt-4">
            <div className="flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-accent" />
              <span>{course.modules?.length || 0} Modules</span>
            </div>
            <div className="flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5 text-accent" />
              <span>{totalLessons} Lessons</span>
            </div>
            <span className="text-faint">·</span>
            <span className="text-faint font-mono text-[11px]">Slug: {course.slug}</span>
          </div>
        </CardHeader>
      </Card>

      {/* Course Syllabus / Outline */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-accent" />
          <span>Course Outline</span>
        </h2>

        {course.modules && course.modules.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-subtle bg-surface/50 p-8 text-center text-xs text-muted">
            No modules have been added to this course yet.
          </div>
        ) : (
          <div className="space-y-4">
            {course.modules?.map((mod, modIdx) => (
              <Card key={mod.id} className="border-subtle bg-surface overflow-hidden shadow-xs">
                <div className="border-b border-subtle/60 bg-surface-2/40 px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-md bg-accent-soft font-mono text-[11px] font-bold text-accent">
                      {modIdx + 1}
                    </span>
                    <h3 className="text-sm font-bold text-foreground">{mod.title}</h3>
                  </div>
                  <span className="text-[11px] text-muted font-medium">
                    {mod.lessons.length} {mod.lessons.length === 1 ? "lesson" : "lessons"}
                  </span>
                </div>

                <CardContent className="p-0 divide-y divide-subtle/50">
                  {mod.lessons.length === 0 ? (
                    <div className="p-4 text-xs text-faint italic text-center">
                      No lessons in this module yet.
                    </div>
                  ) : (
                    mod.lessons.map((lesson, lesIdx) => (
                      <Link
                        key={lesson.id}
                        href={`/app/lessons/${lesson.id}`}
                        className="flex items-center justify-between px-5 py-3 transition-colors hover:bg-surface-2/60 group"
                      >
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-xs text-faint w-4">
                            {lesIdx + 1}.
                          </span>
                          <span className="text-xs font-medium text-foreground group-hover:text-accent transition-colors">
                            {lesson.title}
                          </span>
                        </div>
                        <ChevronRight className="h-3.5 w-3.5 text-muted group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
                      </Link>
                    ))
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
