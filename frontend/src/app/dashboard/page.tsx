"use client";

import {
  Activity,
  AlertCircle,
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
  type LucideIcon,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { z } from "zod";

import {
  createBrand,
  createWorkspace,
  getOrganization,
  listBrands,
  type Brand,
} from "@/lib/api-client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

const brandSchema = z.object({
  name: z.string().min(2, "Brand name must be at least 2 characters."),
});

type MetricCardProps = {
  title: string;
  value: number;
  subtitle: string;
  icon: LucideIcon;
  variant: "lavender" | "green" | "blue" | "peach";
};

const metricVariants = {
  lavender: {
    icon: "bg-violet-100 text-violet-600",
    value: "text-violet-700",
    border: "border-violet-100",
  },
  green: {
    icon: "bg-emerald-100 text-emerald-600",
    value: "text-emerald-700",
    border: "border-emerald-100",
  },
  blue: {
    icon: "bg-sky-100 text-sky-600",
    value: "text-sky-700",
    border: "border-sky-100",
  },
  peach: {
    icon: "bg-orange-100 text-orange-600",
    value: "text-orange-700",
    border: "border-orange-100",
  },
};

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant,
}: MetricCardProps) {
  const styles = metricVariants[variant];

  return (
    <Card
      className={`border ${styles.border} bg-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md`}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>

            <p
              className={`mt-2 text-3xl font-semibold tracking-tight ${styles.value}`}
            >
              {value}
            </p>

            <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
          </div>

          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl ${styles.icon}`}
          >
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function BrandCard({
  brand,
  onOpen,
}: {
  brand: Brand;
  onOpen: () => void;
}) {
  const initials =
    brand.name
      .split(" ")
      .map((word: string) => word[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() || "BR";

  const genomeReady = Boolean(brand.active_genome_version_id);

  const policyReady = Boolean(brand.active_policy_version_id);

  return (
    <Card className="group border-slate-200/80 bg-white shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-violet-200 hover:shadow-lg">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-100 text-sm font-semibold text-violet-700">
              {initials}
            </div>

            <div>
              <CardTitle className="text-base font-semibold text-slate-900">
                {brand.name}
              </CardTitle>

              <p className="mt-1 text-xs text-slate-400">
                Brand intelligence workspace
              </p>
            </div>
          </div>

          <Badge
            variant="secondary"
            className={
              genomeReady
                ? "bg-emerald-50 text-emerald-700"
                : "bg-amber-50 text-amber-700"
            }
          >
            {genomeReady ? "Active" : "Setup"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-violet-500" />

              <span className="text-xs font-medium text-slate-500">
                Genome
              </span>
            </div>

            <div className="mt-2 flex items-center gap-1.5">
              {genomeReady ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-amber-500" />
              )}

              <span className="text-sm font-medium text-slate-700">
                {genomeReady ? "Ready" : "Not configured"}
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-sky-500" />

              <span className="text-xs font-medium text-slate-500">
                Policies
              </span>
            </div>

            <div className="mt-2 flex items-center gap-1.5">
              {policyReady ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-amber-500" />
              )}

              <span className="text-sm font-medium text-slate-700">
                {policyReady ? "Active" : "Not configured"}
              </span>
            </div>
          </div>
        </div>

        <Button
          onClick={onOpen}
          variant="outline"
          className="w-full border-slate-200 text-slate-700 hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700"
        >
          Open brand
          <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </Button>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [orgId, setOrgId] = useState<string | null>(null);

  const [organization, setOrganization] = useState<{
    id: string;
    name: string;
  } | null>(null);

  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [brandName, setBrandName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;

    const storedOrgId = window.localStorage.getItem("brandium_org_id");

    if (storedOrgId) {
      setOrgId(storedOrgId);
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!orgId) return;

    let cancelled = false;

    async function loadDashboard(currentOrgId: string) {
      try {
        setLoading(true);
        setError("");

        const [org, brandList] = await Promise.all([
          getOrganization(currentOrgId),
          listBrands(currentOrgId),
        ]);

        if (!cancelled) {
          setOrganization(org);
          setBrands(brandList);
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load dashboard data.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadDashboard(orgId);

    return () => {
      cancelled = true;
    };
  }, [orgId]);

  const filteredBrands = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return brands;

    return brands.filter((brand: Brand) =>
      brand.name.toLowerCase().includes(query)
    );
  }, [brands, search]);

  const activeGenomes = useMemo(
    () =>
      brands.filter((brand: Brand) =>
        Boolean(brand.active_genome_version_id)
      ).length,
    [brands]
  );

  const activePolicies = useMemo(
    () =>
      brands.filter((brand: Brand) =>
        Boolean(brand.active_policy_version_id)
      ).length,
    [brands]
  );

  const policyAlerts = Math.max(brands.length - activePolicies, 0);

  async function handleCreateBrand() {
    const parsed = brandSchema.safeParse({
      name: brandName.trim(),
    });

    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || "Invalid brand name.");
      return;
    }

    if (!orgId) {
      setError("Organization not found. Please sign in again.");
      return;
    }

    try {
      setCreating(true);
      setError("");

      const workspace = await createWorkspace(
        orgId,
        `${parsed.data.name} Workspace`
      );

      const brand = await createBrand(
        workspace.id,
        parsed.data.name
      );

      setBrands((current) => [...current, brand]);
      setBrandName("");
      setIsCreateOpen(false);
    } catch {
      setError("Unable to create the brand. Please try again.");
    } finally {
      setCreating(false);
    }
  }

  function openBrand(brand: Brand) {
    window.location.href = `/brands/${brand.id}`;
  }

  if (!orgId) {
    return (
      <div className="min-h-screen bg-[#faf9ff] p-6 md:p-10">
        <div className="mx-auto flex min-h-[80vh] max-w-5xl items-center justify-center">
          <Card className="w-full max-w-xl border-violet-100 bg-white shadow-lg">
            <CardContent className="p-8 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100">
                <Sparkles className="h-7 w-7 text-violet-600" />
              </div>

              <h1 className="mt-5 text-2xl font-semibold text-slate-900">
                Welcome to BrandGuard AI
              </h1>

              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
                Create or select an organization to start evaluating your
                brand identity with evidence-driven intelligence.
              </p>

              <Button
                className="mt-6 bg-violet-600 text-white hover:bg-violet-700"
                onClick={() => {
                  window.location.href = "/signup";
                }}
              >
                Get started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#faf9ff]">
      <main className="mx-auto max-w-7xl px-5 py-7 md:px-8 md:py-9">
        <section className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-100">
                <Sparkles className="h-5 w-5 text-violet-600" />
              </div>

              <span className="text-sm font-semibold text-violet-600">
                BrandGuard AI
              </span>
            </div>

            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-900 md:text-4xl">
              Brand intelligence
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              Manage your brands, monitor their identity foundations, and
              prepare them for evidence-based content evaluation.
            </p>

            {organization?.name && (
              <p className="mt-2 text-xs font-medium text-slate-400">
                Organization: {organization.name}
              </p>
            )}
          </div>

          <Button
            onClick={() => {
              setError("");
              setBrandName("");
              setIsCreateOpen(true);
            }}
            className="bg-violet-600 text-white shadow-sm hover:bg-violet-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            New brand
          </Button>
        </section>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {loading ? (
            <>
              {[1, 2, 3, 4].map((item) => (
                <Card key={item} className="border-slate-100 bg-white">
                  <CardContent className="p-5">
                    <Skeleton className="h-5 w-28" />
                    <Skeleton className="mt-3 h-9 w-16" />
                    <Skeleton className="mt-2 h-4 w-36" />
                  </CardContent>
                </Card>
              ))}
            </>
          ) : (
            <>
              <MetricCard
                title="Total brands"
                value={brands.length}
                subtitle="Across this organization"
                icon={Activity}
                variant="lavender"
              />

              <MetricCard
                title="Active genomes"
                value={activeGenomes}
                subtitle="Brand identity foundations"
                icon={GitBranch}
                variant="green"
              />

              <MetricCard
                title="Active policies"
                value={activePolicies}
                subtitle="Governance rules configured"
                icon={ShieldCheck}
                variant="blue"
              />

              <MetricCard
                title="Needs attention"
                value={policyAlerts}
                subtitle="Incomplete configuration"
                icon={AlertCircle}
                variant="peach"
              />
            </>
          )}
        </section>

        <section className="mt-10">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Your brands
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Each brand has its own identity foundation and decision
                context.
              </p>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search brands..."
                  className="w-full border-slate-200 bg-white pl-9 sm:w-64"
                />
              </div>

              <div className="flex items-center rounded-lg border border-slate-200 bg-white p-1">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className="h-8 bg-violet-50 text-violet-700"
                >
                  <LayoutGrid className="mr-1.5 h-4 w-4" />
                  Grid
                </Button>

                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="h-8 text-slate-400"
                >
                  List
                </Button>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-5 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="mt-5">
            {loading ? (
              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {[1, 2, 3].map((item) => (
                  <Card key={item} className="border-slate-100 bg-white">
                    <CardContent className="p-6">
                      <Skeleton className="h-11 w-11 rounded-xl" />
                      <Skeleton className="mt-4 h-5 w-40" />
                      <Skeleton className="mt-2 h-4 w-56" />

                      <div className="mt-6 grid grid-cols-2 gap-3">
                        <Skeleton className="h-20 rounded-xl" />
                        <Skeleton className="h-20 rounded-xl" />
                      </div>

                      <Skeleton className="mt-5 h-10 w-full" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : filteredBrands.length > 0 ? (
              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {filteredBrands.map((brand: Brand) => (
                  <BrandCard
                    key={brand.id}
                    brand={brand}
                    onOpen={() => openBrand(brand)}
                  />
                ))}
              </div>
            ) : brands.length === 0 ? (
              <Card className="border-dashed border-violet-200 bg-white">
                <CardContent className="flex flex-col items-center justify-center px-6 py-14 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100">
                    <Plus className="h-6 w-6 text-violet-600" />
                  </div>

                  <h3 className="mt-5 text-lg font-semibold text-slate-900">
                    Create your first brand
                  </h3>

                  <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                    Start by adding a brand. You can then build its Brand
                    Genome and configure the policies used during evaluation.
                  </p>

                  <Button
                    onClick={() => {
                      setError("");
                      setBrandName("");
                      setIsCreateOpen(true);
                    }}
                    className="mt-5 bg-violet-600 hover:bg-violet-700"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Create brand
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-slate-100 bg-white">
                <CardContent className="flex flex-col items-center justify-center px-6 py-14 text-center">
                  <Search className="h-7 w-7 text-slate-300" />

                  <h3 className="mt-4 text-base font-semibold text-slate-900">
                    No brands found
                  </h3>

                  <p className="mt-1 text-sm text-slate-500">
                    Try a different search term.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </section>

        <section className="mt-10">
          <Card className="overflow-hidden border-violet-100 bg-gradient-to-br from-violet-50 via-white to-sky-50 shadow-sm">
            <CardContent className="p-6 md:p-7">
              <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
                <div className="max-w-2xl">
                  <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-violet-700 shadow-sm ring-1 ring-violet-100">
                    <Sparkles className="h-3.5 w-3.5" />
                    Product philosophy
                  </div>

                  <h2 className="mt-4 text-xl font-semibold text-slate-900">
                    Evidence before AI.
                  </h2>

                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    BrandGuard separates evidence extraction from decision
                    making. Specialized workers produce observable evidence,
                    the deterministic decision engine evaluates it, and AI
                    helps explain the result in a clear human-readable way.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 md:min-w-[300px]">
                  <div className="rounded-2xl border border-white bg-white/80 p-4 shadow-sm">
                    <FileText className="h-5 w-5 text-violet-500" />

                    <p className="mt-3 text-sm font-semibold text-slate-800">
                      Traceable
                    </p>

                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Decisions connect back to evidence.
                    </p>
                  </div>

                  <div className="rounded-2xl border border-white bg-white/80 p-4 shadow-sm">
                    <TrendingUp className="h-5 w-5 text-sky-500" />

                    <p className="mt-3 text-sm font-semibold text-slate-800">
                      Measurable
                    </p>

                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Brand alignment becomes observable.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="border-violet-100 bg-white sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl text-slate-900">
              Create a new brand
            </DialogTitle>

            <DialogDescription className="text-slate-500">
              Add a brand to your organization. You can configure its identity
              foundation after creation.
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              void handleCreateBrand();
            }}
            className="space-y-5"
          >
            <div className="space-y-2">
              <Label htmlFor="brand-name">Brand name</Label>

              <Input
                id="brand-name"
                value={brandName}
                onChange={(event) => setBrandName(event.target.value)}
                placeholder="e.g. Nike"
                className="border-slate-200 focus-visible:ring-violet-400"
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsCreateOpen(false);
                  setBrandName("");
                  setError("");
                }}
                disabled={creating}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                disabled={creating}
                className="bg-violet-600 text-white hover:bg-violet-700"
              >
                {creating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Create brand
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}