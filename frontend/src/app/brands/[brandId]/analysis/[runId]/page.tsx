"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  Flag,
  GitBranch,
  History,
  Lightbulb,
  ListChecks,
  ScrollText,
} from "lucide-react";
import { use, useState } from "react";
import {
  approveReport,
  brandHistoryLabel,
  flagReport,
  getAnalysisProgress,
  getAnalysisRun,
  getBrandHistory,
  getEvidence,
  getExplainability,
  getRecommendations,
  getReportForRun,
  type BrandHistoryItem,
  type ExplainabilityAssertion,
  type ExplainabilityCategory,
  type ExplainabilityChain,
  type ExplainabilityComponent,
  type ExplainabilityEvidence,
} from "@/lib/api-client";
import { Badge, alignmentVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { PipelineTrack } from "@/components/pipeline-track";
import { BdiGauge } from "@/components/bdi-gauge";
import { AssetPreview } from "@/components/asset-preview";
import { cn } from "@/lib/utils";

const TERMINAL_STAGES = new Set(["complete", "failed"]);

function scoreColor(score: number): string {
  if (score >= 75) return "text-aligned";
  if (score >= 50) return "text-partial";
  return "text-misaligned";
}

export default function AnalysisRunPage({ params }: { params: Promise<{ brandId: string; runId: string }> }) {
  const { brandId, runId } = use(params);
  const [tab, setTab] = useState("evidence");

  const runQuery = useQuery({
    queryKey: ["analysis-run", runId],
    queryFn: () => getAnalysisRun(runId),
    refetchInterval: (query) =>
      query.state.data && (query.state.data.status === "complete" || query.state.data.status === "failed") ? false : 1500,
  });

  const progressQuery = useQuery({
    queryKey: ["analysis-progress", runId],
    queryFn: () => getAnalysisProgress(runId),
    refetchInterval: (query) => (query.state.data && TERMINAL_STAGES.has(query.state.data.stage) ? false : 1500),
  });

  const stage = progressQuery.data?.stage ?? "queued";
  const complete = stage === "complete";
  const failed = stage === "failed" || runQuery.data?.status === "failed";

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
  const brandHistoryQuery = useQuery({
    queryKey: ["brand-history", brandId],
    queryFn: () => getBrandHistory(brandId),
    enabled: complete,
  });

  if (runQuery.isLoading) {
    return <div className="mx-auto max-w-6xl px-6 py-12 text-sm text-muted-foreground">Loading run…</div>;
  }

  const run = runQuery.data;
  const evidence = evidenceQuery.data ?? [];
  const recommendations = recommendationsQuery.data ?? [];

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">Asset Analysis</p>
          <h1 className="text-2xl font-semibold text-foreground">{run?.asset_name ?? "Analysis"}</h1>
          <p className="mt-1 font-mono text-xs text-muted-foreground">{runId}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={complete ? "aligned" : failed ? "misaligned" : "secondary"} className="h-6">
            {complete ? "Analysis complete" : failed ? "Analysis failed" : "In progress"}
          </Badge>
          {complete && (
            <Button variant="outline" asChild>
              <a href={`/brands/${brandId}/analysis/${runId}/report`} target="_blank" rel="noreferrer">
                <Download className="h-4 w-4" /> Download Report
              </a>
            </Button>
          )}
        </div>
      </div>

      {/* Hero: asset + BDI, once resolvable */}
      {run && (
        <div className="mb-6 grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Asset</CardTitle>
              <CardDescription>{run.asset_modality === "image" ? "Image" : "Text"} asset submitted for evaluation.</CardDescription>
            </CardHeader>
            <CardContent>
              <AssetPreview versionId={run.asset_version_id} modality={run.asset_modality} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Brand Distinctiveness Index</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center">
              {complete && explainabilityQuery.data ? (
                <>
                  <BdiGauge score={explainabilityQuery.data.score} />
                  <Badge
                    variant={explainabilityQuery.data.verdict.toLowerCase().includes("non") ? "misaligned" : "aligned"}
                    className="mt-3"
                  >
                    {explainabilityQuery.data.verdict}
                  </Badge>
                  <p className="mt-1 text-xs text-muted-foreground">via {explainabilityQuery.data.verdict_source}</p>
                </>
              ) : (
                <div className="flex h-44 flex-col items-center justify-center gap-2 text-center text-sm text-muted-foreground">
                  {failed ? (
                    <>
                      <AlertTriangle className="h-6 w-6 text-misaligned" />
                      No score — run did not complete.
                    </>
                  ) : (
                    "Scoring in progress…"
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Live pipeline */}
      <div className="mb-6">
        <PipelineTrack stage={stage} workUnits={progressQuery.data?.work_units ?? []} />
      </div>

      {failed && run?.failure_reason && (
        <Card className="mb-6 border-misaligned/30">
          <CardContent>
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-misaligned" />
              <div>
                <p className="text-sm font-medium text-misaligned">Analysis did not complete</p>
                <p className="mt-1 text-sm text-muted-foreground">{run.failure_reason}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {complete && explainabilityQuery.data && (
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="evidence">
              <ListChecks className="h-3.5 w-3.5" /> Evidence
            </TabsTrigger>
            <TabsTrigger value="genome">
              <GitBranch className="h-3.5 w-3.5" /> Genome &amp; Policy
            </TabsTrigger>
            <TabsTrigger value="recommendations">
              <Lightbulb className="h-3.5 w-3.5" /> Recommendations
            </TabsTrigger>
            <TabsTrigger value="report">
              <ScrollText className="h-3.5 w-3.5" /> Report
            </TabsTrigger>
          </TabsList>

          <TabsContent value="evidence">
            <div className="flex flex-col gap-2">
              {evidence.map((e) => (
                <Card key={e.id} className="p-4">
                  <div className="flex items-center justify-between gap-4">
                    <p className="text-sm text-foreground/80">{e.observed_characteristic?.description ?? "—"}</p>
                    <div className="flex shrink-0 items-center gap-2">
                      <Badge variant={alignmentVariant(e.alignment_indicator)}>{e.alignment_indicator}</Badge>
                      <span className="text-xs text-muted-foreground">{(e.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </Card>
              ))}
              {evidence.length === 0 && <p className="text-sm text-muted-foreground">No Evidence recorded.</p>}
            </div>
          </TabsContent>

          <TabsContent value="genome">
            <GenomeMatchTab data={explainabilityQuery.data} brandHistory={brandHistoryQuery.data ?? []} />
          </TabsContent>

          <TabsContent value="recommendations">
            <div className="flex flex-col gap-2">
              {recommendations.map((r) => (
                <Card key={r.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <div>
                      <p className="text-sm text-foreground">{r.text}</p>
                      <p className="mt-2 text-xs text-muted-foreground">
                        priority {r.priority.toFixed(2)} — grounded in {r.related_evidence_ids.length} evidence item(s)
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
              {recommendations.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  None triggered — no Component fell below its improvement threshold.
                </p>
              )}
            </div>
          </TabsContent>

          <TabsContent value="report">
            <ReportTab
              reportId={reportQuery.data?.id ?? null}
              reviewStatus={reportQuery.data?.review_status ?? null}
              reportUrl={`/brands/${brandId}/analysis/${runId}/report`}
            />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}

function GenomeMatchTab({ data, brandHistory }: { data: ExplainabilityChain; brandHistory: BrandHistoryItem[] }) {
  const historyById = new Map(brandHistory.map((h) => [h.id, h]));
  return (
    <div className="flex flex-col gap-3">
      {data.categories.map((cat: ExplainabilityCategory) => (
        <Collapsible key={cat.id} defaultOpen>
          <Card className="p-0">
            <CollapsibleTrigger className="flex w-full items-center justify-between px-6 py-4">
              <span className="font-semibold text-foreground">{cat.name.replaceAll("_", " ")}</span>
              {cat.result && (
                <span className={cn("text-sm font-medium", scoreColor(cat.result.value * 100))}>
                  {(cat.result.value * 100).toFixed(0)}
                </span>
              )}
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent>
                <div className="flex flex-col gap-4 border-t border-border pt-4">
                  {cat.components.map((comp: ExplainabilityComponent) => (
                    <div key={comp.id} className="ml-2">
                      <div className="mb-2 flex items-center justify-between">
                        <p className="text-sm font-medium text-foreground/80">{comp.name}</p>
                        {comp.result && (
                          <span className="text-xs text-muted-foreground">{(comp.result.value * 100).toFixed(0)}</span>
                        )}
                      </div>
                      <div className="flex flex-col gap-3 border-l border-border pl-3">
                        {comp.assertions.map((a: ExplainabilityAssertion) => (
                          <div key={a.id}>
                            <p className="text-sm text-foreground/80">{a.content}</p>
                            <div className="mt-1 flex flex-wrap items-center gap-1.5">
                              {a.source_reference_ids.map((refId: string) => {
                                const item = historyById.get(refId);
                                return (
                                  <span key={refId} className="flex items-center gap-1 text-[11px] text-muted-foreground">
                                    <History className="h-3 w-3" />
                                    {item ? brandHistoryLabel(item) : refId.slice(0, 8)}
                                  </span>
                                );
                              })}
                            </div>
                            <div className="mt-1.5 flex flex-col gap-1">
                              {a.evidence.map((e: ExplainabilityEvidence) => (
                                <div key={e.evidence_id} className="flex items-center gap-2 text-xs">
                                  <Badge variant={alignmentVariant(e.alignment_indicator)}>{e.alignment_indicator}</Badge>
                                  <span className="text-muted-foreground">{e.observed_characteristic?.description}</span>
                                </div>
                              ))}
                              {a.evidence.length === 0 && (
                                <span className="text-xs text-muted-foreground">No Evidence for this Assertion.</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </CollapsibleContent>
          </Card>
        </Collapsible>
      ))}
    </div>
  );
}

function ReportTab({
  reportId,
  reviewStatus,
  reportUrl,
}: {
  reportId: string | null;
  reviewStatus: string | null;
  reportUrl: string;
}) {
  const [status, setStatus] = useState(reviewStatus);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");

  async function handleApprove() {
    if (!reportId) return;
    setError(null);
    try {
      const report = await approveReport(reportId);
      setStatus(report.review_status);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function handleFlag() {
    if (!reportId || !reason) return;
    setError(null);
    try {
      const report = await flagReport(reportId, reason);
      setStatus(report.review_status);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Report</CardTitle>
        <CardDescription>Review status: {status ?? "unknown"}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button variant="outline" asChild>
            <a href={reportUrl} target="_blank" rel="noreferrer">
              <Download className="h-4 w-4" /> Open full report
            </a>
          </Button>
          <Button variant="secondary" onClick={handleApprove}>
            <CheckCircle2 className="h-4 w-4" /> Approve
          </Button>
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Flag reason"
            className="h-10 flex-1 rounded-lg border border-border bg-card px-3 text-sm text-foreground placeholder:text-muted-foreground"
          />
          <Button variant="destructive" onClick={handleFlag} disabled={!reason}>
            <Flag className="h-4 w-4" /> Flag
          </Button>
        </div>
        {error && (
          <p className="mt-3 text-xs text-muted-foreground">
            {error} — approving/flagging requires the MarketingManager role (Phase 5 §3), which the onboarding
            bootstrap grant does not include.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
