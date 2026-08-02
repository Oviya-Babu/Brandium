"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, GitBranch, Loader2, Plus, ScrollText, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createBrand, createWorkspace, getOrganization, listBrands, type Brand } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const schema = z.object({ brandName: z.string().min(1, "Required") });
type FormValues = z.infer<typeof schema>;

function BrandCard({ brand }: { brand: Brand }) {
  const genomeReady = !!brand.active_genome_version_id;
  const policyReady = !!brand.active_policy_version_id;
  return (
    <a href={`/brands/${brand.id}`} className="block">
      <Card className="transition-colors hover:border-primary/40">
        <CardHeader>
          <CardTitle>{brand.name}</CardTitle>
          <CardDescription>Brand workspace</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={genomeReady ? "aligned" : "secondary"} className="gap-1">
              <GitBranch className="h-3 w-3" /> Genome {genomeReady ? "active" : "not active"}
            </Badge>
            <Badge variant={policyReady ? "aligned" : "secondary"} className="gap-1">
              <ScrollText className="h-3 w-3" /> Policy {policyReady ? "active" : "not active"}
            </Badge>
          </div>
          <div className="mt-4 flex items-center gap-1 text-sm font-medium text-primary">
            Open workspace <ArrowRight className="h-3.5 w-3.5" />
          </div>
        </CardContent>
      </Card>
    </a>
  );
}

/**
 * Org-level home. Signup now owns "create an organization" (its own
 * dedicated page); this page's job is narrower and real: show every
 * Brand that actually exists for this Organization (`GET
 * /organizations/{id}/brands`, not a `localStorage`-remembered list
 * that was empty on any other browser/device), and let an admin spin
 * up another one.
 */
export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [orgId, setOrgId] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setOrgId(localStorage.getItem("brandium_org_id"));
  }, []);

  const orgQuery = useQuery({
    queryKey: ["organization", orgId],
    queryFn: () => getOrganization(orgId!),
    enabled: !!orgId,
  });
  const brandsQuery = useQuery({
    queryKey: ["brands", orgId],
    queryFn: () => listBrands(orgId!),
    enabled: !!orgId,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onCreateBrand(values: FormValues) {
    if (!orgId) return;
    setError(null);
    try {
      const workspace = await createWorkspace(orgId, `${values.brandName} Workspace`);
      const brand = await createBrand(workspace.id, values.brandName);
      await queryClient.invalidateQueries({ queryKey: ["brands", orgId] });
      reset();
      setDialogOpen(false);
      window.location.href = `/brands/${brand.id}`;
    } catch (err) {
      setError((err as Error).message);
    }
  }

  if (!orgId) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center px-6 text-center">
        <ShieldCheck className="mb-4 h-8 w-8 text-muted-foreground" />
        <h1 className="text-lg font-semibold text-foreground">No active session</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">Log in or create an organization to continue.</p>
        <div className="mt-6 flex gap-3">
          <Button variant="outline" asChild>
            <a href="/login">Log in</a>
          </Button>
          <Button asChild>
            <a href="/signup">Create organization</a>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            {orgQuery.data?.name ?? <Skeleton className="inline-block h-3 w-24 align-middle" />}
          </p>
          <h1 className="text-2xl font-semibold text-foreground">Brands</h1>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4" /> New brand
            </Button>
          </DialogTrigger>
          <DialogContent>
            <form onSubmit={handleSubmit(onCreateBrand)}>
              <DialogHeader>
                <DialogTitle>Create a brand</DialogTitle>
                <DialogDescription>Creates a Workspace and Brand within your organization.</DialogDescription>
              </DialogHeader>
              <div className="py-4">
                <Label htmlFor="brandName">Brand name</Label>
                <Input id="brandName" placeholder="e.g. Red Bull" className="mt-1.5" {...register("brandName")} />
                {errors.brandName && <p className="mt-1 text-xs text-misaligned">{errors.brandName.message}</p>}
                {error && <p className="mt-2 text-xs text-misaligned">{error}</p>}
              </div>
              <DialogFooter>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Create brand
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {brandsQuery.isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      )}

      {brandsQuery.data && brandsQuery.data.length === 0 && (
        <Card className="border-dashed">
          <CardContent>
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              <p className="text-sm text-muted-foreground">No brands yet in this organization.</p>
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="h-4 w-4" /> Create your first brand
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {brandsQuery.data && brandsQuery.data.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {brandsQuery.data.map((brand) => (
            <BrandCard key={brand.id} brand={brand} />
          ))}
        </div>
      )}
    </div>
  );
}
