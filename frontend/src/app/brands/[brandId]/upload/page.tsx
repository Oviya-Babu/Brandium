"use client";

import { useRouter } from "next/navigation";
import { use, useMemo, useState } from "react";
import { AlertTriangle, FileText, Image as ImageIcon, Loader2, UploadCloud, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { createAsset, createCampaign, getBrand, triggerAnalysis, uploadAssetVersion } from "@/lib/api-client";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

/**
 * Upload Workspace — text or image content only (video out of scope for
 * this pass). On submit, the AnalysisRun is created and dispatched to
 * the Celery-backed execution runtime (Phase 4); the user is taken
 * straight to the flagship Live Analysis view, nested under this same
 * Brand (`/brands/{id}/analysis/{runId}`) rather than a disconnected
 * top-level route.
 */
export default function UploadPage({ params }: { params: Promise<{ brandId: string }> }) {
  const { brandId } = use(params);
  const router = useRouter();
  const [campaignName, setCampaignName] = useState("Demo Campaign");
  const [assetName, setAssetName] = useState("Ad copy v1");
  const [modality, setModality] = useState<"text" | "image">("text");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [status, setStatus] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const brandQuery = useQuery({ queryKey: ["brand", brandId], queryFn: () => getBrand(brandId) });
  const ready = !!brandQuery.data?.active_genome_version_id && !!brandQuery.data?.active_policy_version_id;

  const previewUrl = useMemo(() => (file && modality === "image" ? URL.createObjectURL(file) : null), [file, modality]);

  function handleFiles(files: FileList | null) {
    setFile(files?.[0] ?? null);
  }

  async function handleUploadAndAnalyze() {
    if (!file) return;
    setSubmitting(true);
    setError(null);
    try {
      setStatus("Creating campaign & asset…");
      const campaign = await createCampaign(brandId, campaignName);
      const asset = await createAsset(campaign.id, assetName, modality);

      setStatus("Uploading asset version…");
      const form = new FormData();
      form.append("file", file);
      const version = await uploadAssetVersion(asset.id, form);

      setStatus("Dispatching to the execution runtime…");
      const run = await triggerAnalysis(version.id);
      router.push(`/brands/${brandId}/analysis/${run.id}`);
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-1 text-2xl font-semibold text-foreground">Upload</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Submit content for evaluation against this brand&apos;s active Genome and Policy.
      </p>

      {!ready && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Not ready for analysis</AlertTitle>
          <AlertDescription>
            This brand needs an active Genome and Policy before content can be scored. Set those up first.
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Submit content for analysis</CardTitle>
          <CardDescription>Applicability → Planning → Worker Execution → Evidence Fusion → Decision Engine.</CardDescription>
        </CardHeader>

        <CardContent>
          <div className="flex flex-col gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="campaignName">Campaign name</Label>
                <Input id="campaignName" value={campaignName} onChange={(e) => setCampaignName(e.target.value)} className="mt-1.5" />
              </div>
              <div>
                <Label htmlFor="assetName">Asset name</Label>
                <Input id="assetName" value={assetName} onChange={(e) => setAssetName(e.target.value)} className="mt-1.5" />
              </div>
            </div>

            <div>
              <Label>Modality</Label>
              <div className="mt-1.5 flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setModality("text");
                    setFile(null);
                  }}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm",
                    modality === "text" ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground",
                  )}
                >
                  <FileText className="h-4 w-4" /> Text
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setModality("image");
                    setFile(null);
                  }}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm",
                    modality === "image" ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground",
                  )}
                >
                  <ImageIcon className="h-4 w-4" /> Image
                </button>
              </div>
            </div>

            <div>
              <Label>File</Label>
              {!file ? (
                <label
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                  }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    handleFiles(e.dataTransfer.files);
                  }}
                  className={cn(
                    "mt-1.5 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-3 py-10 text-center transition-colors",
                    dragOver ? "border-primary bg-primary/5" : "border-border bg-muted hover:bg-muted/70",
                  )}
                >
                  <UploadCloud className="h-6 w-6 text-muted-foreground" />
                  <p className="text-sm text-foreground/80">
                    Drop a file, or <span className="font-medium text-primary">browse</span>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {modality === "text" ? ".txt, .md, .pdf, .docx" : "PNG, JPG"}
                  </p>
                  <input
                    type="file"
                    accept={modality === "text" ? ".txt,.md,.pdf,.docx" : "image/*"}
                    onChange={(e) => handleFiles(e.target.files)}
                    className="hidden"
                  />
                </label>
              ) : (
                <div className="mt-1.5 flex items-center gap-3 rounded-lg border border-border bg-muted px-3 py-3">
                  {previewUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={previewUrl} alt="" className="h-12 w-12 rounded-md object-cover" />
                  ) : (
                    <div className="flex h-12 w-12 items-center justify-center rounded-md bg-card">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</p>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => setFile(null)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            <Button onClick={handleUploadAndAnalyze} disabled={submitting || !file || !ready} size="lg">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
              Upload &amp; analyze
            </Button>

            {status && !error && <p className="text-sm text-muted-foreground">{status}</p>}
            {error && <p className="text-sm text-misaligned">Error: {error}</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
