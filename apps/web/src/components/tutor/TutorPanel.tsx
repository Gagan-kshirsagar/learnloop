"use client";

import { useState } from "react";
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  HelpCircle,
  Loader2,
  Send,
  Sparkles,
} from "lucide-react";

import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { type AskQuestionResponse } from "@/lib/api/tutor";
import { useAskTutorMutation } from "@/lib/query/tutor";

interface TutorPanelProps {
  lessonId: string;
  lessonTitle?: string;
}

export function TutorPanel({ lessonId, lessonTitle }: TutorPanelProps) {
  const [question, setQuestion] = useState("");
  const [lastResponse, setLastResponse] = useState<AskQuestionResponse | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);

  const askMutation = useAskTutorMutation();

  const handleAsk = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanQ = question.trim();
    if (!cleanQ || askMutation.isPending) return;

    setLastQuestion(cleanQ);
    askMutation.mutate(
      { question: cleanQ, lesson_id: lessonId },
      {
        onSuccess: (data) => {
          setLastResponse(data);
        },
      }
    );
  };

  const handleQuickQuestion = (q: string) => {
    setQuestion(q);
    setLastQuestion(q);
    askMutation.mutate(
      { question: q, lesson_id: lessonId },
      {
        onSuccess: (data) => {
          setLastResponse(data);
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent" />
            <h2 className="text-sm font-semibold tracking-tight text-foreground">
              AI Tutor Assistant
            </h2>
            <Badge variant="outline" className="text-[10px] bg-accent-soft text-accent border-accent/20">
              Grounded RAG
            </Badge>
          </div>
          <p className="text-xs text-muted mt-0.5">
            Ask questions grounded strictly in{" "}
            <span className="font-medium text-foreground">{lessonTitle || "this lesson"}</span>.
          </p>
        </div>
      </div>

      {/* Question Input Form */}
      <Card className="border-subtle bg-surface shadow-xs">
        <CardContent className="p-4">
          <form onSubmit={handleAsk} className="space-y-3">
            <div className="relative">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleAsk();
                  }
                }}
                placeholder="Ask anything about the concepts, formulas, or code in this lesson... (Press Enter to ask)"
                rows={3}
                className="w-full resize-none rounded-lg border border-subtle bg-surface-2 p-3 text-xs text-foreground placeholder:text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-faint hidden sm:inline">
                Answers cite lesson chunks and reject out-of-scope queries
              </span>
              <Button
                type="submit"
                size="sm"
                disabled={!question.trim() || askMutation.isPending}
                className="h-8 gap-1.5 px-4 text-xs font-semibold"
              >
                {askMutation.isPending ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Searching & Thinking...</span>
                  </>
                ) : (
                  <>
                    <Send className="h-3.5 w-3.5" />
                    <span>Ask Tutor</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Loading State Skeleton */}
      {askMutation.isPending && (
        <Card className="border-subtle bg-surface p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-24 rounded" />
            <Skeleton className="h-4 w-16 rounded" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full rounded" />
            <Skeleton className="h-4 w-5/6 rounded" />
            <Skeleton className="h-4 w-4/6 rounded" />
          </div>
          <div className="pt-2">
            <Skeleton className="h-16 w-full rounded-lg" />
          </div>
        </Card>
      )}

      {/* Error State */}
      {askMutation.isError && (
        <div className="rounded-xl border border-danger/30 bg-danger-soft p-4 flex items-start gap-3">
          <AlertCircle className="h-4 w-4 text-danger shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs">
            <p className="font-semibold text-danger">Failed to get tutor answer</p>
            <p className="text-muted">
              {askMutation.error?.message || "An unexpected error occurred while communicating with the AI tutor."}
            </p>
            <button
              type="button"
              onClick={() => handleAsk()}
              className="text-xs font-semibold text-danger underline hover:text-danger/80 pt-1"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Answer & Citations Success State */}
      {lastResponse && !askMutation.isPending && (
        <div className="space-y-4">
          {/* Question Recap */}
          {lastQuestion && (
            <div className="flex items-center gap-2 text-xs text-muted border-l-2 border-accent/40 pl-3 py-1">
              <HelpCircle className="h-3.5 w-3.5 text-accent shrink-0" />
              <span className="font-medium text-foreground italic">&ldquo;{lastQuestion}&rdquo;</span>
            </div>
          )}

          {/* Grounded Answer Card */}
          <Card className="border-subtle bg-surface shadow-xs">
            <CardContent className="p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-subtle/60 pb-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/10 text-accent">
                    <Sparkles className="h-3.5 w-3.5" />
                  </div>
                  <span className="text-xs font-bold text-foreground">Tutor Response</span>
                </div>

                {lastResponse.used_context ? (
                  <Badge variant="outline" className="border-success/30 bg-success-soft text-success text-[10px] gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    Grounded in Lesson
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-[10px] text-muted">
                    Out of Scope / Not Covered
                  </Badge>
                )}
              </div>

              {/* Answer Content */}
              <div className="text-xs leading-relaxed text-foreground">
                <MarkdownRenderer content={lastResponse.answer} />
              </div>

              {/* Citations List */}
              {lastResponse.citations.length > 0 && (
                <div className="border-t border-subtle/60 pt-4 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-muted">
                    <BookOpen className="h-3.5 w-3.5 text-accent" />
                    <span>Referenced Lesson Sources ({lastResponse.citations.length})</span>
                  </div>

                  <div className="grid gap-2 sm:grid-cols-2">
                    {lastResponse.citations.map((c) => (
                      <div
                        key={`${c.lesson_id}-${c.ordinal}`}
                        className="rounded-lg border border-subtle bg-surface-2/60 p-3 space-y-1.5"
                      >
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-foreground">
                            Lesson Chunk #{c.ordinal + 1}
                          </span>
                          <span className="text-[10px] font-mono text-muted bg-surface px-1.5 py-0.5 rounded border border-subtle">
                            {(c.score * 100).toFixed(0)}% match
                          </span>
                        </div>
                        <p className="text-[11px] text-muted line-clamp-3 leading-relaxed font-mono">
                          &ldquo;{c.snippet}&rdquo;
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State Tips */}
      {!lastResponse && !askMutation.isPending && !askMutation.isError && (
        <div className="rounded-xl border border-dashed border-subtle p-6 text-center space-y-3">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-surface-2 text-muted">
            <HelpCircle className="h-5 w-5" />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <p className="text-xs font-semibold text-foreground">Ask anything about this lesson</p>
            <p className="text-[11px] text-muted">
              The AI tutor searches through this lesson&apos;s concepts and answers with cited context.
            </p>
          </div>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => handleQuickQuestion("Can you summarize the core concept in this lesson?")}
              className="rounded-full border border-subtle bg-surface px-3 py-1 text-[11px] text-muted hover:text-foreground hover:bg-surface-2 transition-colors"
            >
              💡 &ldquo;Summarize the core concept&rdquo;
            </button>
            <button
              type="button"
              onClick={() => handleQuickQuestion("Can you explain this with a short code example?")}
              className="rounded-full border border-subtle bg-surface px-3 py-1 text-[11px] text-muted hover:text-foreground hover:bg-surface-2 transition-colors"
            >
              💻 &ldquo;Explain with a code example&rdquo;
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
