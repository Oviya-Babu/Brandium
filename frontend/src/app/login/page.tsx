"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { lookupSession } from "@/lib/api-client";
import { AuthLayout } from "@/components/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const schema = z.object({ email: z.string().email("Enter a valid email") });
type FormValues = z.infer<typeof schema>;

/**
 * Real, not simulated: resolves the actual User/Organization row via
 * `GET /session/lookup` (see that endpoint's docstring). There is no
 * password field because there is no credential storage yet — Phase C
 * adds real JWT authentication on top of this same identity model.
 * This page intentionally does not pretend otherwise.
 */
export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setError(null);
    try {
      const session = await lookupSession(values.email);
      localStorage.setItem("brandium_org_id", session.org_id);
      localStorage.setItem("brandium_user_id", session.user_id);
      localStorage.setItem("brandium_user_email", session.email);
      router.push("/dashboard");
    } catch {
      setError("No account found for this email. Check the address, or create a new organization.");
    }
  }

  return (
    <AuthLayout title="Log in" subtitle="Resume your organization's workspace.">
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <div>
          <Label htmlFor="email">Work email</Label>
          <Input id="email" type="email" placeholder="you@company.com" {...register("email")} className="mt-1.5" />
          {errors.email && <p className="mt-1 text-xs text-misaligned">{errors.email.message}</p>}
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertTitle>Couldn&apos;t log in</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Button type="submit" disabled={isSubmitting} size="lg" className="mt-2">
          {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          Continue
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          New to BrandGuard?{" "}
          <a href="/signup" className="font-medium text-primary hover:text-primary/80">
            Create an organization
          </a>
        </p>
      </form>
    </AuthLayout>
  );
}
