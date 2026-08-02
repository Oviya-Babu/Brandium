"use client";

import { use, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ChevronDown, GitBranch, Layers, Loader2, Sparkles } from "lucide-react";
import {
  activateGenome,
  compileGenomeDraft,
  getBrand,
  getGenomeCompileStatus,
  getGenomeTree,
  submitGenomeForReview,
  type GenomeCompileStatus,
} from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";

const STAGE_LABEL: Record<string, string> = {
  queued: "Queued for compilation…",
  extracting_candidates: "Extracting candidate assertions from Brand History (LLM)…",
  consolidating: "Consolidating candidates (Explicit outranks Exemplar)…",
  assembling_draft: "Assembling the draft Genome…",
};

export default function GenomePage({ params }: { params: Promise<{ brandId: string }> }) {
  const { brandId } = use(params);
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [genomeId, setGenomeId] = useState<string | null>(null);

  const brandQuery = useQuery({ queryKey: ["brand", brandId], queryFn: () => getBrand(brandId) });
  const effectiveGenomeId = genomeId ?? brandQuery.data?.active_genome_version_id ?? null;

  const treeQuery = useQuery({
    queryKey: ["genome-tree", brandId, effectiveGenomeId],
    queryFn: () => getGenomeTree(brandId, effectiveGenomeId!),
    enabled: !!effectiveGenomeId,
  });

  async function handleCompile() {
    setBusy(true);
    setStatus("Dispatching Genome compilation…");
    try {
      const { job_id } = await compileGenomeDraft(brandId);
      const maxAttempts = 150; // ~5 minutes at 2s/poll
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        const result: GenomeCompileStatus = await getGenomeCompileStatus(brandId, job_id);
        setStatus(STAGE_LABEL[result.stage] ?? result.stage);
        if (result.stage === "complete" && result.genome) {
          setGenomeId(result.genome.id);
          setStatus(`Draft created: version ${result.genome.version_number}, status ${result.genome.status}.`);
          return;
        }
        if (result.stage === "failed") {
          setStatus(`Compilation failed: ${result.error ?? "unknown error"}`);
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
      setStatus("Compilation is taking longer than expected — check back shortly or retry.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmitAndActivate() {
    if (!genomeId) return;
    setBusy(true);
    try {
      setStatus("Submitting for review (validation)…");
      await submitGenomeForReview(brandId, genomeId);
      setStatus("Activating (human sign-off)…");
      await activateGenome(brandId, genomeId);
      await queryClient.invalidateQueries({ queryKey: ["genome-tree", brandId, genomeId] });
      await queryClient.invalidateQueries({ queryKey: ["brand", brandId] });
      setStatus("Genome activated.");
    } finally {
      setBusy(false);
    }
  }

  const tree = treeQuery.data;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Brand Genome</h1>
          <p className="text-sm text-muted-foreground">
            Every ingested history item, compiled into Categories, Components, and Assertions.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleCompile} disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Compile draft
          </Button>
          <Button onClick={handleSubmitAndActivate} disabled={busy || !genomeId}>
            <CheckCircle2 className="h-4 w-4" />
            Submit &amp; activate
          </Button>
        </div>
      </div>

      {status && (
        <Card className="mb-6">
          <CardContent>
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              {busy && <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />}
              {status}
            </p>
          </CardContent>
        </Card>
      )}

      {treeQuery.isLoading && (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      )}

      {!tree && !treeQuery.isLoading && (
        <Card className="border-dashed">
          <CardContent>
            <div className="flex flex-col items-center gap-3 py-14 text-center">
              <GitBranch className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                No draft compiled yet in this session. Compile a draft from ingested Brand History to see it here.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {tree && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <Badge variant={genomeId ? "partial" : "aligned"}>
              {genomeId ? "Draft — not yet activated" : "Active version"}
            </Badge>
          </div>
          {tree.categories.map((cat) => (
            <Collapsible key={cat.id} defaultOpen>
              <Card className="p-0">
                <CollapsibleTrigger className="group flex w-full items-center justify-between px-6 py-4">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-primary" />
                    <span className="font-semibold text-foreground">{cat.name.replaceAll("_", " ")}</span>
                    <Badge variant="secondary">
                      {cat.components.reduce((n, c) => n + c.assertions.length, 0)} assertions
                    </Badge>
                  </div>
                  <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <CardContent>
                    <div className="flex flex-col gap-4 border-t border-border pt-4">
                      {cat.components.map((comp) => (
                        <div key={comp.id}>
                          <p className="mb-1.5 text-sm font-medium text-foreground/80">{comp.name}</p>
                          {comp.assertions.length === 0 ? (
                            <p className="ml-3 text-xs text-muted-foreground">No assertions yet.</p>
                          ) : (
                            <ul className="ml-3 flex flex-col gap-1.5 border-l border-border pl-3">
                              {comp.assertions.map((a) => (
                                <li key={a.id} className="text-sm text-muted-foreground">
                                  <span className="text-foreground/80">{a.content}</span>{" "}
                                  <span className="text-xs text-muted-foreground/70">
                                    (confidence {a.confidence.toFixed(2)}, {a.status})
                                  </span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>
          ))}
        </div>
      )}
    </div>
  );
}
