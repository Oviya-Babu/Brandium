"use client";

import { use, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, ScrollText, Sparkles } from "lucide-react";
import { activatePolicy, createPolicy, getBrand, getPolicy } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";

const DEFAULT_RULES = {
  category_weights: {
    visual_identity: 0.2,
    verbal_identity: 0.2,
    messaging_positioning: 0.2,
    values_mission: 0.15,
    compliance_legal: 0.15,
    accessibility: 0.1,
  },
  component_weights: {},
  assertion_weights: {},
  critical_rules: [],
  verdict_thresholds: [
    { min_score: 0, max_score: 59.999999, verdict: "Non-Compliant" },
    { min_score: 59.999999, max_score: 100, verdict: "Compliant" },
  ],
  improvement_threshold: 0.8,
};

export default function PoliciesPage({ params }: { params: Promise<{ brandId: string }> }) {
  const { brandId } = use(params);
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const brandQuery = useQuery({ queryKey: ["brand", brandId], queryFn: () => getBrand(brandId) });
  const activePolicyId = brandQuery.data?.active_policy_version_id ?? null;

  const policyQuery = useQuery({
    queryKey: ["policy", brandId, activePolicyId],
    queryFn: () => getPolicy(brandId, activePolicyId!),
    enabled: !!activePolicyId,
  });

  async function handleCreateDefault() {
    setBusy(true);
    setStatus("Creating a default Policy (uniform category weights)…");
    try {
      const policy = await createPolicy(brandId, DEFAULT_RULES);
      setStatus("Activating…");
      await activatePolicy(brandId, policy.id);
      await queryClient.invalidateQueries({ queryKey: ["brand", brandId] });
      setStatus("Policy created and activated.");
    } finally {
      setBusy(false);
    }
  }

  const rules = policyQuery.data?.rules;

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Policies</h1>
          <p className="text-sm text-muted-foreground">
            Category weights, verdict thresholds, and Critical Rules the Decision Engine scores against.
          </p>
        </div>
        {!activePolicyId && (
          <Button onClick={handleCreateDefault} disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Create default policy
          </Button>
        )}
      </div>

      {status && <p className="mb-4 text-sm text-muted-foreground">{status}</p>}

      {!activePolicyId && !busy && (
        <Card className="border-dashed">
          <CardContent>
            <div className="flex flex-col items-center gap-3 py-14 text-center">
              <ScrollText className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No active policy for this brand yet.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {activePolicyId && policyQuery.isLoading && <Skeleton className="h-64 w-full" />}

      {rules && (
        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Active policy
                <Badge variant="aligned">
                  <CheckCircle2 className="h-3 w-3" /> v{policyQuery.data?.version_number}
                </Badge>
              </CardTitle>
              <CardDescription>Category weights determine each category&apos;s share of the Brand Distinctiveness Index.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-4">
                {Object.entries(rules.category_weights).map(([category, weight]) => (
                  <div key={category}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span className="text-foreground/80">{category.replaceAll("_", " ")}</span>
                      <span className="text-muted-foreground">{Math.round(weight * 100)}%</span>
                    </div>
                    <Progress value={weight * 100} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 sm:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Verdict thresholds</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2">
                  {rules.verdict_thresholds.map((t) => (
                    <div key={t.verdict} className="flex items-center justify-between rounded-lg bg-muted px-3 py-2 text-sm">
                      <span className="text-foreground/80">{t.verdict}</span>
                      <span className="font-mono text-xs text-muted-foreground">
                        {t.min_score.toFixed(0)}–{t.max_score.toFixed(0)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Critical Rules</CardTitle>
                <CardDescription>Instant overrides regardless of the weighted score.</CardDescription>
              </CardHeader>
              <CardContent>
                {rules.critical_rules.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No Critical Rules configured.</p>
                ) : (
                  <p className="text-sm text-foreground/80">{rules.critical_rules.length} rule(s) configured.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
