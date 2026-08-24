"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  History,
  MessageSquare,
  PlusCircle,
  Send,
  Sparkles,
  Square,
  Trash2,
  User,
} from "lucide-react";

import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useTutorStream } from "@/hooks/useTutorStream";
import { fetchChatSessionDetail } from "@/lib/api/tutor";
import {
  useChatSessionsQuery,
  useDeleteChatSessionMutation,
} from "@/lib/query/tutor";

interface TutorPanelProps {
  lessonId: string;
  lessonTitle?: string;
}

export function TutorPanel({ lessonId, lessonTitle }: TutorPanelProps) {
  const [inputText, setInputText] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    messages,
    isStreaming,
    activeSessionId,
    error,
    sendMessage,
    stop,
    loadSession,
    startNewChat,
  } = useTutorStream({ lessonId });

  const sessionsQuery = useChatSessionsQuery(lessonId);
  const deleteSessionMutation = useDeleteChatSessionMutation();

  // Auto-scroll to bottom on new messages or streaming tokens
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isStreaming]);

  const handleSelectSession = async (sid: string) => {
    try {
      setLoadingSessionId(sid);
      const detail = await fetchChatSessionDetail(sid);
      loadSession(detail);
      setShowHistory(false);
    } catch {
      // Ignore error
    } finally {
      setLoadingSessionId(null);
    }
  };

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanText = inputText.trim();
    if (!cleanText || isStreaming) return;
    setInputText("");
    sendMessage(cleanText);
  };

  const handleQuickQuestion = (q: string) => {
    setInputText("");
    sendMessage(q);
  };

  const handleDeleteSession = (e: React.MouseEvent, sid: string) => {
    e.stopPropagation();
    deleteSessionMutation.mutate(sid, {
      onSuccess: () => {
        if (activeSessionId === sid) {
          startNewChat();
        }
      },
    });
  };

  return (
    <div className="flex flex-col h-[700px] border border-subtle rounded-xl bg-surface overflow-hidden shadow-xs">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-subtle bg-surface-2/50 shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h2 className="text-xs font-semibold tracking-tight text-foreground">
                AI Tutor Assistant
              </h2>
              <Badge variant="outline" className="text-[9px] bg-accent-soft text-accent border-accent/20 px-1.5 py-0">
                Streaming SSE
              </Badge>
            </div>
            <p className="text-[10px] text-muted line-clamp-1">
              Grounded in <span className="font-medium text-foreground">{lessonTitle || "this lesson"}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowHistory(!showHistory)}
            className={`h-7 px-2.5 text-xs gap-1.5 ${showHistory ? "bg-surface-3 text-foreground" : "text-muted hover:text-foreground"}`}
            title="Conversation History"
          >
            <History className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">History</span>
            {sessionsQuery.data && sessionsQuery.data.length > 0 && (
              <span className="ml-0.5 rounded-full bg-accent/15 px-1.5 py-0.2 text-[9px] font-semibold text-accent">
                {sessionsQuery.data.length}
              </span>
            )}
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={startNewChat}
            disabled={isStreaming}
            className="h-7 px-2.5 text-xs gap-1.5 font-medium border-subtle hover:bg-surface-3"
          >
            <PlusCircle className="h-3.5 w-3.5 text-accent" />
            <span>New Chat</span>
          </Button>
        </div>
      </div>

      {/* Main Content Area: Sidebar History or Chat Message Thread */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Chat History Drawer */}
        {showHistory && (
          <div className="absolute inset-0 z-10 bg-surface/95 backdrop-blur-xs p-4 flex flex-col space-y-3 overflow-y-auto border-b border-subtle sm:static sm:w-64 sm:border-r sm:border-b-0 shrink-0">
            <div className="flex items-center justify-between pb-2 border-b border-subtle">
              <span className="text-xs font-semibold text-foreground">Saved Conversations</span>
              <button
                type="button"
                onClick={() => setShowHistory(false)}
                className="text-xs text-muted hover:text-foreground sm:hidden"
              >
                Close
              </button>
            </div>

            {sessionsQuery.isLoading && (
              <p className="text-xs text-muted">Loading conversations...</p>
            )}

            {sessionsQuery.data && sessionsQuery.data.length === 0 && (
              <div className="text-center py-6 text-xs text-muted">
                <MessageSquare className="h-6 w-6 mx-auto mb-2 opacity-40" />
                No saved chats yet
              </div>
            )}

            <div className="space-y-1.5 flex-1 overflow-y-auto">
              {sessionsQuery.data?.map((s) => (
                <div
                  key={s.id}
                  onClick={() => handleSelectSession(s.id)}
                  className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer text-xs transition-colors ${
                    activeSessionId === s.id
                      ? "bg-accent-soft text-accent font-medium"
                      : "text-foreground hover:bg-surface-2"
                  } ${loadingSessionId === s.id ? "opacity-50 pointer-events-none" : ""}`}
                >
                  <div className="flex items-center gap-2 overflow-hidden mr-2">
                    <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-70" />
                    <span className="truncate">{s.title || "Conversation"}</span>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    className="opacity-0 group-hover:opacity-100 text-muted hover:text-danger p-1 rounded transition-opacity shrink-0"
                    title="Delete chat"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Message Thread */}
        <div
          className="flex-1 overflow-y-auto p-4 space-y-4"
          aria-live="polite"
        >
          {/* Welcome / Empty State */}
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4 max-w-md mx-auto">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-accent shadow-xs">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-semibold text-foreground">
                  Ask me anything about this lesson
                </h3>
                <p className="text-xs text-muted leading-relaxed">
                  I will stream answers grounded in the curriculum text and cite specific lesson chunks.
                </p>
              </div>

              <div className="w-full space-y-2 pt-2">
                <button
                  type="button"
                  onClick={() => handleQuickQuestion("Can you explain the main concept in simple terms?")}
                  className="w-full text-left rounded-lg border border-subtle bg-surface-2/60 p-2.5 text-xs text-foreground hover:border-accent/40 hover:bg-surface-2 transition-colors flex items-center justify-between group"
                >
                  <span>💡 &ldquo;Explain the main concept in simple terms&rdquo;</span>
                  <Send className="h-3 w-3 text-muted group-hover:text-accent transition-colors" />
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickQuestion("What are the key terms and definitions to know?")}
                  className="w-full text-left rounded-lg border border-subtle bg-surface-2/60 p-2.5 text-xs text-foreground hover:border-accent/40 hover:bg-surface-2 transition-colors flex items-center justify-between group"
                >
                  <span>📖 &ldquo;What are the key terms and definitions?&rdquo;</span>
                  <Send className="h-3 w-3 text-muted group-hover:text-accent transition-colors" />
                </button>
              </div>
            </div>
          )}

          {/* Conversation Bubble List */}
          {messages.map((msg, idx) => {
            const isUser = msg.role === "user";
            const isLatest = idx === messages.length - 1;

            return (
              <div
                key={msg.id || idx}
                className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
              >
                {/* Tutor Avatar */}
                {!isUser && (
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/15 text-accent shrink-0 mt-0.5">
                    <Sparkles className="h-3.5 w-3.5" />
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-3.5 space-y-2 text-xs leading-relaxed ${
                    isUser
                      ? "bg-accent text-accent-foreground font-medium rounded-tr-xs"
                      : "bg-surface-2 border border-subtle text-foreground rounded-tl-xs shadow-xs"
                  }`}
                >
                  {isUser ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <div>
                      {msg.content ? (
                        <div className="prose prose-xs dark:prose-invert max-w-none">
                          <MarkdownRenderer content={msg.content} />
                          {/* Live Streaming Animated Caret */}
                          {isStreaming && isLatest && (
                            <span className="inline-block w-1.5 h-3.5 ml-1 bg-accent animate-pulse align-middle" />
                          )}
                        </div>
                      ) : isStreaming && isLatest ? (
                        <div className="flex items-center gap-1.5 text-muted py-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-accent animate-bounce" />
                          <span className="h-1.5 w-1.5 rounded-full bg-accent animate-bounce [animation-delay:0.2s]" />
                          <span className="h-1.5 w-1.5 rounded-full bg-accent animate-bounce [animation-delay:0.4s]" />
                          <span className="text-[11px] text-muted ml-1 font-mono">Thinking...</span>
                        </div>
                      ) : (
                        <span className="text-muted italic">No response</span>
                      )}

                      {/* Citations Container */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-subtle/80 space-y-1.5">
                          <div className="flex items-center gap-1 text-[10px] font-semibold text-muted uppercase tracking-wider">
                            <BookOpen className="h-3 w-3 text-accent" />
                            <span>Referenced Lesson Sources ({msg.citations.length})</span>
                          </div>
                          <div className="grid gap-1.5 sm:grid-cols-2">
                            {msg.citations.map((c) => (
                              <div
                                key={`${c.lesson_id}-${c.ordinal}`}
                                className="rounded-md border border-subtle bg-surface p-2 space-y-1"
                              >
                                <div className="flex items-center justify-between text-[10px]">
                                  <span className="font-semibold text-foreground">
                                    Chunk #{c.ordinal + 1}
                                  </span>
                                  <span className="font-mono text-muted bg-surface-2 px-1 py-0.2 rounded text-[9px]">
                                    {(c.score * 100).toFixed(0)}%
                                  </span>
                                </div>
                                <p className="text-[10px] text-muted line-clamp-2 font-mono">
                                  &ldquo;{c.snippet}&rdquo;
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* User Avatar */}
                {isUser && (
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-surface-3 text-muted shrink-0 mt-0.5">
                    <User className="h-3.5 w-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {/* Error Banner */}
          {error && (
            <div className="rounded-xl border border-danger/30 bg-danger-soft p-3 flex items-start gap-2.5 text-xs text-danger">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Stream Error</p>
                <p className="text-[11px] text-muted">{error}</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Question Input Footer */}
      <div className="p-3 border-t border-subtle bg-surface shrink-0">
        <form onSubmit={handleSend} className="space-y-2">
          <div className="relative flex items-center">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question or follow-up... (Enter to send, Shift+Enter for newline)"
              rows={2}
              disabled={isStreaming}
              className="w-full resize-none rounded-xl border border-subtle bg-surface-2 p-3 pr-20 text-xs text-foreground placeholder:text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent disabled:opacity-60"
            />

            <div className="absolute right-2.5 bottom-2.5 flex items-center gap-1.5">
              {isStreaming ? (
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={stop}
                  className="h-7 px-2.5 text-xs gap-1 font-semibold"
                  title="Stop generating"
                >
                  <Square className="h-3 w-3 fill-current" />
                  <span>Stop</span>
                </Button>
              ) : (
                <Button
                  type="submit"
                  size="sm"
                  disabled={!inputText.trim()}
                  className="h-7 px-3 text-xs gap-1 font-semibold"
                >
                  <Send className="h-3 w-3" />
                  <span>Ask</span>
                </Button>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-[10px] text-faint px-1">
            <span>AI answers are grounded in lesson context with multi-turn memory</span>
            {activeSessionId && (
              <span className="font-mono text-muted">Session active</span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
