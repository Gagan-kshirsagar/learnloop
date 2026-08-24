import { apiClient } from "@/lib/api/client";

export interface Citation {
  lesson_id: string;
  ordinal: number;
  snippet: string;
  score: number;
}

export interface AskQuestionPayload {
  question: string;
  lesson_id?: string;
}

export interface AskQuestionResponse {
  answer: string;
  citations: Citation[];
  used_context: boolean;
}

export interface LessonIngestResponse {
  lesson_id: string;
  chunks_created: number;
  total_tokens: number;
}

export async function askTutorQuestion(
  payload: AskQuestionPayload
): Promise<AskQuestionResponse> {
  const res = await apiClient.post<AskQuestionResponse>("/api/v1/tutor/ask", payload);
  return res.data;
}

export async function ingestLessonContent(
  lessonId: string
): Promise<LessonIngestResponse> {
  const res = await apiClient.post<LessonIngestResponse>(
    `/api/v1/tutor/lessons/${lessonId}/ingest`
  );
  return res.data;
}
