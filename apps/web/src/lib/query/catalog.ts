import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createCourse,
  createLesson,
  createModule,
  deleteCourse,
  deleteLesson,
  deleteModule,
  fetchCourseDetail,
  fetchCourses,
  fetchLessonDetail,
  publishCourse,
  reorderLessons,
  reorderModules,
  updateCourse,
  updateLesson,
  updateModule,
  type CourseDetail,
  type CourseSummary,
  type CreateCoursePayload,
  type CreateLessonPayload,
  type CreateModulePayload,
  type LessonDetail,
  type ReorderLessonsPayload,
  type ReorderModulesPayload,
  type UpdateCoursePayload,
  type UpdateLessonPayload,
  type UpdateModulePayload,
} from "@/lib/api/catalog";

export const catalogKeys = {
  all: ["catalog"] as const,
  courses: (filters?: { published?: boolean; search?: string }) =>
    ["catalog", "courses", filters] as const,
  course: (id: string) => ["catalog", "course", id] as const,
  lesson: (id: string) => ["catalog", "lesson", id] as const,
};

// ── Query Hooks ──

export function useCoursesQuery(params?: { published?: boolean; search?: string }) {
  return useQuery<CourseSummary[]>({
    queryKey: catalogKeys.courses(params),
    queryFn: () => fetchCourses(params),
    staleTime: 1000 * 30, // 30 seconds
  });
}

export function useCourseDetailQuery(courseId: string) {
  return useQuery<CourseDetail>({
    queryKey: catalogKeys.course(courseId),
    queryFn: () => fetchCourseDetail(courseId),
    enabled: !!courseId,
    staleTime: 1000 * 30,
  });
}

export function useLessonDetailQuery(lessonId: string) {
  return useQuery<LessonDetail>({
    queryKey: catalogKeys.lesson(lessonId),
    queryFn: () => fetchLessonDetail(lessonId),
    enabled: !!lessonId,
    staleTime: 1000 * 60,
  });
}

// ── Mutation Hooks ──

export function useCreateCourseMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateCoursePayload) => createCourse(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.all });
    },
  });
}

export function useUpdateCourseMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateCoursePayload) => updateCourse(courseId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(catalogKeys.course(courseId), data);
      queryClient.invalidateQueries({ queryKey: catalogKeys.courses() });
    },
  });
}

export function usePublishCourseMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: "draft" | "published") => publishCourse(courseId, status),
    onSuccess: (data) => {
      queryClient.setQueryData(catalogKeys.course(courseId), data);
      queryClient.invalidateQueries({ queryKey: catalogKeys.courses() });
    },
  });
}

export function useDeleteCourseMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (courseId: string) => deleteCourse(courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.all });
    },
  });
}

export function useCreateModuleMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateModulePayload) => createModule(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}

export function useUpdateModuleMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ moduleId, payload }: { moduleId: string; payload: UpdateModulePayload }) =>
      updateModule(moduleId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}

export function useDeleteModuleMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (moduleId: string) => deleteModule(moduleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}

export function useReorderModulesMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReorderModulesPayload) => reorderModules(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}

export function useCreateLessonMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateLessonPayload) => createLesson(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}

export function useUpdateLessonMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lessonId, payload }: { lessonId: string; payload: UpdateLessonPayload }) =>
      updateLesson(lessonId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(catalogKeys.lesson(data.id), data);
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}

export function useDeleteLessonMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (lessonId: string) => deleteLesson(lessonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}

export function useReorderLessonsMutation(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReorderLessonsPayload) => reorderLessons(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: catalogKeys.course(courseId) });
    },
  });
}
