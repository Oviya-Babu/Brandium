"use client";

import { useEffect, useState } from "react";
import { FileText, ImageOff } from "lucide-react";
import { getAssetVersionBlobUrl } from "@/lib/api-client";
import { Skeleton } from "@/components/ui/skeleton";

export function AssetPreview({ versionId, modality }: { versionId: string; modality: "text" | "image" }) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    setFailed(false);
    setImageUrl(null);
    setTextContent(null);

    (async () => {
      try {
        if (modality === "image") {
          const url = await getAssetVersionBlobUrl(versionId);
          if (cancelled) return;
          objectUrl = url;
          setImageUrl(url);
        } else {
          const url = await getAssetVersionBlobUrl(versionId);
          const response = await fetch(url);
          const text = await response.text();
          URL.revokeObjectURL(url);
          if (cancelled) return;
          setTextContent(text);
        }
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [versionId, modality]);

  if (failed) {
    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 rounded-lg bg-muted text-muted-foreground">
        <ImageOff className="h-6 w-6" />
        <span className="text-xs">Couldn&apos;t load asset content</span>
      </div>
    );
  }

  if (modality === "image") {
    return imageUrl ? (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={imageUrl} alt="Analyzed asset" className="w-full rounded-lg border border-border object-cover" />
    ) : (
      <Skeleton className="h-48 w-full rounded-lg" />
    );
  }

  return textContent !== null ? (
    <div className="max-h-48 overflow-y-auto rounded-lg border border-border bg-muted p-4">
      <div className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
        <FileText className="h-3.5 w-3.5" /> Text asset
      </div>
      <p className="whitespace-pre-wrap text-sm text-foreground/80">{textContent}</p>
    </div>
  ) : (
    <Skeleton className="h-48 w-full rounded-lg" />
  );
}
