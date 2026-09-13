"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  FileImage,
  FileText,
  ScanSearch,
  Sparkles,
  UploadCloud,
  XCircle,
} from "lucide-react";

import { listAnalysisRuns } from "@/lib/api-client";
import { Badge, alignmentVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

function statusVariant(
  status: string,
): "aligned" | "misaligned" | "secondary" {
  if (status === "complete") return "aligned";
  if (status === "failed") return "misaligned";
  return "secondary";
}

function isAligned(verdict: string | null): boolean {
  if (!verdict) return false;

  return !verdict.toLowerCase().includes("non");
}

export default function AnalysisHistoryPage({
  params,
}: {
  params: Promise<{ brandId: string }>;
}) {
  const { brandId } = use(params);

  const runsQuery = useQuery({
    queryKey: ["analysis-runs", brandId],
    queryFn: () => listAnalysisRuns(brandId),
  });

  const runs = runsQuery.data ?? [];

  const completedRuns = runs.filter(
    (run) => run.status === "complete" && run.score !== null,
  );

  const averageScore =
    completedRuns.length > 0
      ? completedRuns.reduce((total, run) => total + (run.score ?? 0), 0) /
        completedRuns.length
      : null;

  const alignedCount = runs.filter(
    (run) => run.verdict && isAligned(run.verdict),
  ).length;

  const needsReviewCount = runs.filter(
    (run) => run.verdict && !isAligned(run.verdict),
  ).length;

  return (
    <div className="min-h-screen bg-background">
      {/* Top navigation */}
      <div className="border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" asChild>
              <a href="/dashboard" aria-label="Back to dashboard">
                <ArrowLeft className="h-4 w-4" />
              </a>
            </Button>

            <div className="h-6 w-px bg-border" />

            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Brand workspace
              </p>
              <p className="text-sm font-semibold text-foreground">
                Brand Intelligence
              </p>
            </div>
          </div>

          <Button asChild>
            <a href={`/brands/${brandId}/upload`}>
              <UploadCloud className="mr-2 h-4 w-4" />
              Evaluate asset
            </a>
          </Button>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Hero */}
        <section className="relative overflow-hidden rounded-3xl border bg-card px-7 py-8 shadow-sm">
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-32 left-1/3 h-56 w-56 rounded-full bg-purple-500/10 blur-3xl" />

          <div className="relative flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
            <div className="max-w-2xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                Brand Decision Intelligence
              </div>

              <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                Is your content
                <span className="block text-primary">
                  unmistakably your brand?
                </span>
              </h1>

              <p className="mt-4 max-w-xl text-sm leading-6 text-muted-foreground sm:text-base">
                Evaluate generated content against your brand identity and
                understand where it aligns, drifts, or needs review.
              </p>
            </div>

            <div className="rounded-2xl border bg-background/80 px-5 py-4 lg:min-w-[220px]">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Brand ID
              </p>
              <p className="mt-1 truncate text-sm font-semibold text-foreground">
                {brandId}
              </p>
            </div>
          </div>
        </section>

        {/* Metrics */}
        <section className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Total analyses
                  </p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight">
                    {runsQuery.isLoading ? "—" : runs.length}
                  </p>
                </div>

                <div className="rounded-xl bg-primary/10 p-2.5">
                  <BarChart3 className="h-5 w-5 text-primary" />
                </div>
              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Assets evaluated against this brand
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Average BDI
                  </p>
                  <p
                    className={`mt-2 text-3xl font-semibold tracking-tight ${
                      averageScore !== null
                        ? scoreColor(averageScore)
                        : "text-foreground"
                    }`}
                  >
                    {averageScore !== null
                      ? averageScore.toFixed(1)
                      : "—"}
                  </p>
                </div>

                <div className="rounded-xl bg-muted p-2.5">
                  <ScanSearch className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Across completed evaluations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Aligned
                  </p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight text-aligned">
                    {runsQuery.isLoading ? "—" : alignedCount}
                  </p>
                </div>

                <div className="rounded-xl bg-green-500/10 p-2.5">
                  <CheckCircle2 className="h-5 w-5 text-aligned" />
                </div>
              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Content meeting brand expectations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Needs review
                  </p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight text-misaligned">
                    {runsQuery.isLoading ? "—" : needsReviewCount}
                  </p>
                </div>

                <div className="rounded-xl bg-red-500/10 p-2.5">
                  <XCircle className="h-5 w-5 text-misaligned" />
                </div>
              </div>

              <p className="mt-3 text-xs text-muted-foreground">
                Content requiring attention
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Evaluation workspace */}
        <section className="mt-6 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="flex min-h-[260px] flex-col justify-between p-7">
                <div>
                  <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10">
                    <UploadCloud className="h-5 w-5 text-primary" />
                  </div>

                  <h2 className="text-xl font-semibold">
                    Evaluate new content
                  </h2>

                  <p className="mt-2 max-w-lg text-sm leading-6 text-muted-foreground">
                    Upload an image or supported asset to measure how
                    distinctly it represents this brand.
                  </p>
                </div>

                <div className="mt-8 flex flex-wrap items-center gap-3">
                  <Button asChild>
                    <a href={`/brands/${brandId}/upload`}>
                      Start evaluation
                      <ArrowUpRight className="ml-2 h-4 w-4" />
                    </a>
                  </Button>

                  <span className="text-xs text-muted-foreground">
                    Evidence-first brand validation
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Brand Genome</CardTitle>
                  <CardDescription className="mt-1">
                    Your brand identity foundation
                  </CardDescription>
                </div>

                <div className="rounded-xl bg-primary/10 p-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <div className="space-y-3">
                {[
                  "Brand voice",
                  "Visual identity",
                  "Distinctive signals",
                  "Content principles",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center justify-between rounded-xl border bg-muted/30 px-4 py-3"
                  >
                    <span className="text-sm font-medium">{item}</span>
                    <span className="text-xs text-muted-foreground">
                      Configure
                    </span>
                  </div>
                ))}
              </div>

              <p className="mt-4 text-xs leading-5 text-muted-foreground">
                The Brand Genome acts as the structured source of truth used
                when evaluating brand distinctiveness.
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Analysis history */}
        <section className="mt-8">
          <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Evaluation history
              </p>
              <h2 className="mt-1 text-xl font-semibold">
                Recent brand decisions
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Review every asset submitted for brand validation.
              </p>
            </div>

            {runs.length > 0 && (
              <span className="text-xs text-muted-foreground">
                {runs.length} evaluation{runs.length === 1 ? "" : "s"}
              </span>
            )}
          </div>

          <Card>
            <CardContent className="p-0">
              {runsQuery.isLoading && (
                <div className="p-6">
                  <Skeleton className="h-64 w-full rounded-xl" />
                </div>
              )}

              {!runsQuery.isLoading && runs.length === 0 && (
                <div className="flex min-h-[300px] flex-col items-center justify-center px-6 py-14 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl border bg-muted/40">
                    <ScanSearch className="h-6 w-6 text-muted-foreground" />
                  </div>

                  <h3 className="mt-5 text-base font-semibold">
                    No evaluations yet
                  </h3>

                  <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">
                    Upload your first asset to see its BDI score, verdict, and
                    evaluation evidence here.
                  </p>

                  <Button className="mt-5" asChild>
                    <a href={`/brands/${brandId}/upload`}>
                      <UploadCloud className="mr-2 h-4 w-4" />
                      Evaluate first asset
                    </a>
                  </Button>
                </div>
              )}

              {!runsQuery.isLoading && runs.length > 0 && (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="pl-6">Asset</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>BDI</TableHead>
                        <TableHead>Verdict</TableHead>
                        <TableHead className="text-right pr-6">
                          Submitted
                        </TableHead>
                      </TableRow>
                    </TableHeader>

                    <TableBody>
                      {runs.map((run) => (
                        <TableRow
                          key={run.id}
                          className="cursor-pointer transition-colors hover:bg-muted/40"
                          onClick={() => {
                            window.location.href = `/brands/${brandId}/analysis/${run.id}`;
                          }}
                        >
                          <TableCell className="pl-6">
                            <div className="flex items-center gap-3">
                              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                                {run.asset_modality === "image" ? (
                                  <FileImage className="h-4 w-4 text-muted-foreground" />
                                ) : (
                                  <FileText className="h-4 w-4 text-muted-foreground" />
                                )}
                              </div>

                              <div className="min-w-0">
                                <p className="max-w-[260px] truncate text-sm font-medium text-foreground">
                                  {run.asset_name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {run.asset_modality}
                                </p>
                              </div>
                            </div>
                          </TableCell>

                          <TableCell>
                            <Badge variant={statusVariant(run.status)}>
                              {run.status}
                            </Badge>
                          </TableCell>

                          <TableCell
                            className={`font-semibold ${
                              run.score !== null
                                ? scoreColor(run.score)
                                : "text-muted-foreground"
                            }`}
                          >
                            {run.score !== null
                              ? run.score.toFixed(1)
                              : "—"}
                          </TableCell>

                          <TableCell>
                            {run.verdict ? (
                              <Badge
                                variant={alignmentVariant(
                                  isAligned(run.verdict)
                                    ? "aligned"
                                    : "misaligned",
                                )}
                              >
                                {run.verdict}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>

                          <TableCell className="pr-6 text-right text-xs text-muted-foreground">
                            {run.started_at
                              ? new Date(run.started_at).toLocaleString()
                              : "Queued"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}