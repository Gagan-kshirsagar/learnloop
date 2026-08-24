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

export interface ToolStep {
  type: "tool_call" | "tool_result";
  tool: string;
  summary?: string;
  args?: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[] | null;
  tool_steps?: ToolStep[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  lesson_id: string | null;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail {
  session: ChatSession;
  messages: ChatMessage[];
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

export async function fetchChatSessions(
  lessonId?: string
): Promise<ChatSession[]> {
  const url = lessonId
    ? `/api/v1/tutor/sessions?lesson_id=${encodeURIComponent(lessonId)}`
    : "/api/v1/tutor/sessions";
  const res = await apiClient.get<ChatSession[]>(url);
  return res.data;
}

export async function fetchChatSessionDetail(
  sessionId: string
): Promise<ChatSessionDetail> {
  const res = await apiClient.get<ChatSessionDetail>(`/api/v1/tutor/sessions/${sessionId}`);
  return res.data;
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/api/v1/tutor/sessions/${sessionId}`);
}

export async function ingestLessonContent(
  lessonId: string
): Promise<LessonIngestResponse> {
  const res = await apiClient.post<LessonIngestResponse>(
    `/api/v1/tutor/lessons/${lessonId}/ingest`
  );
  return res.data;
}
