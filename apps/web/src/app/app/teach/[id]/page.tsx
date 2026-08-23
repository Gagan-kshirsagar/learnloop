"use client";

import { use, useState } from "react";
import Link from "next/link";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Check,
  Edit,
  Eye,
  FileCode,
  Layers,
  Loader2,
  Plus,
  Radio,
  Save,
  Trash2,
  X,
} from "lucide-react";

import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCourseDetailQuery,
  useCreateLessonMutation,
  useCreateModuleMutation,
  useDeleteLessonMutation,
  useDeleteModuleMutation,
  usePublishCourseMutation,
  useReorderLessonsMutation,
  useReorderModulesMutation,
  useUpdateCourseMutation,
  useUpdateLessonMutation,
  useUpdateModuleMutation,
} from "@/lib/query/catalog";

interface TeachCoursePageProps {
  params: Promise<{ id: string }>;
}

export default function TeachCoursePage({ params }: TeachCoursePageProps) {
  const resolvedParams = use(params);
  const courseId = resolvedParams.id;

  const { data: course, isLoading, error, refetch } = useCourseDetailQuery(courseId);

  // Course Meta Edit State
  const [isEditingMeta, setIsEditingMeta] = useState(false);
  const [metaTitle, setMetaTitle] = useState("");
  const [metaDesc, setMetaDesc] = useState("");
  const [metaSlug, setMetaSlug] = useState("");

  // Module Create / Edit State
  const [showAddModuleModal, setShowAddModuleModal] = useState(false);
  const [moduleTitle, setModuleTitle] = useState("");
  const [editingModuleId, setEditingModuleId] = useState<string | null>(null);
  const [editingModuleTitle, setEditingModuleTitle] = useState("");

  // Lesson Create / Edit State
  const [lessonModalMode, setLessonModalMode] = useState<"create" | "edit" | null>(null);
  const [targetModuleId, setTargetModuleId] = useState<string | null>(null);
  const [targetLessonId, setTargetLessonId] = useState<string | null>(null);
  const [lessonTitle, setLessonTitle] = useState("");
  const [lessonContent, setLessonContent] = useState("");
  const [lessonTab, setLessonTab] = useState<"write" | "preview">("write");

  // Mutations
  const updateCourseMutation = useUpdateCourseMutation(courseId);
  const publishMutation = usePublishCourseMutation(courseId);
  const createModuleMutation = useCreateModuleMutation(courseId);
  const updateModuleMutation = useUpdateModuleMutation(courseId);
  const deleteModuleMutation = useDeleteModuleMutation(courseId);
  const reorderModulesMutation = useReorderModulesMutation(courseId);
  const createLessonMutation = useCreateLessonMutation(courseId);
  const updateLessonMutation = useUpdateLessonMutation(courseId);
  const deleteLessonMutation = useDeleteLessonMutation(courseId);
  const reorderLessonsMutation = useReorderLessonsMutation(courseId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-6 w-36 rounded-md" />
        <Skeleton className="h-44 w-full rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="rounded-2xl border border-danger/30 bg-danger-soft p-8 text-center">
        <p className="text-sm font-semibold text-danger">Course not found</p>
        <div className="mt-4 flex items-center justify-center gap-3">
          <Link href="/app/teach">
            <Button size="sm" variant="outline">Back to Authoring</Button>
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

  const isPublished = course.status === "published";

  const handleStartEditingMeta = () => {
    setMetaTitle(course.title);
    setMetaDesc(course.description || "");
    setMetaSlug(course.slug);
    setIsEditingMeta(true);
  };

  const handleSaveMeta = () => {
    updateCourseMutation.mutate(
      {
        title: metaTitle.trim() || undefined,
        description: metaDesc.trim() || undefined,
        slug: metaSlug.trim() || undefined,
      },
      {
        onSuccess: () => setIsEditingMeta(false),
      }
    );
  };

  const handleTogglePublish = () => {
    publishMutation.mutate(isPublished ? "draft" : "published");
  };

  const handleCreateModule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!moduleTitle.trim()) return;

    createModuleMutation.mutate(
      { course_id: courseId, title: moduleTitle.trim() },
      {
        onSuccess: () => {
          setModuleTitle("");
          setShowAddModuleModal(false);
        },
      }
    );
  };

  const handleSaveModuleTitle = (moduleId: string) => {
    if (!editingModuleTitle.trim()) return;
    updateModuleMutation.mutate(
      { moduleId, payload: { title: editingModuleTitle.trim() } },
      {
        onSuccess: () => setEditingModuleId(null),
      }
    );
  };

  const handleMoveModule = (currentIndex: number, direction: "up" | "down") => {
    if (!course.modules) return;
    const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= course.modules.length) return;

    const newOrder = [...course.modules];
    const temp = newOrder[currentIndex];
    newOrder[currentIndex] = newOrder[targetIndex];
    newOrder[targetIndex] = temp;

    reorderModulesMutation.mutate({
      course_id: courseId,
      ordered_module_ids: newOrder.map((m) => m.id),
    });
  };

  const handleMoveLesson = (
    moduleId: string,
    lessons: Array<{ id: string }>,
    currentIndex: number,
    direction: "up" | "down"
  ) => {
    const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= lessons.length) return;

    const newOrder = [...lessons];
    const temp = newOrder[currentIndex];
    newOrder[currentIndex] = newOrder[targetIndex];
    newOrder[targetIndex] = temp;

    reorderLessonsMutation.mutate({
      module_id: moduleId,
      ordered_lesson_ids: newOrder.map((l) => l.id),
    });
  };

  const handleOpenCreateLesson = (moduleId: string) => {
    setTargetModuleId(moduleId);
    setTargetLessonId(null);
    setLessonTitle("");
    setLessonContent("# New Lesson\n\nExplain the core concept here...\n\n```python\n# Example code block\n```");
    setLessonTab("write");
    setLessonModalMode("create");
  };

  const handleOpenEditLesson = async (moduleId: string, lessonId: string, currentTitle: string) => {
    setTargetModuleId(moduleId);
    setTargetLessonId(lessonId);
    setLessonTitle(currentTitle);
    setLessonContent("Loading lesson markdown...");
    setLessonTab("write");
    setLessonModalMode("edit");

    // Fetch full lesson content
    try {
      const { fetchLessonDetail } = await import("@/lib/api/catalog");
      const data = await fetchLessonDetail(lessonId);
      setLessonContent(data.content_md);
    } catch {
      setLessonContent("# Error loading content\nPlease check your network.");
    }
  };

  const handleSaveLesson = (e: React.FormEvent) => {
    e.preventDefault();
    if (!lessonTitle.trim()) return;

    if (lessonModalMode === "create" && targetModuleId) {
      createLessonMutation.mutate(
        {
          module_id: targetModuleId,
          title: lessonTitle.trim(),
          content_md: lessonContent,
        },
        {
          onSuccess: () => setLessonModalMode(null),
        }
      );
    } else if (lessonModalMode === "edit" && targetLessonId) {
      updateLessonMutation.mutate(
        {
          lessonId: targetLessonId,
          payload: {
            title: lessonTitle.trim(),
            content_md: lessonContent,
          },
        },
        {
          onSuccess: () => setLessonModalMode(null),
        }
      );
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          href="/app/teach"
          className="flex items-center gap-1.5 text-xs font-medium text-muted hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Authoring</span>
        </Link>

        <div className="flex items-center gap-3">
          <Badge
            variant={isPublished ? "default" : "secondary"}
            className={`text-[10px] uppercase font-bold ${
              isPublished
                ? "bg-success-soft text-success border-success/30"
                : "bg-surface-2 text-muted"
            }`}
          >
            {isPublished ? (
              <span className="flex items-center gap-1">
                <Radio className="h-2 w-2 animate-pulse" />
                Live on Catalog
              </span>
            ) : (
              "Draft (Hidden from Students)"
            )}
          </Badge>

          <Button
            size="sm"
            onClick={handleTogglePublish}
            disabled={publishMutation.isPending}
            className={`text-xs font-semibold ${
              isPublished
                ? "bg-surface-2 text-foreground hover:bg-surface border border-subtle"
                : "bg-accent text-accent-foreground hover:bg-accent-hover"
            }`}
          >
            {publishMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : isPublished ? (
              "Unpublish to Draft"
            ) : (
              "Publish Course"
            )}
          </Button>
        </div>
      </div>

      {/* Course Meta Card */}
      <Card className="border-subtle bg-surface shadow-xs">
        <CardHeader className="space-y-3">
          {!isEditingMeta ? (
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  {course.title}
                </CardTitle>
                <p className="mt-2 text-sm text-muted leading-relaxed max-w-2xl">
                  {course.description || "No description. Click edit to add a course overview."}
                </p>
                <p className="mt-3 text-xs font-mono text-faint">
                  Slug: <span className="text-foreground">{course.slug}</span>
                </p>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={handleStartEditingMeta}
                className="gap-1.5 text-xs font-semibold shrink-0"
              >
                <Edit className="h-3.5 w-3.5" />
                <span>Edit Metadata</span>
              </Button>
            </div>
          ) : (
            <div className="space-y-4 p-2">
              <h3 className="text-sm font-bold text-foreground">Edit Course Details</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-foreground">Title</label>
                  <Input
                    value={metaTitle}
                    onChange={(e) => setMetaTitle(e.target.value)}
                    className="h-9 text-xs mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-foreground">Slug</label>
                  <Input
                    value={metaSlug}
                    onChange={(e) => setMetaSlug(e.target.value)}
                    className="h-9 text-xs mt-1 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-foreground">Description</label>
                  <textarea
                    rows={3}
                    value={metaDesc}
                    onChange={(e) => setMetaDesc(e.target.value)}
                    className="w-full rounded-md border border-subtle bg-surface p-2.5 text-xs text-foreground mt-1 focus-visible:outline-2 focus-visible:outline-ring"
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <Button
                    size="sm"
                    onClick={handleSaveMeta}
                    disabled={updateCourseMutation.isPending}
                    className="font-semibold gap-1.5"
                  >
                    {updateCourseMutation.isPending ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Save className="h-3.5 w-3.5" />
                    )}
                    <span>Save Changes</span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditingMeta(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardHeader>
      </Card>

      {/* Curriculum Outline Management */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-bold text-foreground">Course Modules &amp; Lessons</h2>
          </div>

          <Button
            size="sm"
            onClick={() => setShowAddModuleModal(true)}
            className="font-semibold gap-1.5 shadow-xs text-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Module</span>
          </Button>
        </div>

        {course.modules && course.modules.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-subtle bg-surface/50 p-8 text-center">
            <p className="text-xs text-muted">No modules added yet. Create your first module to start organizing lessons.</p>
            <Button
              size="sm"
              onClick={() => setShowAddModuleModal(true)}
              className="mt-3 text-xs"
            >
              Add First Module
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {course.modules?.map((mod, modIdx) => (
              <Card key={mod.id} className="border-subtle bg-surface overflow-hidden shadow-xs">
                {/* Module Header Bar */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-subtle/70 bg-surface-2/50 px-4 py-3">
                  <div className="flex items-center gap-2 flex-1 min-w-[200px]">
                    <span className="flex h-5 w-5 items-center justify-center rounded-md bg-accent font-mono text-[10px] font-bold text-accent-foreground shrink-0">
                      {modIdx + 1}
                    </span>

                    {editingModuleId === mod.id ? (
                      <div className="flex items-center gap-2 flex-1">
                        <Input
                          value={editingModuleTitle}
                          onChange={(e) => setEditingModuleTitle(e.target.value)}
                          className="h-7 text-xs"
                          autoFocus
                        />
                        <Button
                          size="sm"
                          className="h-7 px-2"
                          onClick={() => handleSaveModuleTitle(mod.id)}
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2"
                          onClick={() => setEditingModuleId(null)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ) : (
                      <h3 className="text-sm font-bold text-foreground truncate">{mod.title}</h3>
                    )}
                  </div>

                  {/* Module Action Controls */}
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={modIdx === 0}
                      onClick={() => handleMoveModule(modIdx, "up")}
                      className="h-7 w-7 p-0 text-muted hover:text-foreground"
                      title="Move Module Up"
                    >
                      <ArrowUp className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={modIdx === (course.modules?.length || 1) - 1}
                      onClick={() => handleMoveModule(modIdx, "down")}
                      className="h-7 w-7 p-0 text-muted hover:text-foreground"
                      title="Move Module Down"
                    >
                      <ArrowDown className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEditingModuleId(mod.id);
                        setEditingModuleTitle(mod.title);
                      }}
                      className="h-7 px-2 text-xs text-muted hover:text-foreground"
                    >
                      <Edit className="h-3 w-3 mr-1" />
                      <span>Rename</span>
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete module "${mod.title}" and its lessons?`)) {
                          deleteModuleMutation.mutate(mod.id);
                        }
                      }}
                      className="h-7 px-2 text-xs text-danger hover:bg-danger-soft"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {/* Lessons in Module */}
                <CardContent className="p-0">
                  <div className="divide-y divide-subtle/50">
                    {mod.lessons.map((lesson, lesIdx) => (
                      <div
                        key={lesson.id}
                        className="flex items-center justify-between px-4 py-2.5 transition-colors hover:bg-surface-2/40"
                      >
                        <div className="flex items-center gap-3">
                          <FileCode className="h-3.5 w-3.5 text-accent shrink-0" />
                          <span className="font-mono text-xs text-faint w-4">{lesIdx + 1}.</span>
                          <span className="text-xs font-semibold text-foreground">{lesson.title}</span>
                        </div>

                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={lesIdx === 0}
                            onClick={() => handleMoveLesson(mod.id, mod.lessons, lesIdx, "up")}
                            className="h-6 w-6 p-0 text-muted"
                          >
                            <ArrowUp className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={lesIdx === mod.lessons.length - 1}
                            onClick={() => handleMoveLesson(mod.id, mod.lessons, lesIdx, "down")}
                            className="h-6 w-6 p-0 text-muted"
                          >
                            <ArrowDown className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenEditLesson(mod.id, lesson.id, lesson.title)}
                            className="h-6 px-2 text-xs text-muted hover:text-foreground"
                          >
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (confirm(`Delete lesson "${lesson.title}"?`)) {
                                deleteLessonMutation.mutate(lesson.id);
                              }
                            }}
                            className="h-6 px-1.5 text-danger hover:bg-danger-soft"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Add Lesson Button in Module Footer */}
                  <div className="border-t border-subtle/50 bg-surface-2/20 p-2.5">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenCreateLesson(mod.id)}
                      className="w-full justify-center text-xs font-medium text-accent hover:bg-accent-soft h-8"
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      <span>Add Lesson to {mod.title}</span>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Add Module Modal */}
      {showAddModuleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-subtle bg-surface p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-foreground">Add New Module</h3>
            <form onSubmit={handleCreateModule} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-foreground">Module Title</label>
                <Input
                  placeholder="e.g. Graph Traversal & BFS"
                  value={moduleTitle}
                  onChange={(e) => setModuleTitle(e.target.value)}
                  className="h-9 text-xs mt-1"
                  required
                  autoFocus
                />
              </div>
              <div className="flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddModuleModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={createModuleMutation.isPending || !moduleTitle.trim()}
                  className="font-semibold"
                >
                  {createModuleMutation.isPending ? "Adding..." : "Add Module"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lesson Authoring Modal (Write + Live Preview) */}
      {lessonModalMode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl border border-subtle bg-surface shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-subtle bg-surface-2 px-5 py-3.5">
              <h3 className="text-sm font-bold text-foreground">
                {lessonModalMode === "create" ? "Add New Lesson" : "Edit Lesson & Content"}
              </h3>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0"
                onClick={() => setLessonModalMode(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Modal Body Form */}
            <form onSubmit={handleSaveLesson} className="flex flex-col flex-1 overflow-y-auto p-5 space-y-4">
              <div>
                <label className="text-xs font-medium text-foreground">Lesson Title</label>
                <Input
                  placeholder="e.g. Breadth-First Search Implementation"
                  value={lessonTitle}
                  onChange={(e) => setLessonTitle(e.target.value)}
                  className="h-9 text-xs mt-1"
                  required
                  autoFocus
                />
              </div>

              {/* Markdown Editor Tabs */}
              <div className="flex-1 flex flex-col space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-medium text-foreground">
                    Lesson Markdown Content
                  </label>
                  <div className="flex items-center rounded-lg border border-subtle bg-surface-2 p-0.5 text-xs">
                    <button
                      type="button"
                      onClick={() => setLessonTab("write")}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                        lessonTab === "write"
                          ? "bg-surface text-foreground font-semibold shadow-xs"
                          : "text-muted hover:text-foreground"
                      }`}
                    >
                      Write Markdown
                    </button>
                    <button
                      type="button"
                      onClick={() => setLessonTab("preview")}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1 ${
                        lessonTab === "preview"
                          ? "bg-surface text-foreground font-semibold shadow-xs"
                          : "text-muted hover:text-foreground"
                      }`}
                    >
                      <Eye className="h-3 w-3" />
                      Preview
                    </button>
                  </div>
                </div>

                {lessonTab === "write" ? (
                  <textarea
                    rows={12}
                    placeholder="# Lesson Heading&#10;&#10;Write explanation here...&#10;&#10;```python&#10;def solution():&#10;    pass&#10;```"
                    value={lessonContent}
                    onChange={(e) => setLessonContent(e.target.value)}
                    className="w-full flex-1 min-h-[260px] rounded-xl border border-subtle bg-surface p-4 font-mono text-xs text-foreground placeholder:text-faint focus-visible:outline-2 focus-visible:outline-ring"
                  />
                ) : (
                  <div className="w-full flex-1 min-h-[260px] max-h-[360px] overflow-y-auto rounded-xl border border-subtle bg-surface p-4 text-xs">
                    <MarkdownRenderer content={lessonContent} />
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end gap-2 border-t border-subtle pt-3">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setLessonModalMode(null)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={createLessonMutation.isPending || updateLessonMutation.isPending || !lessonTitle.trim()}
                  className="font-semibold"
                >
                  {createLessonMutation.isPending || updateLessonMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Save className="h-3.5 w-3.5 mr-1" />
                  )}
                  <span>Save Lesson</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
