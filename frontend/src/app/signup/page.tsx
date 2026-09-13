"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Loader2,
  Mail,
  Sparkles,
  Tag,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  createBrand,
  createOrganization,
  createUser,
  createWorkspace,
} from "@/lib/api-client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";

const schema = z.object({
  orgName: z.string().min(1, "Organization name is required"),
  adminEmail: z.string().email("Enter a valid email"),
  brandName: z.string().min(1, "Brand name is required"),
});

type FormValues = z.infer<typeof schema>;

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

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

      const workspace = await createWorkspace(
        org.id,
        "Default Workspace"
      );

      setStep(`Creating brand "${values.brandName}"…`);

      const brand = await createBrand(
        workspace.id,
        values.brandName
      );

      router.push(`/brands/${brand.id}`);
    } catch (err) {
      setStep(null);
      setError((err as Error).message);
    }
  }

  return (
    <main className="min-h-screen bg-[#fbfaff] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl items-center">
        <div className="grid w-full overflow-hidden rounded-3xl border border-[#e9e3f3] bg-white shadow-[0_20px_60px_rgba(91,68,130,0.08)] lg:grid-cols-[0.9fr_1.1fr]">

          {/* Left: Product introduction */}
          <section className="relative hidden overflow-hidden bg-[#f5f0fc] p-10 lg:flex lg:flex-col lg:justify-between xl:p-14">
            <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-[#e7dcf7] opacity-70 blur-3xl" />
            <div className="absolute -bottom-20 -left-20 h-56 w-56 rounded-full bg-[#eee7fa] blur-3xl" />

            <div className="relative">
              <div className="mb-8 flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#7657ca] text-white shadow-sm">
                  <Sparkles className="h-4 w-4" />
                </div>

                <span className="text-sm font-semibold tracking-tight text-[#302547]">
                  BrandGuard AI
                </span>
              </div>

              <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[#8067b5]">
                Brand intelligence platform
              </p>

              <h1 className="max-w-md text-3xl font-semibold leading-tight tracking-tight text-[#292233] xl:text-4xl">
                Build a trusted foundation for your brand.
              </h1>

              <p className="mt-5 max-w-md text-sm leading-6 text-[#6f6879]">
                Create your organization and establish the first brand
                workspace. BrandGuard will use it as the foundation for
                evidence-based brand evaluation.
              </p>
            </div>

            <div className="relative mt-12 space-y-3">
              <div className="rounded-2xl border border-[#e5ddf0] bg-white/70 p-4 backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 rounded-lg bg-[#eee8fa] p-2 text-[#7657ca]">
                    <Building2 className="h-4 w-4" />
                  </div>

                  <div>
                    <p className="text-sm font-medium text-[#342c40]">
                      Organization
                    </p>
                    <p className="mt-1 text-xs leading-5 text-[#7c7487]">
                      Your secure home for brand intelligence.
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-[#e5ddf0] bg-white/70 p-4 backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 rounded-lg bg-[#e9f5ee] p-2 text-[#4f9270]">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>

                  <div>
                    <p className="text-sm font-medium text-[#342c40]">
                      Evidence-first evaluation
                    </p>
                    <p className="mt-1 text-xs leading-5 text-[#7c7487]">
                      Every decision can be traced back to evidence.
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-[#e5ddf0] bg-white/70 p-4 backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 rounded-lg bg-[#f8eee4] p-2 text-[#ad7650]">
                    <Tag className="h-4 w-4" />
                  </div>

                  <div>
                    <p className="text-sm font-medium text-[#342c40]">
                      Brand Genome
                    </p>
                    <p className="mt-1 text-xs leading-5 text-[#7c7487]">
                      Turn your brand identity into a structured source of
                      truth.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Right: Signup form */}
          <section className="flex items-center p-6 sm:p-10 lg:p-12 xl:p-14">
            <div className="mx-auto w-full max-w-lg">

              {/* Mobile brand */}
              <div className="mb-8 flex items-center gap-2 lg:hidden">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#7657ca] text-white">
                  <Sparkles className="h-4 w-4" />
                </div>

                <span className="text-sm font-semibold text-[#302547]">
                  BrandGuard AI
                </span>
              </div>

              <div className="mb-8">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#8067b5]">
                  Get started
                </p>

                <h2 className="text-2xl font-semibold tracking-tight text-[#292233] sm:text-3xl">
                  Create your organization
                </h2>

                <p className="mt-2 max-w-md text-sm leading-6 text-[#756d80]">
                  Set up your organization, admin account, workspace, and
                  first brand in one step.
                </p>
              </div>

              <form
                onSubmit={handleSubmit(onSubmit)}
                className="space-y-5"
              >
                {/* Organization */}
                <div>
                  <Label
                    htmlFor="orgName"
                    className="text-sm font-medium text-[#3b3445]"
                  >
                    Organization name
                  </Label>

                  <div className="relative mt-2">
                    <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9a91a5]" />

                    <Input
                      id="orgName"
                      placeholder="Acme Inc."
                      {...register("orgName")}
                      className="h-11 rounded-xl border-[#e4deeb] bg-[#fdfcff] pl-10 shadow-none transition focus:border-[#b8a3df] focus:ring-[#e8def7]"
                    />
                  </div>

                  {errors.orgName && (
                    <p className="mt-1.5 text-xs text-misaligned">
                      {errors.orgName.message}
                    </p>
                  )}
                </div>

                {/* Email */}
                <div>
                  <Label
                    htmlFor="adminEmail"
                    className="text-sm font-medium text-[#3b3445]"
                  >
                    Admin email
                  </Label>

                  <div className="relative mt-2">
                    <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9a91a5]" />

                    <Input
                      id="adminEmail"
                      type="email"
                      placeholder="you@company.com"
                      {...register("adminEmail")}
                      className="h-11 rounded-xl border-[#e4deeb] bg-[#fdfcff] pl-10 shadow-none transition focus:border-[#b8a3df] focus:ring-[#e8def7]"
                    />
                  </div>

                  {errors.adminEmail && (
                    <p className="mt-1.5 text-xs text-misaligned">
                      {errors.adminEmail.message}
                    </p>
                  )}
                </div>

                {/* Brand */}
                <div>
                  <Label
                    htmlFor="brandName"
                    className="text-sm font-medium text-[#3b3445]"
                  >
                    First brand
                  </Label>

                  <div className="relative mt-2">
                    <Tag className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9a91a5]" />

                    <Input
                      id="brandName"
                      placeholder="e.g. Nike"
                      {...register("brandName")}
                      className="h-11 rounded-xl border-[#e4deeb] bg-[#fdfcff] pl-10 shadow-none transition focus:border-[#b8a3df] focus:ring-[#e8def7]"
                    />
                  </div>

                  {errors.brandName && (
                    <p className="mt-1.5 text-xs text-misaligned">
                      {errors.brandName.message}
                    </p>
                  )}
                </div>

                {/* Error */}
                {error && (
                  <Alert variant="destructive" className="rounded-xl">
                    <AlertTitle>
                      Couldn&apos;t create your organization
                    </AlertTitle>

                    <AlertDescription>
                      {error}
                    </AlertDescription>
                  </Alert>
                )}

                {/* Submit */}
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  size="lg"
                  className="mt-2 h-11 w-full rounded-xl bg-[#7657ca] text-white shadow-[0_8px_20px_rgba(118,87,202,0.18)] transition hover:bg-[#694bbd]"
                >
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <ArrowRight className="h-4 w-4" />
                  )}

                  {step ?? "Create organization"}
                </Button>

                <p className="pt-2 text-center text-sm text-[#7b7383]">
                  Already have an organization?{" "}
                  <a
                    href="/login"
                    className="font-medium text-[#7657ca] transition hover:text-[#6244b0]"
                  >
                    Log in
                  </a>
                </p>
              </form>

              <p className="mt-8 text-center text-[11px] leading-5 text-[#aaa3b0]">
                By continuing, you&apos;ll create an organization workspace
                and its initial brand configuration.
              </p>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}