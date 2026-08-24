import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/authStore";
import type { ChatMessage, ChatSessionDetail, Citation } from "@/lib/api/tutor";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface UseTutorStreamOptions {
  lessonId?: string;
  initialSessionId?: string | null;
}

export function useTutorStream({ lessonId, initialSessionId = null }: UseTutorStreamOptions = {}) {
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(initialSessionId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Clean up streaming on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const loadSession = useCallback((detail: ChatSessionDetail) => {
    setActiveSessionId(detail.session.id);
    setMessages(detail.messages);
    setError(null);
  }, []);

  const startNewChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setActiveSessionId(null);
    setMessages([]);
    setIsStreaming(false);
    setError(null);
  }, []);

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback(
    async (questionText: string) => {
      const trimmed = questionText.trim();
      if (!trimmed || isStreaming) return;

      setError(null);
      setIsStreaming(true);

      // Create placeholder messages
      const userMsgId = `temp-user-${Date.now()}`;
      const asstMsgId = `temp-asst-${Date.now()}`;

      const userMessage: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      };

      const assistantMessage: ChatMessage = {
        id: asstMsgId,
        role: "assistant",
        content: "",
        citations: [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const token = useAuthStore.getState().accessToken;
        const res = await fetch(`${API_BASE_URL}/api/v1/tutor/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            question: trimmed,
            session_id: activeSessionId ?? undefined,
            lesson_id: lessonId ?? undefined,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`Stream request failed with HTTP ${res.status}`);
        }

        if (!res.body) {
          throw new Error("ReadableStream not supported in response");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const blocks = buffer.split("\n\n");
          buffer = blocks.pop() ?? "";

          for (const block of blocks) {
            if (!block.trim()) continue;

            let eventName = "message";
            let dataStr = "";

            for (const line of block.split("\n")) {
              if (line.startsWith("event: ")) {
                eventName = line.slice(7).trim();
              } else if (line.startsWith("data: ")) {
                dataStr = line.slice(6).trim();
              }
            }

            if (!dataStr) continue;

            try {
              const parsed = JSON.parse(dataStr);

              if (eventName === "token") {
                const tokenText = parsed.text ?? "";
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === asstMsgId
                      ? { ...msg, content: msg.content + tokenText }
                      : msg
                  )
                );
              } else if (eventName === "citations") {
                const citationsList: Citation[] = parsed.citations ?? [];
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === asstMsgId
                      ? { ...msg, citations: citationsList }
                      : msg
                  )
                );
              } else if (eventName === "done") {
                const finalSessionId: string = parsed.session_id;
                const finalMessageId: string = parsed.message_id;
                if (finalSessionId) {
                  setActiveSessionId(finalSessionId);
                }
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === asstMsgId
                      ? { ...msg, id: finalMessageId || msg.id }
                      : msg
                  )
                );
                queryClient.invalidateQueries({ queryKey: ["tutor-sessions"] });
              } else if (eventName === "error") {
                setError(parsed.message || "An error occurred during generation");
              }
            } catch {
              // Ignore non-JSON malformed SSE chunk
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error)?.name !== "AbortError") {
          const msg = (err as Error)?.message || "Failed to stream tutor response";
          setError(msg);
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [activeSessionId, isStreaming, lessonId, queryClient]
  );

  return {
    messages,
    isStreaming,
    activeSessionId,
    error,
    sendMessage,
    stop,
    loadSession,
    startNewChat,
  };
}
