import { apiClient } from "@/lib/api/client";

export interface Enrollment {
  id: string;
  tenant_id: string;
  user_id: string;
  course_id: string;
  status: "active" | "completed";
  enrolled_at: string;
}

export interface MyEnrollmentSummary {
  id: string;
  course_id: string;
  course_title: string;
  course_slug: string;
  course_description: string | null;
  status: string;
  enrolled_at: string;
  total_lessons: number;
  completed_lessons: number;
  progress_percentage: number;
}

export interface Exercise {
  id: string;
  tenant_id: string;
  lesson_id: string;
  prompt_md: string;
  starter_code: string;
  language: string;
  created_at: string;
}

export interface ExerciseDetail extends Exercise {
  tests_code: string;
}

export interface SaveExercisePayload {
  prompt_md: string;
  starter_code: string;
  tests_code: string;
  language?: string;
}

export interface SubmitCodePayload {
  code: string;
}

export interface SubmissionQueuedResponse {
  submission_id: string;
  status: string;
}

export interface SubmissionStatusResponse {
  id: string;
  tenant_id: string;
  user_id: string;
  exercise_id: string;
  status: "queued" | "running" | "passed" | "failed" | "error";
  stdout: string | null;
  stderr: string | null;
  tests_passed: number;
  tests_total: number;
  duration_ms: number | null;
  created_at: string;
}

export interface ProgressResponse {
  id: string;
  tenant_id: string;
  user_id: string;
  lesson_id: string | null;
  exercise_id: string | null;
  completed: boolean;
  attempts: number;
  updated_at: string;
}

// ── API Methods ──

export async function enrollInCourse(courseId: string): Promise<Enrollment> {
  const res = await apiClient.post<Enrollment>(`/api/v1/learning/courses/${courseId}/enroll`);
  return res.data;
}

export async function fetchMyEnrollments(): Promise<MyEnrollmentSummary[]> {
  const res = await apiClient.get<MyEnrollmentSummary[]>("/api/v1/learning/me/enrollments");
  return res.data;
}

export async function fetchExerciseForLesson(lessonId: string): Promise<Exercise | null> {
  try {
    const res = await apiClient.get<Exercise>(`/api/v1/learning/lessons/${lessonId}/exercise`);
    return res.data;
  } catch (err: unknown) {
    if ((err as { response?: { status?: number } })?.response?.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function fetchExerciseAuthor(lessonId: string): Promise<ExerciseDetail | null> {
  try {
    const res = await apiClient.get<ExerciseDetail>(
      `/api/v1/learning/lessons/${lessonId}/exercise/author`
    );
    return res.data;
  } catch (err: unknown) {
    if ((err as { response?: { status?: number } })?.response?.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function saveExerciseAuthor(
  lessonId: string,
  payload: SaveExercisePayload
): Promise<ExerciseDetail> {
  const res = await apiClient.post<ExerciseDetail>(
    `/api/v1/learning/lessons/${lessonId}/exercise`,
    payload
  );
  return res.data;
}

export async function submitExerciseCode(
  exerciseId: string,
  payload: SubmitCodePayload
): Promise<SubmissionQueuedResponse> {
  const res = await apiClient.post<SubmissionQueuedResponse>(
    `/api/v1/learning/exercises/${exerciseId}/submit`,
    payload
  );
  return res.data;
}

export async function fetchSubmissionStatus(
  submissionId: string
): Promise<SubmissionStatusResponse> {
  const res = await apiClient.get<SubmissionStatusResponse>(
    `/api/v1/learning/submissions/${submissionId}`
  );
  return res.data;
}

export async function completeLesson(
  lessonId: string,
  completed: boolean = true
): Promise<ProgressResponse> {
  const res = await apiClient.post<ProgressResponse>(
    `/api/v1/learning/lessons/${lessonId}/complete`,
    { completed }
  );
  return res.data;
}
