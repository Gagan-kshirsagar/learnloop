"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export function DemoCard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="rounded-xl border border-subtle bg-surface p-6 shadow-sm"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-soft text-accent">
          <Sparkles className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Slice-0 Architecture Online
          </h2>
          <p className="text-sm text-muted">
            Design tokens, motion, state providers, and modular monolith API verified.
          </p>
        </div>
      </div>
    </motion.div>
  );
}
