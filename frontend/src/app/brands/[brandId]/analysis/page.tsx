"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileImage, FileText, ScanSearch, UploadCloud } from "lucide-react";
import { listAnalysisRuns } from "@/lib/api-client";
import { Badge, alignmentVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

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

export default function AnalysisHistoryPage({ params }: { params: Promise<{ brandId: string }> }) {
  const { brandId } = use(params);
  const runsQuery = useQuery({ queryKey: ["analysis-runs", brandId], queryFn: () => listAnalysisRuns(brandId) });
  const runs = runsQuery.data ?? [];

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Asset Analysis</h1>
          <p className="text-sm text-muted-foreground">Every asset submitted for evaluation against this brand.</p>
        </div>
        <Button asChild>
          <a href={`/brands/${brandId}/upload`}>
            <UploadCloud className="h-4 w-4" /> Upload asset
          </a>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All analyses</CardTitle>
          <CardDescription>{runs.length} run{runs.length === 1 ? "" : "s"}.</CardDescription>
        </CardHeader>
        <CardContent>
          {runsQuery.isLoading && <Skeleton className="h-64 w-full" />}
          {runs.length === 0 && !runsQuery.isLoading && (
            <div className="flex flex-col items-center gap-3 py-14 text-center">
              <ScanSearch className="h-8 w-8 text-muted-foreground" />
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
                {runs.map((run) => (
                  <TableRow
                    key={run.id}
                    className="cursor-pointer"
                    onClick={() => (window.location.href = `/brands/${brandId}/analysis/${run.id}`)}
                  >
                    <TableCell className="flex items-center gap-2 font-medium text-foreground">
                      {run.asset_modality === "image" ? (
                        <FileImage className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <FileText className="h-4 w-4 text-muted-foreground" />
                      )}
                      {run.asset_name}
                    </TableCell>
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
        </CardContent>
      </Card>
    </div>
  );
}
