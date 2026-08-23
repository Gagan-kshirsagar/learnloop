import { apiClient } from "@/lib/api/client";

export interface LessonSummary {
  id: string;
  module_id: string;
  title: string;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface LessonDetail {
  id: string;
  tenant_id: string;
  module_id: string;
  title: string;
  content_md: string;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface ModuleDetail {
  id: string;
  tenant_id: string;
  course_id: string;
  title: string;
  position: number;
  created_at: string;
  lessons: LessonSummary[];
}

export interface CourseSummary {
  id: string;
  tenant_id: string;
  title: string;
  slug: string;
  description: string | null;
  status: "draft" | "published";
  created_by: string | null;
  created_at: string;
  updated_at: string;
  module_count: number;
  lesson_count: number;
}

export interface CourseDetail {
  id: string;
  tenant_id: string;
  title: string;
  slug: string;
  description: string | null;
  status: "draft" | "published";
  created_by: string | null;
  created_at: string;
  updated_at: string;
  modules: ModuleDetail[];
}

export interface CreateCoursePayload {
  title: string;
  slug?: string;
  description?: string;
  status?: "draft" | "published";
}

export interface UpdateCoursePayload {
  title?: string;
  slug?: string;
  description?: string;
  status?: "draft" | "published";
}

export interface CreateModulePayload {
  course_id: string;
  title: string;
  position?: number;
}

export interface UpdateModulePayload {
  title?: string;
  position?: number;
}

export interface ReorderModulesPayload {
  course_id: string;
  ordered_module_ids: string[];
}

export interface CreateLessonPayload {
  module_id: string;
  title: string;
  content_md?: string;
  position?: number;
}

export interface UpdateLessonPayload {
  title?: string;
  content_md?: string;
  position?: number;
}

export interface ReorderLessonsPayload {
  module_id: string;
  ordered_lesson_ids: string[];
}

// ── API Client Methods ──

export async function fetchCourses(params?: {
  published?: boolean;
  search?: string;
}): Promise<CourseSummary[]> {
  const res = await apiClient.get<CourseSummary[]>("/api/v1/catalog/courses", {
    params,
  });
  return res.data;
}

export async function fetchCourseDetail(courseId: string): Promise<CourseDetail> {
  const res = await apiClient.get<CourseDetail>(`/api/v1/catalog/courses/${courseId}`);
  return res.data;
}

export async function fetchLessonDetail(lessonId: string): Promise<LessonDetail> {
  const res = await apiClient.get<LessonDetail>(`/api/v1/catalog/lessons/${lessonId}`);
  return res.data;
}

export async function createCourse(payload: CreateCoursePayload): Promise<CourseDetail> {
  const res = await apiClient.post<CourseDetail>("/api/v1/catalog/courses", payload);
  return res.data;
}

export async function updateCourse(
  courseId: string,
  payload: UpdateCoursePayload
): Promise<CourseDetail> {
  const res = await apiClient.patch<CourseDetail>(
    `/api/v1/catalog/courses/${courseId}`,
    payload
  );
  return res.data;
}

export async function publishCourse(
  courseId: string,
  status: "draft" | "published"
): Promise<CourseDetail> {
  const res = await apiClient.post<CourseDetail>(
    `/api/v1/catalog/courses/${courseId}/publish`,
    { status }
  );
  return res.data;
}

export async function deleteCourse(courseId: string): Promise<void> {
  await apiClient.delete(`/api/v1/catalog/courses/${courseId}`);
}

export async function createModule(payload: CreateModulePayload): Promise<ModuleDetail> {
  const res = await apiClient.post<ModuleDetail>("/api/v1/catalog/modules", payload);
  return res.data;
}

export async function updateModule(
  moduleId: string,
  payload: UpdateModulePayload
): Promise<ModuleDetail> {
  const res = await apiClient.patch<ModuleDetail>(
    `/api/v1/catalog/modules/${moduleId}`,
    payload
  );
  return res.data;
}

export async function deleteModule(moduleId: string): Promise<void> {
  await apiClient.delete(`/api/v1/catalog/modules/${moduleId}`);
}

export async function reorderModules(
  payload: ReorderModulesPayload
): Promise<ModuleDetail[]> {
  const res = await apiClient.post<ModuleDetail[]>(
    "/api/v1/catalog/modules/reorder",
    payload
  );
  return res.data;
}

export async function createLesson(payload: CreateLessonPayload): Promise<LessonDetail> {
  const res = await apiClient.post<LessonDetail>("/api/v1/catalog/lessons", payload);
  return res.data;
}

export async function updateLesson(
  lessonId: string,
  payload: UpdateLessonPayload
): Promise<LessonDetail> {
  const res = await apiClient.patch<LessonDetail>(
    `/api/v1/catalog/lessons/${lessonId}`,
    payload
  );
  return res.data;
}

export async function deleteLesson(lessonId: string): Promise<void> {
  await apiClient.delete(`/api/v1/catalog/lessons/${lessonId}`);
}

export async function reorderLessons(
  payload: ReorderLessonsPayload
): Promise<LessonSummary[]> {
  const res = await apiClient.post<LessonSummary[]>(
    "/api/v1/catalog/lessons/reorder",
    payload
  );
  return res.data;
}
