"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  GitBranch,
  ScrollText,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  UploadCloud,
} from "lucide-react";
import { getBrand, listAnalysisRuns } from "@/lib/api-client";
import { Badge, alignmentVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function scoreColor(score: number): string {
  if (score >= 75) return "text-aligned";
  if (score >= 50) return "text-partial";
  return "text-misaligned";
}

function statusVariant(status: string): "aligned" | "misaligned" | "secondary" {
  if (status === "complete") return "aligned";
  if (status === "failed") return "misaligned";
  return "secondary";
}

export default function BrandOverviewPage({ params }: { params: Promise<{ brandId: string }> }) {
  const { brandId } = use(params);
  const brandQuery = useQuery({ queryKey: ["brand", brandId], queryFn: () => getBrand(brandId) });
  const runsQuery = useQuery({ queryKey: ["analysis-runs", brandId], queryFn: () => listAnalysisRuns(brandId) });

  const runs = runsQuery.data ?? [];
  const scored = runs.filter((r) => r.score !== null);
  const avgScore = scored.length ? scored.reduce((sum, r) => sum + (r.score ?? 0), 0) / scored.length : null;
  const activeCount = runs.filter((r) => r.status === "queued" || r.status === "running").length;

  const genomeReady = !!brandQuery.data?.active_genome_version_id;
  const policyReady = !!brandQuery.data?.active_policy_version_id;
  const readyForAnalysis = genomeReady && policyReady;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Overview</h1>
          <p className="text-sm text-muted-foreground">Brand health, governance status, and recent activity.</p>
        </div>
        <Button asChild disabled={!readyForAnalysis}>
          <a href={`/brands/${brandId}/upload`}>
            <UploadCloud className="h-4 w-4" /> Upload asset
          </a>
        </Button>
      </div>

      {!readyForAnalysis && (
        <Card className="mb-6 border-partial/30 bg-partial/5">
          <CardContent>
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-partial" />
              <div className="text-sm">
                <p className="font-medium text-foreground">This brand isn&apos;t ready for analysis yet.</p>
                <p className="mt-1 text-muted-foreground">
                  {!genomeReady && "Activate a Brand Genome"}
                  {!genomeReady && !policyReady && " and "}
                  {!policyReady && "activate a Policy"} before submitting content.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardDescription>Average BDI</CardDescription>
          </CardHeader>
          <CardContent>
            <p className={`text-3xl font-semibold ${avgScore !== null ? scoreColor(avgScore) : "text-muted-foreground"}`}>
              {avgScore !== null ? avgScore.toFixed(1) : "—"}
            </p>
            <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3" /> across {scored.length} scored asset{scored.length === 1 ? "" : "s"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Total analyses</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold text-foreground">{runs.length}</p>
            <p className="mt-1 text-xs text-muted-foreground">{activeCount} in progress</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Brand Genome</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <GitBranch className={`h-5 w-5 ${genomeReady ? "text-aligned" : "text-muted-foreground"}`} />
              <span className="text-sm font-medium text-foreground">{genomeReady ? "Active" : "Not active"}</span>
            </div>
            <a href={`/brands/${brandId}/genome`} className="mt-2 flex items-center gap-1 text-xs text-primary hover:text-primary/80">
              Manage <ArrowRight className="h-3 w-3" />
            </a>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Policy</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <ScrollText className={`h-5 w-5 ${policyReady ? "text-aligned" : "text-muted-foreground"}`} />
              <span className="text-sm font-medium text-foreground">{policyReady ? "Active" : "Not active"}</span>
            </div>
            <a href={`/brands/${brandId}/policies`} className="mt-2 flex items-center gap-1 text-xs text-primary hover:text-primary/80">
              Manage <ArrowRight className="h-3 w-3" />
            </a>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent analyses</CardTitle>
          <CardDescription>Every asset submitted for evaluation against this brand.</CardDescription>
        </CardHeader>
        <CardContent>
          {runsQuery.isLoading && <Skeleton className="h-40 w-full" />}
          {runs.length === 0 && !runsQuery.isLoading && (
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              <ShieldCheck className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No assets analyzed yet.</p>
            </div>
          )}
          {runs.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Asset</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>BDI</TableHead>
                  <TableHead>Verdict</TableHead>
                  <TableHead className="text-right">Submitted</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.slice(0, 8).map((run) => (
                  <TableRow key={run.id} className="cursor-pointer" onClick={() => (window.location.href = `/brands/${brandId}/analysis/${run.id}`)}>
                    <TableCell className="font-medium text-foreground">{run.asset_name}</TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
                    </TableCell>
                    <TableCell className={run.score !== null ? scoreColor(run.score) : "text-muted-foreground"}>
                      {run.score !== null ? run.score.toFixed(1) : "—"}
                    </TableCell>
                    <TableCell>
                      {run.verdict ? (
                        <Badge variant={alignmentVariant(run.verdict.toLowerCase().includes("non") ? "misaligned" : "aligned")}>
                          {run.verdict}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right text-xs text-muted-foreground">
                      {run.started_at ? new Date(run.started_at).toLocaleString() : "queued"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {runs.length > 0 && (
            <a
              href={`/brands/${brandId}/analysis`}
              className="mt-4 flex items-center gap-1 text-sm font-medium text-primary hover:text-primary/80"
            >
              View all analyses <ArrowRight className="h-3.5 w-3.5" />
            </a>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
