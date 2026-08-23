"use client";

import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

export function TutorPreview() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98, y: 12 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="relative w-full max-w-lg"
    >
      <div className="overflow-hidden rounded-2xl border border-subtle bg-surface shadow-xl">
        {/* Title bar */}
        <div className="flex items-center justify-between border-b border-subtle bg-surface-2/70 px-4 py-2.5">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5" aria-hidden="true">
              <span className="h-2.5 w-2.5 rounded-full bg-danger/60" />
              <span className="h-2.5 w-2.5 rounded-full bg-warning/60" />
              <span className="h-2.5 w-2.5 rounded-full bg-success/60" />
            </div>
            <span className="text-xs font-medium text-muted">binary_search.py</span>
          </div>
          <span className="text-[10px] font-medium text-muted">Python 3.12</span>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 sm:grid-cols-[1.1fr,0.9fr]">
          {/* Code */}
          <div className="border-b border-subtle p-4 font-mono text-xs leading-relaxed sm:border-b-0 sm:border-r">
            <div className="space-y-1">
              <div><span className="text-accent">def</span> <span className="text-foreground font-semibold">binary_search</span>(arr, target):</div>
              <div className="text-muted">    left, right = <span className="text-accent-2">0</span>, <span className="text-accent">len</span>(arr) - <span className="text-accent-2">1</span></div>
              <div>    <span className="text-accent">while</span> left &lt;= right:</div>
              <div className="text-muted">        mid = (left + right) // <span className="text-accent-2">2</span></div>
              <div>        <span className="text-accent">if</span> arr[mid] == target:</div>
              <div>            <span className="text-accent">return</span> mid</div>
              <div>        <span className="text-accent">elif</span> arr[mid] &lt; target:</div>
              <div className="text-muted">            left = mid + <span className="text-accent-2">1</span></div>
              <div>        <span className="text-accent">else</span>: right = mid - <span className="text-accent-2">1</span></div>
              <div>    <span className="text-accent">return</span> <span className="text-accent-2">-1</span></div>
            </div>
          </div>

          {/* Socratic Dialogue */}
          <div className="flex flex-col justify-between bg-surface-2/30 p-3.5">
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 pb-1 text-[11px] font-semibold text-foreground">
                <span className="flex h-4 w-4 items-center justify-center rounded bg-accent text-[8px] font-bold text-accent-foreground">
                  AI
                </span>
                Socratic Tutor
              </div>

              <div className="rounded-lg bg-accent-soft p-2.5 text-[11px] leading-snug text-foreground">
                What happens when <code className="rounded bg-surface px-1 font-mono text-[10px]">left == right</code>? Why is that comparison important?
              </div>

              <div className="ml-2 rounded-lg border border-subtle bg-surface p-2 text-[11px] leading-snug text-muted">
                It checks the final remaining element before exiting.
              </div>

              <div className="rounded-lg bg-accent-soft p-2.5 text-[11px] leading-snug text-foreground">
                Exactly! That guarantees O(log n) worst-case time without missing keys.
              </div>
            </div>
          </div>
        </div>

        {/* Footer Bar */}
        <div className="flex items-center justify-between border-t border-subtle bg-surface-2/60 px-4 py-2 text-[11px]">
          <div className="flex items-center gap-1.5 text-success font-medium">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>3/3 Tests Passed</span>
          </div>
          <span className="text-faint text-[10px]">Safe Sandbox Environment</span>
        </div>
      </div>
    </motion.div>
  );
}
