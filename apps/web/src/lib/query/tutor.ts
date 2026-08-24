import { useMutation } from "@tanstack/react-query";

import {
  askTutorQuestion,
  ingestLessonContent,
  type AskQuestionPayload,
  type AskQuestionResponse,
  type LessonIngestResponse,
} from "@/lib/api/tutor";

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
