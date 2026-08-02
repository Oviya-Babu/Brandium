"use client";

import { use, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, FileText, Loader2, UploadCloud } from "lucide-react";
import { brandHistoryLabel, getBrandHistory, ingestBrandHistory } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const AUTHORITY_VARIANT: Record<string, "aligned" | "partial"> = {
  explicit: "aligned",
  exemplar: "partial",
};

/**
 * Knowledge Repository — the real, persistent document library backing
 * a Brand's Genome (`BrandHistory`, ingested via `POST /brands/{id}/history`).
 * Previously this lived as one tab inside the Genome page; it's real
 * content management (upload, browse, filter what's been ingested) and
 * earns its own place in the workspace IA.
 */
export default function KnowledgeRepositoryPage({ params }: { params: Promise<{ brandId: string }> }) {
  const { brandId } = use(params);
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [sourceType, setSourceType] = useState("guideline_document");
  const [authorityLevel, setAuthorityLevel] = useState("explicit");
  const [busy, setBusy] = useState(false);

  const historyQuery = useQuery({
    queryKey: ["brand-history", brandId],
    queryFn: () => getBrandHistory(brandId),
  });

  async function handleIngest() {
    if (!file) return;
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    form.append("source_type", sourceType);
    form.append("modality", "text");
    form.append("authority_level", authorityLevel);
    try {
      await ingestBrandHistory(brandId, form);
      await queryClient.invalidateQueries({ queryKey: ["brand-history", brandId] });
      setFile(null);
      setDialogOpen(false);
    } finally {
      setBusy(false);
    }
  }

  const items = historyQuery.data ?? [];

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Knowledge Repository</h1>
          <p className="text-sm text-muted-foreground">
            Guideline documents, design system specs, and campaign material ingested for this brand.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <UploadCloud className="h-4 w-4" /> Ingest document
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Ingest Brand History</DialogTitle>
              <DialogDescription>Adds one document to this brand&apos;s Knowledge Repository.</DialogDescription>
            </DialogHeader>
            <div className="flex flex-col gap-4 py-2">
              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-2 file:text-sm file:text-foreground"
              />
              <div className="flex gap-2">
                <Select value={sourceType} onValueChange={setSourceType}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="guideline_document">Guideline document</SelectItem>
                    <SelectItem value="design_system_spec">Design system spec</SelectItem>
                    <SelectItem value="campaign">Campaign</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={authorityLevel} onValueChange={setAuthorityLevel}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="explicit">Explicit</SelectItem>
                    <SelectItem value="exemplar">Exemplar</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleIngest} disabled={busy || !file}>
                {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                Ingest
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ingested documents</CardTitle>
          <CardDescription>{items.length} document{items.length === 1 ? "" : "s"} in this repository.</CardDescription>
        </CardHeader>
        <CardContent>
          {historyQuery.isLoading && <Skeleton className="h-40 w-full" />}
          {items.length === 0 && !historyQuery.isLoading && (
            <div className="flex flex-col items-center gap-3 py-14 text-center">
              <BookOpen className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Nothing ingested yet — add your first document.</p>
            </div>
          )}
          {items.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Source type</TableHead>
                  <TableHead>Authority</TableHead>
                  <TableHead>Modality</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="flex items-center gap-2 font-medium text-foreground">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      {brandHistoryLabel(item)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{item.source_type.replaceAll("_", " ")}</TableCell>
                    <TableCell>
                      <Badge variant={AUTHORITY_VARIANT[item.authority_level] ?? "secondary"}>
                        {item.authority_level}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{item.modality}</TableCell>
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
