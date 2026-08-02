import Link from "next/link";
import { CheckCircle2, ShieldCheck } from "lucide-react";

const POINTS = [
  "Guidelines compiled into a versioned, human-approved Brand Genome",
  "Evidence-first scoring — the Decision Engine, not the LLM, computes the verdict",
  "Every score drillable down to the exact source asset behind it",
];

/**
 * Shared split-screen shell for Login/Signup — the enterprise SaaS
 * auth-page convention (Vercel, Linear, GitHub Enterprise): a branded
 * story panel on one side, the actual form on the other, no persistent
 * nav chrome around either.
 */
export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-foreground p-10 text-background lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 15% 15%, color-mix(in oklch, var(--primary), transparent 20%), transparent 45%)",
          }}
        />
        <Link href="/" className="relative flex items-center gap-2 text-sm font-semibold">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <ShieldCheck className="h-4 w-4" />
          </div>
          BrandGuard AI
        </Link>
        <div className="relative">
          <p className="text-3xl font-semibold leading-tight">
            Every asset, evaluated against your brand — with evidence, not opinion.
          </p>
          <ul className="mt-8 flex flex-col gap-4">
            {POINTS.map((point) => (
              <li key={point} className="flex items-start gap-3 text-sm text-background/70">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                {point}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-background/50">Enterprise Brand Decision Intelligence Platform</p>
      </div>

      <div className="flex flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <Link href="/" className="mb-8 flex items-center gap-2 text-sm font-semibold text-foreground lg:hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <ShieldCheck className="h-4 w-4" />
            </div>
            BrandGuard AI
          </Link>
          <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </main>
  );
}
