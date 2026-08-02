"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { Printer, ShieldCheck } from "lucide-react";
import {
  getAnalysisRun,
  getEvidence,
  getExplainability,
  getRecommendations,
  getReportForRun,
  type ExplainabilityCategory,
} from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Badge, alignmentVariant } from "@/components/ui/badge";

function scoreColor(score: number): string {
  if (score >= 75) return "text-aligned";
  if (score >= 50) return "text-partial";
  return "text-misaligned";
}

/**
 * Executive Report — a document, not a dashboard panel. Deliberately
 * plain, print-optimized layout so the browser's native "Print → Save
 * as PDF" produces a clean, presentable artifact; there is no backend
 * PDF generation service (see `reporting/domain/models.py`'s docstring
 * — `Report` is a review-workflow record, not a rendered file), so this
 * is the honest way to make "Download Report" real rather than a button
 * pointing at nothing.
 */
export default function ExecutiveReportPage({ params }: { params: Promise<{ brandId: string; runId: string }> }) {
  const { runId } = use(params);

  const runQuery = useQuery({ queryKey: ["analysis-run", runId], queryFn: () => getAnalysisRun(runId) });
  const run = runQuery.data;
  const complete = run?.status === "complete";

  const explainabilityQuery = useQuery({
    queryKey: ["explainability", runId],
    queryFn: () => getExplainability(runId),
    enabled: complete,
  });
  const evidenceQuery = useQuery({ queryKey: ["evidence", runId], queryFn: () => getEvidence(runId), enabled: complete });
  const recommendationsQuery = useQuery({
    queryKey: ["recommendations", runId],
    queryFn: () => getRecommendations(runId),
    enabled: complete,
  });
  const reportQuery = useQuery({ queryKey: ["report", runId], queryFn: () => getReportForRun(runId), enabled: complete });

  const data = explainabilityQuery.data;

  return (
    <div className="mx-auto max-w-3xl px-8 py-12 print:max-w-none print:px-0 print:py-0">
      <div className="mb-8 flex items-center justify-between print:hidden">
        <p className="text-sm text-muted-foreground">Print this page or save as PDF for a portable copy.</p>
        <Button onClick={() => window.print()}>
          <Printer className="h-4 w-4" /> Print / Save as PDF
        </Button>
      </div>

      <header className="mb-10 flex items-start justify-between border-b border-border pb-6">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <ShieldCheck className="h-5 w-5 text-primary" />
          BrandGuard AI — Executive Report
        </div>
        <div className="text-right text-xs text-muted-foreground">
          <p className="font-mono">{runId}</p>
          {run?.completed_at && <p>{new Date(run.completed_at).toLocaleString()}</p>}
        </div>
      </header>

      {run && !complete ? (
        <p className="text-sm text-muted-foreground">
          No report available — this analysis {run.status === "failed" ? "did not complete" : "is still in progress"}.
          {run.failure_reason && ` (${run.failure_reason})`}
        </p>
      ) : !data ? (
        <p className="text-sm text-muted-foreground">Loading report…</p>
      ) : (
        <>
          <section className="mb-10 grid grid-cols-3 gap-6">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Asset</p>
              <p className="mt-1 font-medium text-foreground">{data.asset.name}</p>
              <p className="text-xs text-muted-foreground">{data.asset.modality}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Brand Distinctiveness Index</p>
              <p className={`mt-1 text-3xl font-semibold ${scoreColor(data.score)}`}>{data.score.toFixed(1)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Verdict</p>
              <p className="mt-1">
                <Badge variant={data.verdict.toLowerCase().includes("non") ? "misaligned" : "aligned"}>{data.verdict}</Badge>
              </p>
              <p className="mt-1 text-xs text-muted-foreground">via {data.verdict_source}</p>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-foreground">Category breakdown</h2>
            <div className="flex flex-col gap-2">
              {data.categories.map((cat: ExplainabilityCategory) => (
                <div key={cat.id} className="flex items-center justify-between border-b border-border py-2 text-sm">
                  <span className="text-foreground/80">{cat.name.replaceAll("_", " ")}</span>
                  <span className={cat.result ? scoreColor(cat.result.value * 100) : "text-muted-foreground"}>
                    {cat.result ? (cat.result.value * 100).toFixed(0) : "—"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className="mb-10 break-inside-avoid">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-foreground">Recommendations</h2>
            {(recommendationsQuery.data ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">None triggered.</p>
            ) : (
              <ol className="flex flex-col gap-3">
                {(recommendationsQuery.data ?? []).map((r, i) => (
                  <li key={r.id} className="text-sm text-foreground/80">
                    <span className="font-medium text-foreground">{i + 1}.</span> {r.text}
                  </li>
                ))}
              </ol>
            )}
          </section>

          <section className="mb-10 break-inside-avoid">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-foreground">Evidence trace</h2>
            <div className="flex flex-col gap-1.5">
              {(evidenceQuery.data ?? []).slice(0, 20).map((e) => (
                <div key={e.id} className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-foreground/80">{e.observed_characteristic?.description ?? "—"}</span>
                  <Badge variant={alignmentVariant(e.alignment_indicator)}>{e.alignment_indicator}</Badge>
                </div>
              ))}
            </div>
          </section>

          <footer className="flex items-center justify-between border-t border-border pt-4 text-xs text-muted-foreground">
            <span>Review status: {reportQuery.data?.review_status ?? "unreviewed"}</span>
            <span>Generated by BrandGuard AI — deterministic, reproducible scoring.</span>
          </footer>
        </>
      )}
    </div>
  );
}
