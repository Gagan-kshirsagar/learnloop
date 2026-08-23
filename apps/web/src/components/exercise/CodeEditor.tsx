"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  height?: string;
}

function EditorSkeleton({ height = "400px" }: { height?: string }) {
  return (
    <div
      style={{ height }}
      className="flex flex-col justify-between rounded-xl border border-subtle bg-surface-2/70 p-4 font-mono text-xs text-muted"
    >
      <div className="space-y-2">
        <Skeleton className="h-4 w-1/3 rounded-md" />
        <Skeleton className="h-4 w-2/3 rounded-md" />
        <Skeleton className="h-4 w-1/2 rounded-md" />
      </div>
      <div className="flex items-center justify-between text-[11px] text-faint">
        <span>Loading Monaco Code Engine…</span>
        <span>Python 3.12</span>
      </div>
    </div>
  );
}

const MonacoComponent = dynamic(
  () => import("@monaco-editor/react").then((mod) => mod.default),
  {
    ssr: false,
    loading: () => <EditorSkeleton />,
  }
);

export function CodeEditor({
  value,
  onChange,
  language = "python",
  readOnly = false,
  height = "420px",
}: CodeEditorProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-subtle bg-surface shadow-xs">
      <MonacoComponent
        height={height}
        language={language}
        value={value}
        onChange={(val) => onChange(val || "")}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true,
          readOnly,
          tabSize: 4,
          wordWrap: "on",
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: "all",
          cursorBlinking: "smooth",
          smoothScrolling: true,
        }}
      />
    </div>
  );
}
