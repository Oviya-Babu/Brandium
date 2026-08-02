"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { createBrand, createOrganization, createUser, createWorkspace } from "@/lib/api-client";
import { AuthLayout } from "@/components/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const schema = z.object({
  orgName: z.string().min(1, "Required"),
  adminEmail: z.string().email("Enter a valid email"),
  brandName: z.string().min(1, "Required"),
});
type FormValues = z.infer<typeof schema>;

/**
 * Real signup: creates an Organization, bootstrap admin User (the
 * OrganizationAdministrator + BrandAdministrator exception documented
 * in `api/routers/users.py`), a default Workspace, and the first Brand
 * — the same four calls the old Dashboard onboarding form made, now a
 * dedicated page with its own IA instead of living inside the app home.
 */
export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setError(null);
    try {
      setStep("Creating organization…");
      const org = await createOrganization(values.orgName);
      localStorage.setItem("brandium_org_id", org.id);

      setStep("Creating your account…");
      const user = await createUser(org.id, values.adminEmail);
      localStorage.setItem("brandium_user_id", user.id);
      localStorage.setItem("brandium_user_email", values.adminEmail);

      setStep("Creating workspace…");
      const workspace = await createWorkspace(org.id, "Default Workspace");

      setStep(`Creating brand "${values.brandName}"…`);
      const brand = await createBrand(workspace.id, values.brandName);

      router.push(`/brands/${brand.id}`);
    } catch (err) {
      setStep(null);
      setError((err as Error).message);
    }
  }

  return (
    <AuthLayout title="Create your organization" subtitle="Sets up your organization, admin account, and first brand.">
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div>
          <Label htmlFor="orgName">Organization name</Label>
          <Input id="orgName" placeholder="Acme Inc." {...register("orgName")} className="mt-1.5" />
          {errors.orgName && <p className="mt-1 text-xs text-misaligned">{errors.orgName.message}</p>}
        </div>
        <div>
          <Label htmlFor="adminEmail">Admin email</Label>
          <Input id="adminEmail" type="email" placeholder="you@company.com" {...register("adminEmail")} className="mt-1.5" />
          {errors.adminEmail && <p className="mt-1 text-xs text-misaligned">{errors.adminEmail.message}</p>}
        </div>
        <div>
          <Label htmlFor="brandName">First brand</Label>
          <Input id="brandName" placeholder="e.g. Red Bull" {...register("brandName")} className="mt-1.5" />
          {errors.brandName && <p className="mt-1 text-xs text-misaligned">{errors.brandName.message}</p>}
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertTitle>Couldn&apos;t create your organization</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Button type="submit" disabled={isSubmitting} size="lg" className="mt-2">
          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          {step ?? "Create organization"}
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          Already have an organization?{" "}
          <a href="/login" className="font-medium text-primary hover:text-primary/80">
            Log in
          </a>
        </p>
      </form>
    </AuthLayout>
  );
}
