"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Clock,
  Code2,
  HelpCircle,
  History,
  KeyRound,
  Lightbulb,
  MessageSquare,
  PlusCircle,
  Send,
  ShieldAlert,
  Sparkles,
  Square,
  Terminal,
  Trash2,
  User,
} from "lucide-react";

import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useTutorStream } from "@/hooks/useTutorStream";
import type { ToolStep } from "@/lib/api/tutor";
import { fetchChatSessionDetail } from "@/lib/api/tutor";
import {
  useChatSessionsQuery,
  useDeleteChatSessionMutation,
} from "@/lib/query/tutor";

interface TutorPanelProps {
  lessonId: string;
  lessonTitle?: string;
  exerciseId?: string;
}

function ThinkingTrail({
  steps,
  isLive,
}: {
  steps: ToolStep[];
  isLive: boolean;
}) {
  const [userToggled, setUserToggled] = useState<boolean | null>(null);
  const isExpanded = userToggled ?? isLive;

  if (!steps || steps.length === 0) return null;

  const getToolIcon = (tool: string) => {
    switch (tool) {
      case "read_submission":
        return <Code2 className="h-3 w-3 text-accent" />;
      case "retrieve_lesson":
        return <BookOpen className="h-3 w-3 text-brand" />;
      case "check_code":
        return <Terminal className="h-3 w-3 text-emerald-500" />;
      default:
        return <Sparkles className="h-3 w-3 text-muted" />;
    }
  };

  const getToolLabel = (step: ToolStep) => {
    if (step.summary) return step.summary;
    switch (step.tool) {
      case "read_submission":
        return "Inspecting learner code submission...";
      case "retrieve_lesson":
        return "Searching curriculum context chunks...";
      case "check_code":
        return "Running code tests in sandbox...";
      case "get_progress":
        return "Checking attempt history...";
      default:
        return `Invoking tool: ${step.tool}`;
    }
  };

  return (
    <div className="mb-2.5 rounded-lg border border-subtle/80 bg-surface/50 text-[11px] overflow-hidden">
      <button
        type="button"
        onClick={() => setUserToggled(!isExpanded)}
        className="w-full flex items-center justify-between px-2.5 py-1.5 bg-surface-2/40 hover:bg-surface-2 text-muted hover:text-foreground transition-colors font-mono"
      >
        <div className="flex items-center gap-1.5">
          <Sparkles className="h-3 w-3 text-accent" />
          <span>Agent Reasoning Trail ({steps.length})</span>
          {isLive && (
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-ping ml-1" />
          )}
        </div>
        {isExpanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
      </button>

      {isExpanded && (
        <div className="p-2 space-y-1.5 divide-y divide-subtle/40">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-2 pt-1 first:pt-0 ${
                step.type === "tool_call" ? "opacity-80" : "font-medium"
              }`}
            >
              <div className="mt-0.5 shrink-0">{getToolIcon(step.tool)}</div>
              <div className="flex-1 leading-snug break-words">
                <span>{getToolLabel(step)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function TutorPanel({ lessonId, lessonTitle, exerciseId }: TutorPanelProps) {
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
    limitInfo,
    clearLimit,
    sendMessage,
    stop,
    loadSession,
    startNewChat,
  } = useTutorStream({ lessonId, exerciseId });

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
      <div className="flex items-center justify-between px-4 py-3 border-b border-subtle bg-surface-2/70">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent-soft text-accent">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h2 className="text-sm font-semibold text-foreground">Socratic AI Tutor</h2>
              <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                LangGraph ReAct
              </Badge>
            </div>
            {lessonTitle && (
              <p className="text-xs text-muted truncate max-w-[200px] sm:max-w-xs">
                {lessonTitle}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={startNewChat}
            disabled={isStreaming}
            className="h-8 text-xs gap-1 text-muted hover:text-foreground"
            title="New Chat"
          >
            <PlusCircle className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">New Chat</span>
          </Button>

          <Button
            variant={showHistory ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setShowHistory(!showHistory)}
            className="h-8 text-xs gap-1 text-muted hover:text-foreground"
            title="Conversation History"
          >
            <History className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">History</span>
          </Button>
        </div>
      </div>

      {/* Main Workspace Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Chat Sessions History Drawer */}
        {showHistory && (
          <div className="absolute inset-y-0 right-0 w-64 bg-surface border-l border-subtle z-20 shadow-lg p-3 flex flex-col animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between pb-2 border-b border-subtle mb-2">
              <span className="text-xs font-semibold text-foreground">Past Conversations</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 text-muted"
                onClick={() => setShowHistory(false)}
              >
                &times;
              </Button>
            </div>

            {sessionsQuery.isLoading && (
              <div className="p-4 text-center text-xs text-muted">Loading history...</div>
            )}

            {!sessionsQuery.isLoading && (sessionsQuery.data?.length ?? 0) === 0 && (
              <div className="p-4 text-center text-xs text-muted">No saved chats yet.</div>
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
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-accent shadow-xs border border-accent/20">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-sm font-bold tracking-tight text-foreground">
                  Ask me anything about this lesson
                </h3>
                <p className="text-xs text-muted leading-relaxed">
                  I will reason with tool observations and provide progressive Socratic hints to guide your solution.
                </p>
              </div>

              <div className="w-full space-y-2 pt-2">
                <button
                  type="button"
                  onClick={() => handleQuickQuestion("Why is my code failing? Please guide me.")}
                  className="w-full text-left rounded-xl border border-subtle bg-surface-2/60 p-3 text-xs text-foreground hover:border-accent/40 hover:bg-surface-2 active:scale-[0.99] transition-all flex items-center justify-between group shadow-xs"
                >
                  <span className="flex items-center gap-2">
                    <Code2 className="h-3.5 w-3.5 text-accent" />
                    &ldquo;Why is my code failing? Please guide me&rdquo;
                  </span>
                  <Send className="h-3 w-3 text-muted group-hover:text-accent transition-colors" />
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickQuestion("Can you explain the main concept in simple terms?")}
                  className="w-full text-left rounded-xl border border-subtle bg-surface-2/60 p-3 text-xs text-foreground hover:border-accent/40 hover:bg-surface-2 active:scale-[0.99] transition-all flex items-center justify-between group shadow-xs"
                >
                  <span className="flex items-center gap-2">
                    <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
                    &ldquo;Explain the main concept in simple terms&rdquo;
                  </span>
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
                className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} animate-in fade-in duration-150`}
              >
                {/* Tutor Avatar */}
                {!isUser && (
                  <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-accent-soft text-accent border border-accent/20 shrink-0 mt-0.5 shadow-xs">
                    <Sparkles className="h-3.5 w-3.5" />
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 space-y-2 text-xs leading-relaxed ${
                    isUser
                      ? "bg-accent text-accent-foreground font-medium rounded-tr-xs shadow-xs"
                      : "bg-surface-2 border border-subtle text-foreground rounded-tl-xs shadow-xs"
                  }`}
                >
                  {isUser ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <div>
                      {/* Thinking Trail (Tool Steps) */}
                      {msg.tool_steps && msg.tool_steps.length > 0 && (
                        <ThinkingTrail
                          steps={msg.tool_steps}
                          isLive={isStreaming && isLatest}
                        />
                      )}

                      {msg.content ? (
                        <div className="max-w-none text-xs">
                          <MarkdownRenderer content={msg.content} compact />
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
                          <span className="text-[11px] text-muted ml-1 font-mono">Agent reasoning...</span>
                        </div>
                      ) : (
                        <span className="text-muted italic">No response</span>
                      )}

                      {/* Citations Container */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-subtle/80 space-y-1.5">
                          <div className="flex items-center gap-1 text-[11px] font-medium text-muted">
                            <BookOpen className="h-3 w-3" />
                            <span>Referenced Lesson Sources ({msg.citations.length})</span>
                          </div>
                          <div className="grid gap-1.5">
                            {msg.citations.map((c, i) => (
                              <div
                                key={i}
                                className="rounded-md border border-subtle/70 bg-surface/70 p-2 text-[11px] space-y-1"
                              >
                                <div className="flex items-center justify-between text-muted">
                                  <span className="font-medium text-foreground">
                                    Chunk #{c.ordinal + 1}
                                  </span>
                                  <span className="font-mono text-[10px]">
                                    {Math.round(c.score * 100)}% relevance
                                  </span>
                                </div>
                                <div className="text-muted/90 line-clamp-3 text-[11px] font-sans">
                                  <MarkdownRenderer
                                    content={
                                      c.snippet.replace(/^#{1,6}\s+[^\n]+\n*/g, "").trim() ||
                                      c.snippet
                                    }
                                    className="text-[11px] text-muted leading-relaxed"
                                    compact
                                  />
                                </div>
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
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-surface-2 border border-subtle text-foreground shrink-0 mt-0.5">
                    <User className="h-3.5 w-3.5 opacity-70" />
                  </div>
                )}
              </div>
            );
          })}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Limit State Banner */}
      {limitInfo && (
        <div
          className={`mx-4 mb-2 p-2.5 rounded-lg border text-xs flex items-center justify-between gap-2 animate-in fade-in duration-200 ${
            limitInfo.reason === "user_rate_limit"
              ? "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400"
              : limitInfo.reason === "provider_busy"
              ? "border-accent/30 bg-accent-soft text-accent"
              : "border-subtle bg-surface-2 text-foreground"
          }`}
        >
          <div className="flex items-center gap-2">
            {limitInfo.reason === "user_rate_limit" ? (
              <Clock className="h-4 w-4 shrink-0 text-amber-500" />
            ) : limitInfo.reason === "provider_busy" ? (
              <Sparkles className="h-4 w-4 shrink-0 text-accent" />
            ) : (
              <ShieldAlert className="h-4 w-4 shrink-0 text-brand" />
            )}
            <span className="leading-snug">{limitInfo.message}</span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {limitInfo.reason === "provider_busy" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  clearLimit();
                  handleQuickQuestion(inputText || "Can you explain the main concept?");
                }}
                className="h-6 text-xs px-2 border-accent/40 hover:bg-accent/10"
              >
                Retry
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={clearLimit}
              className="h-6 text-xs px-2 text-muted hover:text-foreground"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && !limitInfo && (
        <div className="mx-4 mb-2 p-2.5 rounded-lg border border-danger/40 bg-danger-soft text-danger text-xs flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleQuickQuestion(inputText || "Can you explain the main concept?")}
            className="h-6 text-xs px-2 text-danger hover:bg-danger/10"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Socratic Pedagogy Action Chips */}
      {messages.length > 0 && !isStreaming && (
        <div className="px-4 py-1.5 bg-surface-2/30 border-t border-subtle flex items-center gap-1.5 overflow-x-auto text-[11px]">
          <span className="text-muted shrink-0 flex items-center gap-1">
            <HelpCircle className="h-3 w-3" />
            <span>Pedagogy:</span>
          </span>
          <button
            type="button"
            onClick={() => handleQuickQuestion("I'm still stuck on this exercise. Can you give me a more specific hint?")}
            className="px-2 py-0.5 rounded-md border border-subtle bg-surface hover:bg-surface-2 text-foreground transition-colors shrink-0 flex items-center gap-1"
          >
            <Lightbulb className="h-2.5 w-2.5 text-amber-500" />
            <span>Still stuck (Hint +)</span>
          </button>
          <button
            type="button"
            onClick={() => handleQuickQuestion("Please reveal the worked solution and explain each step in detail.")}
            className="px-2 py-0.5 rounded-md border border-subtle bg-surface hover:bg-surface-2 text-foreground transition-colors shrink-0 flex items-center gap-1"
          >
            <KeyRound className="h-2.5 w-2.5 text-accent" />
            <span>Reveal Solution</span>
          </button>
        </div>
      )}

      {/* Input Composer */}
      <form
        onSubmit={handleSend}
        className="p-3 border-t border-subtle bg-surface flex items-center gap-2"
      >
        <div className="relative flex-1">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={
              isStreaming
                ? "Tutor is responding..."
                : limitInfo?.reason === "tenant_daily_budget" || limitInfo?.reason === "global_daily_budget"
                ? "Daily demo limit reached — resumes tomorrow."
                : limitInfo?.reason === "user_rate_limit"
                ? "Message rate limit reached — please wait a moment."
                : "Ask a question or request guidance (Enter to send)..."
            }
            disabled={isStreaming}
            className="w-full resize-none rounded-xl border border-subtle bg-surface-2 px-3.5 py-2.5 text-xs text-foreground placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent disabled:opacity-50 transition-colors"
          />
        </div>

        {isStreaming ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={stop}
            className="h-9 px-3 gap-1.5 text-xs text-danger border-danger/30 hover:bg-danger-soft"
          >
            <Square className="h-3 w-3 fill-current" />
            <span>Stop</span>
          </Button>
        ) : (
          <Button
            type="submit"
            size="sm"
            disabled={!inputText.trim()}
            className="h-9 w-9 p-0 rounded-xl bg-accent text-accent-foreground hover:bg-accent/90 disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </Button>
        )}
      </form>
    </div>
  );
}
