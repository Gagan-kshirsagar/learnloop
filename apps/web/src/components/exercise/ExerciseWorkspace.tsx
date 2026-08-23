"use client";

import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Code2,
  Loader2,
  Play,
  RotateCcw,
  Terminal,
  XCircle,
} from "lucide-react";

import { CodeEditor } from "@/components/exercise/CodeEditor";
import { MarkdownRenderer } from "@/components/markdown/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type Exercise } from "@/lib/api/learning";
import { useSubmissionStatusQuery, useSubmitCodeMutation } from "@/lib/query/learning";

interface ExerciseWorkspaceProps {
  exercise: Exercise;
  onCompleted?: () => void;
}

export function ExerciseWorkspace({ exercise, onCompleted }: ExerciseWorkspaceProps) {
  const [code, setCode] = useState(exercise.starter_code || "def solution():\n    pass\n");
  const [activeSubmissionId, setActiveSubmissionId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const submitMutation = useSubmitCodeMutation();
  const { data: submissionStatus } = useSubmissionStatusQuery(activeSubmissionId);



  const hasNotifiedCompletion = useRef(false);

  // Trigger completion callback once on passed status
  useEffect(() => {
    if (submissionStatus?.status === "passed" && !hasNotifiedCompletion.current) {
      hasNotifiedCompletion.current = true;
      onCompleted?.();
    }
  }, [submissionStatus?.status, onCompleted]);

  const handleReset = () => {
    if (confirm("Reset editor to original starter code?")) {
      setCode(exercise.starter_code || "");
      setActiveSubmissionId(null);
      setErrorMessage(null);
    }
  };

  const handleSubmit = () => {
    if (!code.trim()) return;
    setErrorMessage(null);

    submitMutation.mutate(
      { exerciseId: exercise.id, payload: { code } },
      {
        onSuccess: (data) => {
          setActiveSubmissionId(data.submission_id);
        },
        onError: (err: unknown) => {
          const detail =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            "Failed to submit code. Please try again.";
          setErrorMessage(detail);
        },
      }
    );
  };

  const isEvaluating =
    submitMutation.isPending ||
    submissionStatus?.status === "queued" ||
    submissionStatus?.status === "running";

  return (
    <div className="grid gap-6 lg:grid-cols-12 items-start">
      {/* Left Column: Problem Prompt & Instructions */}
      <div className="lg:col-span-5 space-y-4">
        <Card className="border-subtle bg-surface shadow-xs">
          <CardHeader className="pb-3 border-b border-subtle/60 bg-surface-2/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code2 className="h-4 w-4 text-accent" />
                <CardTitle className="text-sm font-bold text-foreground">Coding Challenge</CardTitle>
              </div>
              <Badge variant="outline" className="text-[10px] font-mono uppercase text-muted">
                {exercise.language}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-5 overflow-y-auto max-h-[calc(100vh-280px)]">
            <MarkdownRenderer content={exercise.prompt_md} />
          </CardContent>
        </Card>
      </div>

      {/* Right Column: Code Editor & Execution Console */}
      <div className="lg:col-span-7 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted">
            <Terminal className="h-3.5 w-3.5 text-accent" />
            <span>Python Workspace</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            disabled={isEvaluating}
            className="h-7 text-xs text-muted hover:text-foreground gap-1"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Reset Starter</span>
          </Button>
        </div>

        {/* Code Editor */}
        <CodeEditor
          value={code}
          onChange={setCode}
          language={exercise.language}
          readOnly={isEvaluating}
          height="380px"
        />

        {/* Action Controls */}
        <div className="flex items-center justify-between gap-3 border-t border-subtle/60 pt-3">
          <div className="text-xs text-muted">
            {errorMessage && (
              <p className="text-danger flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                <span>{errorMessage}</span>
              </p>
            )}
          </div>

          <Button
            onClick={handleSubmit}
            disabled={isEvaluating || !code.trim()}
            className="font-semibold gap-2 shadow-xs shrink-0"
          >
            {isEvaluating ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Evaluating Submission…</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Run &amp; Submit</span>
              </>
            )}
          </Button>
        </div>

        {/* Execution Results Panel */}
        {submissionStatus && (
          <Card className="border-subtle bg-surface shadow-xs overflow-hidden">
            <div className="flex items-center justify-between border-b border-subtle/70 bg-surface-2/50 px-4 py-2.5">
              <div className="flex items-center gap-2">
                {submissionStatus.status === "passed" && (
                  <Badge className="bg-success-soft text-success border-success/30 gap-1 text-[11px] font-bold">
                    <CheckCircle2 className="h-3 w-3" />
                    Passed ({submissionStatus.tests_passed}/{submissionStatus.tests_total} tests)
                  </Badge>
                )}
                {submissionStatus.status === "failed" && (
                  <Badge className="bg-danger-soft text-danger border-danger/30 gap-1 text-[11px] font-bold">
                    <XCircle className="h-3 w-3" />
                    Failed ({submissionStatus.tests_passed}/{submissionStatus.tests_total} tests)
                  </Badge>
                )}
                {submissionStatus.status === "error" && (
                  <Badge className="bg-danger-soft text-danger border-danger/30 gap-1 text-[11px] font-bold">
                    <AlertCircle className="h-3 w-3" />
                    Execution Error
                  </Badge>
                )}
                {(submissionStatus.status === "queued" || submissionStatus.status === "running") && (
                  <Badge variant="secondary" className="gap-1 text-[11px] font-bold">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Sandboxed Worker Running…
                  </Badge>
                )}
              </div>

              {submissionStatus.duration_ms !== null && (
                <div className="flex items-center gap-1 text-[11px] font-mono text-muted">
                  <Clock className="h-3 w-3" />
                  <span>{submissionStatus.duration_ms}ms</span>
                </div>
              )}
            </div>

            <CardContent className="p-4 space-y-3 font-mono text-xs">
              {submissionStatus.stdout && (
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-muted">Output:</span>
                  <pre className="overflow-x-auto rounded-lg bg-surface-2 p-3 text-foreground leading-relaxed">
                    {submissionStatus.stdout}
                  </pre>
                </div>
              )}

              {submissionStatus.stderr && (
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-danger">Details:</span>
                  <pre className="overflow-x-auto rounded-lg bg-danger-soft/40 border border-danger/20 p-3 text-danger leading-relaxed">
                    {submissionStatus.stderr}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
