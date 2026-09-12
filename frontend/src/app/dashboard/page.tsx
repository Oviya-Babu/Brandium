"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  FileText,
  GitBranch,
  LayoutGrid,
  Loader2,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  createBrand,
  createWorkspace,
  getOrganization,
  listBrands,
  type Brand,
} from "@/lib/api-client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

const schema = z.object({
  brandName: z.string().min(1, "Brand name is required"),
});

type FormValues = z.infer<typeof schema>;

/* -------------------------------------------------------------------------- */
/* Brand Card                                                                 */
/* -------------------------------------------------------------------------- */

function BrandCard({ brand }: { brand: Brand }) {
  const genomeReady = !!brand.active_genome_version_id;
  const policyReady = !!brand.active_policy_version_id;

  const initials = brand.name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <a
      href={`/brands/${brand.id}`}
      className="group block h-full"
    >
      <Card className="relative h-full overflow-hidden border-[#e8e0f5] bg-white/90 shadow-[0_8px_30px_rgba(108,76,150,0.06)] transition-all duration-300 hover:-translate-y-1 hover:border-[#cfc0ee] hover:shadow-[0_16px_40px_rgba(108,76,150,0.12)]">
        {/* subtle lavender decoration */}
        <div className="pointer-events-none absolute right-0 top-0 h-32 w-32 rounded-full bg-[#eee7fb] opacity-50 blur-3xl transition-opacity group-hover:opacity-80" />

        <CardHeader className="relative pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-[#e4daf7] bg-[#f4effd] text-lg font-semibold text-[#7254c5] shadow-sm">
                {initials}
              </div>

              <div>
                <CardTitle className="text-lg font-semibold tracking-[-0.02em] text-[#202033]">
                  {brand.name}
                </CardTitle>

                <CardDescription className="mt-1 text-sm text-[#858097]">
                  Brand workspace
                </CardDescription>
              </div>
            </div>

            <Badge
              className={
                genomeReady && policyReady
                  ? "border-[#d8f0e2] bg-[#effaf3] text-[#3b9a63]"
                  : "border-[#f4dfbd] bg-[#fff8ec] text-[#c58a25]"
              }
            >
              <span
                className={`mr-1.5 h-1.5 w-1.5 rounded-full ${
                  genomeReady && policyReady
                    ? "bg-[#55b879]"
                    : "bg-[#e7a735]"
                }`}
              />
              {genomeReady && policyReady ? "Active" : "Setup"}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="relative">
          <div className="grid grid-cols-2 gap-3">
            {/* Genome */}
            <div className="rounded-2xl border border-[#eeeaf5] bg-[#fbfaff] p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#9690a5]">
                  Genome
                </span>

                {genomeReady ? (
                  <CheckCircle2 className="h-4 w-4 text-[#55b879]" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-[#e7a735]" />
                )}
              </div>

              <p
                className={`mt-3 text-sm font-semibold ${
                  genomeReady ? "text-[#41965f]" : "text-[#9b95a7]"
                }`}
              >
                {genomeReady ? "Active" : "Not active"}
              </p>

              <p className="mt-1 text-xs text-[#aaa5b5]">
                {genomeReady
                  ? "Source of truth ready"
                  : "Configure your genome"}
              </p>
            </div>

            {/* Policy */}
            <div className="rounded-2xl border border-[#eeeaf5] bg-[#fbfaff] p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#9690a5]">
                  Policy
                </span>

                {policyReady ? (
                  <CheckCircle2 className="h-4 w-4 text-[#55b879]" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-[#e7a735]" />
                )}
              </div>

              <p
                className={`mt-3 text-sm font-semibold ${
                  policyReady ? "text-[#41965f]" : "text-[#b38a45]"
                }`}
              >
                {policyReady ? "Active" : "Not configured"}
              </p>

              <p className="mt-1 text-xs text-[#aaa5b5]">
                {policyReady
                  ? "Brand rules active"
                  : "Add policy to get started"}
              </p>
            </div>
          </div>

          {/* Bottom action */}
          <div className="mt-5 flex items-center justify-between border-t border-[#eeeaf5] pt-5">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-[0.1em] text-[#aaa5b5]">
                Workspace
              </p>
              <p className="mt-1 text-sm font-medium text-[#4f4a5d]">
                Ready to explore
              </p>
            </div>

            <div className="flex items-center gap-2 text-sm font-semibold text-[#7355c7] transition-all group-hover:gap-3">
              Open workspace
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>
        </CardContent>
      </Card>
    </a>
  );
}

/* -------------------------------------------------------------------------- */
/* Metric Card                                                                */
/* -------------------------------------------------------------------------- */

function MetricCard({
  icon: Icon,
  value,
  label,
  description,
  variant,
}: {
  icon: typeof Sparkles;
  value: number;
  label: string;
  description: string;
  variant: "lavender" | "green" | "blue" | "peach";
}) {
  const styles = {
    lavender: {
      icon: "bg-[#f1eafd] text-[#7657ca]",
      glow: "bg-[#eee5fb]",
    },
    green: {
      icon: "bg-[#edf8f1] text-[#55a975]",
      glow: "bg-[#e5f6ec]",
    },
    blue: {
      icon: "bg-[#edf5fb] text-[#5797c7]",
      glow: "bg-[#e5f1fa]",
    },
    peach: {
      icon: "bg-[#fff4ed] text-[#d9955f]",
      glow: "bg-[#fff0e7]",
    },
  };

  return (
    <Card className="relative overflow-hidden border-[#ebe6f2] bg-white shadow-[0_6px_24px_rgba(80,60,120,0.045)]">
      <div
        className={`absolute -right-8 -top-8 h-24 w-24 rounded-full blur-2xl ${styles[variant].glow}`}
      />

      <CardContent className="relative flex items-center gap-4 p-5">
        <div
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${styles[variant].icon}`}
        >
          <Icon className="h-5 w-5" />
        </div>

        <div className="min-w-0">
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#242236]">
            {value}
          </p>

          <p className="mt-0.5 text-sm font-medium text-[#514b60]">
            {label}
          </p>

          <p className="mt-0.5 text-xs text-[#a09aaa]">
            {description}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

/* -------------------------------------------------------------------------- */
/* Dashboard                                                                  */
/* -------------------------------------------------------------------------- */

export default function DashboardPage() {
  const queryClient = useQueryClient();

  const [orgId, setOrgId] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

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
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  async function onCreateBrand(values: FormValues) {
    if (!orgId) return;

    setError(null);

    try {
      const workspace = await createWorkspace(
        orgId,
        `${values.brandName} Workspace`
      );

      const brand = await createBrand(
        workspace.id,
        values.brandName
      );

      await queryClient.invalidateQueries({
        queryKey: ["brands", orgId],
      });

      reset();
      setDialogOpen(false);

      window.location.href = `/brands/${brand.id}`;
    } catch (err) {
      setError((err as Error).message);
    }
  }

  /* ---------------------------------------------------------------------- */
  /* No session                                                              */
  /* ---------------------------------------------------------------------- */

  if (!orgId) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center px-6">
        <Card className="w-full max-w-md border-[#e8e0f5] bg-white shadow-[0_20px_60px_rgba(100,75,150,0.08)]">
          <CardContent className="flex flex-col items-center px-8 py-12 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-[#f1eafd]">
              <ShieldCheck className="h-7 w-7 text-[#7355c7]" />
            </div>

            <h1 className="mt-6 text-xl font-semibold text-[#242236]">
              Welcome to BrandGuard
            </h1>

            <p className="mt-2 max-w-sm text-sm leading-6 text-[#8f899d]">
              Log in or create an organization to start monitoring your
              brand identity.
            </p>

            <div className="mt-7 flex gap-3">
              <Button
                variant="outline"
                asChild
                className="border-[#ded5ed] hover:bg-[#f8f5fc]"
              >
                <a href="/login">Log in</a>
              </Button>

              <Button
                asChild
                className="bg-[#7657ca] text-white shadow-[0_6px_18px_rgba(118,87,202,0.2)] hover:bg-[#6749b9]"
              >
                <a href="/signup">Create organization</a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const brands = brandsQuery.data ?? [];

  const filteredBrands = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return brands;

    return brands.filter((brand) =>
      brand.name.toLowerCase().includes(value)
    );
  }, [brands, search]);

  const activeGenomes = brands.filter(
    (brand) => !!brand.active_genome_version_id
  ).length;

  const activePolicies = brands.filter(
    (brand) => !!brand.active_policy_version_id
  ).length;

  const policyAlerts = Math.max(brands.length - activePolicies, 0);

  /* ---------------------------------------------------------------------- */
  /* Main dashboard                                                          */
  /* ---------------------------------------------------------------------- */

  return (
    <main className="min-h-screen bg-[#faf9fc]">
      <div className="mx-auto max-w-[1400px] px-5 py-7 sm:px-8 lg:px-10">
        {/* ---------------------------------------------------------------- */}
        {/* Header                                                            */}
        {/* ---------------------------------------------------------------- */}

        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-[#9a91aa]">
              <Sparkles className="h-3.5 w-3.5 text-[#8b6ed1]" />
              {orgQuery.data?.name ?? "Organization"}
            </div>

            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-[#242236] sm:text-[34px]">
              Brand intelligence
            </h1>

            <p className="mt-2 max-w-xl text-sm leading-6 text-[#898398]">
              Monitor how consistently your brands are represented across
              content and campaigns.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#aaa4b5]" />

              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search brands..."
                className="h-11 w-full border-[#e5dfed] bg-white pl-10 text-sm shadow-sm placeholder:text-[#aaa4b5] focus-visible:border-[#bca9e5] focus-visible:ring-[#e8def8] sm:w-60"
              />
            </div>

            {/* Create brand */}
            <Dialog
              open={dialogOpen}
              onOpenChange={setDialogOpen}
            >
              <DialogTrigger asChild>
                <Button className="h-11 bg-[#7657ca] px-5 text-white shadow-[0_7px_20px_rgba(118,87,202,0.18)] hover:bg-[#6749b9]">
                  <Plus className="h-4 w-4" />
                  New brand
                </Button>
              </DialogTrigger>

              <DialogContent className="border-[#e8e0f5] bg-white">
                <form onSubmit={handleSubmit(onCreateBrand)}>
                  <DialogHeader>
                    <DialogTitle className="text-[#242236]">
                      Create a brand
                    </DialogTitle>

                    <DialogDescription className="text-[#8d879b]">
                      Creates a Workspace and Brand within your organization.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="py-5">
                    <Label
                      htmlFor="brandName"
                      className="text-[#514b60]"
                    >
                      Brand name
                    </Label>

                    <Input
                      id="brandName"
                      placeholder="e.g. Red Bull"
                      className="mt-2 border-[#e5dfed] focus-visible:border-[#bca9e5] focus-visible:ring-[#e8def8]"
                      {...register("brandName")}
                    />

                    {errors.brandName && (
                      <p className="mt-1.5 text-xs text-red-500">
                        {errors.brandName.message}
                      </p>
                    )}

                    {error && (
                      <p className="mt-2 text-xs text-red-500">
                        {error}
                      </p>
                    )}
                  </div>

                  <DialogFooter>
                    <Button
                      type="submit"
                      disabled={isSubmitting}
                      className="bg-[#7657ca] hover:bg-[#6749b9]"
                    >
                      {isSubmitting && (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      )}
                      Create brand
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Metrics                                                           */}
        {/* ---------------------------------------------------------------- */}

        <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            icon={LayoutGrid}
            value={brands.length}
            label="Total brands"
            description="Across all workspaces"
            variant="lavender"
          />

          <MetricCard
            icon={GitBranch}
            value={activeGenomes}
            label="Active genomes"
            description="Currently configured"
            variant="green"
          />

          <MetricCard
            icon={Activity}
            value={activePolicies}
            label="Active policies"
            description="Brand rules in use"
            variant="blue"
          />

          <MetricCard
            icon={AlertCircle}
            value={policyAlerts}
            label="Needs attention"
            description="Incomplete configuration"
            variant="peach"
          />
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* Brands section                                                    */}
        {/* ---------------------------------------------------------------- */}

        <section className="mt-10">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[#9b93a9]">
                Workspaces
              </p>

              <h2 className="mt-1.5 text-2xl font-semibold tracking-[-0.025em] text-[#29253a]">
                Your brands
              </h2>

              <p className="mt-1 text-sm text-[#8f899d]">
                Manage your brand identity and evaluation rules.
              </p>
            </div>

            <div className="hidden items-center gap-1 rounded-xl border border-[#e6dfef] bg-white p-1 sm:flex">
              <button className="flex items-center gap-2 rounded-lg bg-[#f1eafd] px-3 py-2 text-xs font-semibold text-[#7254c5]">
                <LayoutGrid className="h-3.5 w-3.5" />
                Grid
              </button>

              <button className="px-3 py-2 text-xs font-medium text-[#9992a4]">
                List
              </button>
            </div>
          </div>

          {/* Loading */}
          {brandsQuery.isLoading && (
            <div className="grid gap-5 md:grid-cols-2">
              {[0, 1].map((item) => (
                <Card
                  key={item}
                  className="border-[#e8e0f5] bg-white"
                >
                  <CardContent className="space-y-5 p-6">
                    <div className="flex gap-4">
                      <Skeleton className="h-14 w-14 rounded-2xl" />

                      <div className="space-y-2">
                        <Skeleton className="h-5 w-32" />
                        <Skeleton className="h-4 w-24" />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <Skeleton className="h-28 rounded-2xl" />
                      <Skeleton className="h-28 rounded-2xl" />
                    </div>

                    <Skeleton className="h-10 rounded-xl" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Empty */}
          {brandsQuery.data &&
            brandsQuery.data.length === 0 && (
              <Card className="border-dashed border-[#dcd1ed] bg-white">
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-[#f1eafd]">
                    <Sparkles className="h-7 w-7 text-[#795bc9]" />
                  </div>

                  <h3 className="mt-5 text-lg font-semibold text-[#2b2739]">
                    Your brand workspace starts here
                  </h3>

                  <p className="mt-2 max-w-md text-sm leading-6 text-[#918a9e]">
                    Create your first brand and build the structured
                    identity that BrandGuard will use for evaluation.
                  </p>

                  <Button
                    onClick={() => setDialogOpen(true)}
                    className="mt-6 bg-[#7657ca] hover:bg-[#6749b9]"
                  >
                    <Plus className="h-4 w-4" />
                    Create your first brand
                  </Button>
                </CardContent>
              </Card>
            )}

          {/* Search empty */}
          {brandsQuery.data &&
            brandsQuery.data.length > 0 &&
            filteredBrands.length === 0 && (
              <Card className="border-[#e8e0f5] bg-white">
                <CardContent className="flex flex-col items-center py-12 text-center">
                  <Search className="h-7 w-7 text-[#a59db2]" />

                  <p className="mt-4 text-sm font-medium text-[#4e485c]">
                    No brands found
                  </p>

                  <p className="mt-1 text-xs text-[#9d97a8]">
                    Try a different search term.
                  </p>
                </CardContent>
              </Card>
            )}

          {/* Brands */}
          {filteredBrands.length > 0 && (
            <div className="grid gap-5 md:grid-cols-2">
              {filteredBrands.map((brand) => (
                <BrandCard
                  key={brand.id}
                  brand={brand}
                />
              ))}
            </div>
          )}
        </section>

        {/* ---------------------------------------------------------------- */}
        {/* Product philosophy section                                       */}
        /* ---------------------------------------------------------------- */}

        <section className="mt-8">
          <Card className="overflow-hidden border-[#e4dbf1] bg-gradient-to-r from-[#f5f0fc] via-white to-[#f8f5fc] shadow-[0_8px_30px_rgba(100,75,150,0.05)]">
            <CardContent className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between sm:p-7">
              <div className="flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#ebe1fa] text-[#7657ca]">
                  <TrendingUp className="h-5 w-5" />
                </div>

                <div>
                  <p className="text-sm font-semibold text-[#393347]">
                    Evidence before AI
                  </p>

                  <p className="mt-1 max-w-2xl text-sm leading-6 text-[#8b8498]">
                    BrandGuard evaluates content against your structured
                    Brand Genome so every decision can be traced back to
                    evidence.
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-2 text-xs font-semibold text-[#7657ca]">
                <FileText className="h-4 w-4" />
                Evidence-first evaluation
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}