"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  Tag,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { lookupSession } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";

const schema = z.object({
  email: z.string().email("Enter a valid email"),
});

type FormValues = z.infer<typeof schema>;

const POINTS = [
  {
    title: "Evidence-first evaluation",
    description: "Every decision can be traced back to measurable evidence.",
    icon: CheckCircle2,
    iconClass: "bg-emerald-50 text-emerald-600",
  },
  {
    title: "Brand Genome",
    description: "Keep your brand identity structured and version-controlled.",
    icon: Tag,
    iconClass: "bg-orange-50 text-orange-600",
  },
  {
    title: "Explainable decisions",
    description: "Understand why content passes, fails, or needs review.",
    icon: ShieldCheck,
    iconClass: "bg-violet-50 text-violet-600",
  },
];

export default function LoginPage() {
  const router = useRouter();
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
      const session = await lookupSession(values.email);

      localStorage.setItem("brandium_org_id", session.org_id);
      localStorage.setItem("brandium_user_id", session.user_id);
      localStorage.setItem("brandium_user_email", session.email);

      router.push("/dashboard");
    } catch {
      setError(
        "No account found for this email. Check the address, or create a new organization.",
      );
    }
  }

  return (
    <main className="min-h-screen bg-[#faf9ff] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-[1250px] overflow-hidden rounded-[26px] border border-[#e6def2] bg-white shadow-[0_24px_70px_rgba(91,70,135,0.08)] lg:grid-cols-2">
        {/* Left brand panel */}
        <section className="relative overflow-hidden bg-[#f4effc] px-8 py-10 sm:px-12 lg:px-16 lg:py-14">
          <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-[#e5d8fa] opacity-50 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-32 -left-20 h-80 w-80 rounded-full bg-white opacity-70 blur-3xl" />

          <div className="relative flex h-full flex-col">
            {/* Brand */}
            <Link
              href="/"
              className="flex items-center gap-2.5 text-sm font-semibold text-[#17152a]"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7654cf] text-white shadow-[0_5px_12px_rgba(118,84,207,0.25)]">
                <ShieldCheck className="h-5 w-5" />
              </span>

              <span className="text-[15px]">BrandGuard AI</span>
            </Link>

            {/* Main message */}
            <div className="mt-14 max-w-[500px] lg:mt-16">
              <p className="text-[12px] font-semibold uppercase tracking-[0.22em] text-[#7654cf]">
                Brand intelligence platform
              </p>

              <h2 className="mt-5 text-[36px] font-semibold leading-[1.08] tracking-[-0.035em] text-[#17152a] sm:text-[40px]">
                Welcome back to your
                <br />
                brand intelligence
                <br />
                workspace.
              </h2>

              <p className="mt-7 max-w-[470px] text-[15px] leading-7 text-[#6f6680]">
                Continue evaluating AI-generated content against your brand
                identity with evidence-based decisions and explainable
                results.
              </p>
            </div>

            {/* Feature cards */}
            <div className="mt-auto space-y-3 pt-10">
              {POINTS.map((point) => {
                const Icon = point.icon;

                return (
                  <div
                    key={point.title}
                    className="flex items-center gap-4 rounded-2xl border border-[#e5dced] bg-white/75 px-4 py-4 backdrop-blur-sm"
                  >
                    <div
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${point.iconClass}`}
                    >
                      <Icon className="h-[17px] w-[17px]" />
                    </div>

                    <div>
                      <p className="text-[14px] font-semibold text-[#40394d]">
                        {point.title}
                      </p>

                      <p className="mt-1 text-[12px] leading-5 text-[#8a8195]">
                        {point.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Right login panel */}
        <section className="flex items-center bg-white px-8 py-12 sm:px-12 lg:px-16">
          <div className="w-full max-w-[560px]">
            <p className="text-[12px] font-semibold uppercase tracking-[0.22em] text-[#7654cf]">
              Welcome back
            </p>

            <h1 className="mt-4 text-[30px] font-semibold tracking-[-0.03em] text-[#17152a] sm:text-[32px]">
              Continue to your workspace
            </h1>

            <p className="mt-3 max-w-[480px] text-[14px] leading-6 text-[#756d7e]">
              Enter your work email to access your organization and continue
              where you left off.
            </p>

            <form
              onSubmit={handleSubmit(onSubmit)}
              className="mt-10 flex flex-col gap-6"
            >
              {/* Email */}
              <div>
                <Label
                  htmlFor="email"
                  className="text-[14px] font-medium text-[#211d29]"
                >
                  Work email
                </Label>

                <div className="relative mt-2.5">
                  <Building2 className="pointer-events-none absolute left-4 top-1/2 h-[17px] w-[17px] -translate-y-1/2 text-[#a49aaa]" />

                  <Input
                    id="email"
                    type="email"
                    placeholder="you@company.com"
                    autoComplete="email"
                    {...register("email")}
                    className="h-12 rounded-xl border-[#e2dce7] bg-white pl-11 text-[14px] shadow-none placeholder:text-[#aaa2b0] focus:border-[#8b6ad8] focus:ring-[#dcd0f5]"
                  />
                </div>

                {errors.email && (
                  <p className="mt-2 text-xs text-misaligned">
                    {errors.email.message}
                  </p>
                )}
              </div>

              {/* Error */}
              {error && (
                <Alert variant="destructive" className="rounded-xl">
                  <AlertTitle>Couldn&apos;t log in</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Submit */}
              <Button
                type="submit"
                disabled={isSubmitting}
                size="lg"
                className="h-12 rounded-xl bg-[#7654cf] text-[14px] font-semibold text-white shadow-[0_8px_20px_rgba(118,84,207,0.22)] transition-all hover:bg-[#6848bf]"
              >
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowRight className="h-4 w-4" />
                )}

                Continue to workspace
              </Button>

              {/* Signup link */}
              <p className="text-center text-[14px] text-[#82798b]">
                New to BrandGuard?{" "}
                <Link
                  href="/signup"
                  className="font-semibold text-[#7654cf] hover:text-[#6243b8]"
                >
                  Create an organization
                </Link>
              </p>

              {/* Footer note */}
              <p className="pt-4 text-center text-[11px] leading-5 text-[#aaa2b0]">
                Access your organization workspace and continue your brand
                evaluation workflow.
              </p>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}