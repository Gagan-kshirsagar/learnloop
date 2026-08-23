"use client";

import { useState } from "react";
import Link from "next/link";
import { BookOpen, ChevronRight, FileText, Layers, Search } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useCoursesQuery } from "@/lib/query/catalog";

export default function CoursesPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const { data: courses, isLoading, error, refetch } = useCoursesQuery({
    published: true,
    search: searchTerm || undefined,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Course Catalog
          </h1>
          <p className="mt-1 text-sm text-muted">
            Explore published courses grounded in your curriculum with Socratic guidance.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
          <Input
            type="search"
            placeholder="Search courses…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="h-9 pl-9 text-xs"
          />
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-2xl border border-subtle bg-surface p-6 space-y-4">
              <Skeleton className="h-6 w-3/4 rounded-md" />
              <Skeleton className="h-12 w-full rounded-md" />
              <div className="flex items-center gap-4 pt-2">
                <Skeleton className="h-4 w-20 rounded-md" />
                <Skeleton className="h-4 w-20 rounded-md" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="rounded-2xl border border-danger/30 bg-danger-soft p-6 text-center">
          <p className="text-sm font-semibold text-danger">Failed to load courses</p>
          <p className="mt-1 text-xs text-muted">Please check your connection and try again.</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-4 rounded-lg bg-surface px-4 py-1.5 text-xs font-semibold text-foreground border border-subtle shadow-xs hover:bg-surface-2"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && courses && courses.length === 0 && (
        <div className="rounded-2xl border border-dashed border-subtle bg-surface/50 p-12 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-accent">
            <BookOpen className="h-6 w-6" />
          </div>
          <h3 className="text-base font-bold text-foreground">No published courses</h3>
          <p className="mx-auto mt-1 max-w-sm text-xs text-muted">
            {searchTerm
              ? `No courses matching "${searchTerm}". Try a different search.`
              : "Your instructors haven't published any courses yet. Check back soon!"}
          </p>
        </div>
      )}

      {/* Course Cards Grid */}
      {!isLoading && courses && courses.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => (
            <Link
              key={course.id}
              href={`/app/courses/${course.id}`}
              className="group block transition-transform active:scale-[0.99]"
            >
              <Card className="h-full border-subtle bg-surface transition-all hover:border-strong hover:shadow-md">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base font-bold text-foreground group-hover:text-accent transition-colors line-clamp-1">
                      {course.title}
                    </CardTitle>
                    <ChevronRight className="h-4 w-4 text-muted group-hover:text-accent group-hover:translate-x-0.5 transition-all shrink-0 mt-0.5" />
                  </div>
                  <CardDescription className="line-clamp-2 text-xs leading-relaxed">
                    {course.description || "No description provided."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center gap-4 text-[11px] font-medium text-muted border-t border-subtle/60 pt-3">
                    <div className="flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5 text-accent" />
                      <span>{course.module_count} {course.module_count === 1 ? "module" : "modules"}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5 text-accent" />
                      <span>{course.lesson_count} {course.lesson_count === 1 ? "lesson" : "lessons"}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
