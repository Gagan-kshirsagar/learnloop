import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  completeLesson,
  enrollInCourse,
  fetchExerciseAuthor,
  fetchExerciseForLesson,
  fetchMyEnrollments,
  fetchSubmissionStatus,
  saveExerciseAuthor,
  submitExerciseCode,
  type Exercise,
  type ExerciseDetail,
  type MyEnrollmentSummary,
  type SaveExercisePayload,
  type SubmissionStatusResponse,
  type SubmitCodePayload,
} from "@/lib/api/learning";

export const learningKeys = {
  all: ["learning"] as const,
  enrollments: () => ["learning", "enrollments"] as const,
  exercise: (lessonId: string) => ["learning", "exercise", lessonId] as const,
  exerciseAuthor: (lessonId: string) => ["learning", "exercise", "author", lessonId] as const,
  submission: (submissionId: string) => ["learning", "submission", submissionId] as const,
};

// ── Query Hooks ──

export function useMyEnrollmentsQuery() {
  return useQuery<MyEnrollmentSummary[]>({
    queryKey: learningKeys.enrollments(),
    queryFn: fetchMyEnrollments,
    staleTime: 1000 * 15,
  });
}

export function useExerciseQuery(lessonId: string) {
  return useQuery<Exercise | null>({
    queryKey: learningKeys.exercise(lessonId),
    queryFn: () => fetchExerciseForLesson(lessonId),
    enabled: !!lessonId,
    staleTime: 1000 * 60,
  });
}

export function useExerciseAuthorQuery(lessonId: string) {
  return useQuery<ExerciseDetail | null>({
    queryKey: learningKeys.exerciseAuthor(lessonId),
    queryFn: () => fetchExerciseAuthor(lessonId),
    enabled: !!lessonId,
    staleTime: 1000 * 30,
  });
}

export function useSubmissionStatusQuery(submissionId: string | null) {
  return useQuery<SubmissionStatusResponse>({
    queryKey: learningKeys.submission(submissionId || ""),
    queryFn: () => fetchSubmissionStatus(submissionId!),
    enabled: !!submissionId,
    refetchInterval: (query) => {
      const currentStatus = query.state.data?.status;
      if (currentStatus === "queued" || currentStatus === "running") {
        return 600; // Poll every 600ms while evaluating
      }
      return false; // Stop polling on terminal state
    },
    staleTime: 0,
  });
}

// ── Mutation Hooks ──

export function useEnrollInCourseMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (courseId: string) => enrollInCourse(courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: learningKeys.enrollments() });
    },
  });
}

export function useSaveExerciseAuthorMutation(lessonId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SaveExercisePayload) => saveExerciseAuthor(lessonId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(learningKeys.exerciseAuthor(lessonId), data);
      queryClient.invalidateQueries({ queryKey: learningKeys.exercise(lessonId) });
    },
  });
}

export function useSubmitCodeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ exerciseId, payload }: { exerciseId: string; payload: SubmitCodePayload }) =>
      submitExerciseCode(exerciseId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: learningKeys.enrollments() });
    },
  });
}

export function useCompleteLessonMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (lessonId: string) => completeLesson(lessonId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: learningKeys.enrollments() });
    },
  });
}
