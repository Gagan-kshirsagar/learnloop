import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  askTutorQuestion,
  deleteChatSession,
  fetchChatSessionDetail,
  fetchChatSessions,
  ingestLessonContent,
  type AskQuestionPayload,
  type AskQuestionResponse,
  type ChatSession,
  type ChatSessionDetail,
  type LessonIngestResponse,
} from "@/lib/api/tutor";

export function useChatSessionsQuery(lessonId?: string) {
  return useQuery<ChatSession[], Error>({
    queryKey: ["tutor-sessions", lessonId ?? "all"],
    queryFn: () => fetchChatSessions(lessonId),
    staleTime: 30 * 1000,
  });
}

export function useChatSessionDetailQuery(sessionId?: string | null) {
  return useQuery<ChatSessionDetail, Error>({
    queryKey: ["tutor-session-detail", sessionId],
    queryFn: () => fetchChatSessionDetail(sessionId!),
    enabled: Boolean(sessionId),
    staleTime: 60 * 1000,
  });
}

export function useDeleteChatSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (sessionId) => deleteChatSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tutor-sessions"] });
    },
  });
}

export function useAskTutorMutation() {
  return useMutation<AskQuestionResponse, Error, AskQuestionPayload>({
    mutationFn: (payload) => askTutorQuestion(payload),
  });
}

export function useIngestLessonMutation() {
  return useMutation<LessonIngestResponse, Error, string>({
    mutationFn: (lessonId) => ingestLessonContent(lessonId),
  });
}
