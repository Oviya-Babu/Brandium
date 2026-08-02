"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Check, Loader2 } from "lucide-react";
import type { PipelineStage, WorkUnitProgress } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const STAGES: { key: PipelineStage; label: string }[] = [
  { key: "queued", label: "Queued" },
  { key: "applicability", label: "Applicability" },
  { key: "planning", label: "Planning" },
  { key: "worker_execution", label: "Worker Execution" },
  { key: "evidence_fusion", label: "Evidence Fusion" },
  { key: "completeness_verification", label: "Completeness" },
  { key: "decision_engine", label: "Decision Engine" },
  { key: "recommendation_generation", label: "Recommendations" },
  { key: "report_ready", label: "Report" },
];

const WORKER_LABEL: Record<string, string> = {
  text_worker: "Text Worker",
  image_worker: "Image Worker",
};

const WORK_UNIT_STATE_LABEL: Record<WorkUnitProgress["state"], string> = {
  assigned: "Assigned",
  executing: "Executing",
  succeeded: "Succeeded",
  failed: "Failed",
  timed_out: "Timed out",
};

/**
 * Phase 4 §11's real-time execution view, rendered as the horizontal
 * pipeline the demo objective explicitly asks for: "watch the runtime
 * execute... observe the planner creating work... observe worker
 * execution... observe evidence generation/fusion... observe the
 * Decision Engine."
 */
export function PipelineTrack({ stage, workUnits }: { stage: PipelineStage; workUnits: WorkUnitProgress[] }) {
  const failed = stage === "failed";
  const currentIndex = STAGES.findIndex((s) => s.key === stage);

  return (
    <div className="card p-6">
      <div className="flex items-center gap-1 overflow-x-auto pb-2">
        {STAGES.map((s, i) => {
          const done = !failed && (currentIndex > i || stage === "complete");
          const active = !failed && currentIndex === i && stage !== "complete";
          return (
            <div key={s.key} className="flex flex-1 items-center">
              <div className="flex flex-col items-center gap-2">
                <motion.div
                  animate={active ? { scale: [1, 1.1, 1] } : { scale: 1 }}
                  transition={active ? { repeat: Infinity, duration: 1.4 } : {}}
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border text-xs font-medium",
                    done && "border-aligned bg-aligned/10 text-aligned",
                    active && "border-primary bg-primary/10 text-primary",
                    !done && !active && "border-border text-muted-foreground",
                    failed && "border-border text-muted-foreground",
                  )}
                >
                  {done ? <Check className="h-4 w-4" /> : active ? <Loader2 className="h-4 w-4 animate-spin" /> : i + 1}
                </motion.div>
                <span
                  className={cn(
                    "whitespace-nowrap text-[11px]",
                    done || active ? "text-foreground/80" : "text-muted-foreground",
                  )}
                >
                  {s.label}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <div className={cn("mx-1 h-px flex-1", done ? "bg-aligned/40" : "bg-border")} />
              )}
            </div>
          );
        })}
      </div>

      {failed && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-misaligned/30 bg-misaligned/10 px-4 py-3 text-sm text-misaligned">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          Run failed during Completeness Verification — see the failure reason below.
        </div>
      )}

      {workUnits.length > 0 && (
        <div className="mt-6">
          <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Work Units</p>
          <div className="flex flex-col gap-2">
            {workUnits.map((wu) => (
              <div
                key={wu.work_unit_id}
                className="flex items-center justify-between rounded-lg border border-border bg-muted px-4 py-2.5 text-sm"
              >
                <span className="text-foreground/80">
                  {WORKER_LABEL[wu.worker_type] ?? wu.worker_type}
                  <span className="ml-2 text-xs text-muted-foreground">{wu.assertion_ids.length} assertion(s)</span>
                </span>
                <span
                  className={cn(
                    "flex items-center gap-1.5 text-xs font-medium",
                    wu.state === "succeeded" && "text-aligned",
                    wu.state === "executing" && "text-primary",
                    (wu.state === "failed" || wu.state === "timed_out") && "text-misaligned",
                    wu.state === "assigned" && "text-muted-foreground",
                  )}
                >
                  {wu.state === "executing" && <Loader2 className="h-3 w-3 animate-spin" />}
                  {WORK_UNIT_STATE_LABEL[wu.state]}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
