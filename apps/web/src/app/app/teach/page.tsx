"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BookOpen,
  Edit,
  GraduationCap,
  Layers,
  Loader2,
  Plus,
  Radio,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCoursesQuery,
  useCreateCourseMutation,
  useDeleteCourseMutation,
  usePublishCourseMutation,
} from "@/lib/query/catalog";

export default function TeachPage() {
  const router = useRouter();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const { data: courses, isLoading, error, refetch } = useCoursesQuery({
    published: undefined, // Author sees all courses (draft & published)
  });

  const createCourseMutation = useCreateCourseMutation();
  const publishMutation = usePublishCourseMutation("");
  const deleteMutation = useDeleteCourseMutation();

  const handleCreateCourse = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    createCourseMutation.mutate(
      { title: title.trim(), description: description.trim() || undefined },
      {
        onSuccess: (newCourse) => {
          setShowCreateModal(false);
          setTitle("");
          setDescription("");
          router.push(`/app/teach/${newCourse.id}`);
        },
      }
    );
  };

  const handleTogglePublish = (courseId: string, currentStatus: "draft" | "published") => {
    const nextStatus = currentStatus === "published" ? "draft" : "published";
    publishMutation.mutate(nextStatus, {
      onSuccess: () => refetch(),
    });
  };

  const handleDeleteCourse = (courseId: string, courseTitle: string) => {
    if (confirm(`Are you sure you want to delete "${courseTitle}"? This will delete all its modules and lessons.`)) {
      deleteMutation.mutate(courseId, {
        onSuccess: () => refetch(),
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <GraduationCap className="h-6 w-6 text-accent" />
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Course Authoring
            </h1>
          </div>
          <p className="mt-1 text-sm text-muted">
            Create, organize, and publish course curricula with interactive Socratic modules.
          </p>
        </div>

        <Button
          onClick={() => setShowCreateModal(true)}
          className="font-semibold gap-1.5 shadow-xs shrink-0"
        >
          <Plus className="h-4 w-4" />
          <span>New Course</span>
        </Button>
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
          <p className="text-sm font-semibold text-danger">Failed to load instructor courses</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-3 rounded-lg bg-surface px-4 py-1.5 text-xs font-semibold text-foreground border border-subtle shadow-xs hover:bg-surface-2"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && courses && courses.length === 0 && (
        <div className="rounded-2xl border border-dashed border-subtle bg-surface/50 p-12 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-accent">
            <BookOpen className="h-6 w-6" />
          </div>
          <h3 className="text-base font-bold text-foreground">No courses created yet</h3>
          <p className="mx-auto mt-1 max-w-sm text-xs text-muted">
            Create your first course to begin authoring modules and Socratic lessons.
          </p>
          <Button
            onClick={() => setShowCreateModal(true)}
            size="sm"
            className="mt-5 font-semibold gap-1.5"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Create Course</span>
          </Button>
        </div>
      )}

      {/* Course Cards Grid */}
      {!isLoading && courses && courses.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => {
            const isPublished = course.status === "published";
            return (
              <Card key={course.id} className="border-subtle bg-surface flex flex-col justify-between shadow-xs">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base font-bold text-foreground line-clamp-1">
                      {course.title}
                    </CardTitle>
                    <Badge
                      variant={isPublished ? "default" : "secondary"}
                      className={`text-[10px] uppercase font-bold shrink-0 ${
                        isPublished
                          ? "bg-success-soft text-success border-success/30"
                          : "bg-surface-2 text-muted"
                      }`}
                    >
                      {isPublished ? (
                        <span className="flex items-center gap-1">
                          <Radio className="h-2 w-2 animate-pulse" />
                          Published
                        </span>
                      ) : (
                        "Draft"
                      )}
                    </Badge>
                  </div>
                  <CardDescription className="line-clamp-2 text-xs leading-relaxed">
                    {course.description || "No description provided."}
                  </CardDescription>
                </CardHeader>

                <CardContent className="pt-0 space-y-4">
                  <div className="flex items-center gap-4 text-[11px] font-medium text-muted border-t border-subtle/60 pt-3">
                    <div className="flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5 text-accent" />
                      <span>{course.module_count} Modules</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <BookOpen className="h-3.5 w-3.5 text-accent" />
                      <span>{course.lesson_count} Lessons</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-1 border-t border-subtle/50">
                    <Link href={`/app/teach/${course.id}`} className="flex-1">
                      <Button variant="outline" size="sm" className="w-full text-xs font-semibold gap-1.5">
                        <Edit className="h-3.5 w-3.5" />
                        <span>Edit Course</span>
                      </Button>
                    </Link>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTogglePublish(course.id, course.status)}
                      className={`text-xs px-2.5 ${
                        isPublished
                          ? "text-muted hover:text-amber-600 dark:hover:text-amber-400"
                          : "text-accent hover:text-accent-hover font-semibold"
                      }`}
                    >
                      {isPublished ? "Unpublish" : "Publish"}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteCourse(course.id, course.title)}
                      className="text-danger hover:bg-danger-soft px-2 h-8"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Course Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-subtle bg-surface p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-foreground">Create New Course</h3>
            <p className="text-xs text-muted">
              Add course details. You can author modules, lessons, and change publish status anytime.
            </p>

            <form onSubmit={handleCreateCourse} className="space-y-3.5">
              <div className="space-y-1.5">
                <label htmlFor="course-title" className="text-xs font-medium text-foreground">
                  Course Title
                </label>
                <Input
                  id="course-title"
                  placeholder="e.g. Data Structures & Algorithms"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="h-9 text-xs"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="course-desc" className="text-xs font-medium text-foreground">
                  Description (Optional)
                </label>
                <textarea
                  id="course-desc"
                  rows={3}
                  placeholder="Brief overview of course topics..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-md border border-subtle bg-surface p-2.5 text-xs text-foreground placeholder:text-faint focus-visible:outline-2 focus-visible:outline-ring"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={createCourseMutation.isPending || !title.trim()}
                  className="font-semibold"
                >
                  {createCourseMutation.isPending ? (
                    <>
                      <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                      Creating…
                    </>
                  ) : (
                    "Create Course"
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
