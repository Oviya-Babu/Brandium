import {
  ArrowRight,
  FileSearch,
  GitBranch,
  Lock,
  ScanSearch,
  ServerCog,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const PRINCIPLES = [
  "Deterministic scoring",
  "Full evidence trace",
  "Multi-tenant isolation",
  "Self-hosted LLM by default",
];

const STEPS = [
  {
    icon: GitBranch,
    title: "Compile your Brand Genome",
    body: "Ingest guideline documents, design systems, and campaign history. BrandGuard extracts Assertions into versioned, human-approved Categories and Components — your single source of truth.",
  },
  {
    icon: UploadCloud,
    title: "Submit content for analysis",
    body: "Upload any text or image asset. It's queued against your Brand's active Genome and Policy — nothing is scored without both in place.",
  },
  {
    icon: ScanSearch,
    title: "Workers extract Evidence",
    body: "Text and image workers produce Observations against every applicable Assertion, fused into Evidence — not opinions, structured judgments with a confidence score.",
  },
  {
    icon: ShieldCheck,
    title: "The Decision Engine scores it",
    body: "A deterministic function — not the LLM — aggregates Evidence into a Brand Distinctiveness Index, a verdict, and prioritized recommendations, drillable back to source.",
  },
];

const FEATURES = [
  {
    icon: GitBranch,
    title: "Brand Genome",
    body: "Guidelines compiled into versioned, human-approved Categories, Components, and Assertions.",
  },
  {
    icon: FileSearch,
    title: "Evidence-first analysis",
    body: "Every verdict traces back to the exact Observation and source asset that produced it.",
  },
  {
    icon: ServerCog,
    title: "Deterministic Decision Engine",
    body: "Reproducible scoring — the same Evidence always produces the same Brand Distinctiveness Index.",
  },
  {
    icon: Lock,
    title: "Tenant isolation by default",
    body: "Row-level security scopes every query to your organization — enforced at the database, not just the API.",
  },
  {
    icon: Sparkles,
    title: "Local-first LLM",
    body: "Runs against a self-hosted model by default, with an automatic, logged fallback — never a hardcoded key.",
  },
  {
    icon: ShieldCheck,
    title: "Human sign-off, always",
    body: "Genomes and Policies activate only via an explicit, audited action from an authenticated Brand Administrator.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <header className="sticky top-0 z-30 border-b border-border/60 bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <ShieldCheck className="h-4 w-4" />
            </div>
            BrandGuard AI
          </div>
          <nav className="hidden items-center gap-8 text-sm text-muted-foreground sm:flex">
            <a href="#how-it-works" className="hover:text-foreground">How it works</a>
            <a href="#platform" className="hover:text-foreground">Platform</a>
          </nav>
          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <a href="/login">Log in</a>
            </Button>
            <Button asChild>
              <a href="/signup">
                Sign up <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[560px] opacity-40"
          style={{
            background:
              "radial-gradient(600px circle at 20% 0%, color-mix(in oklch, var(--primary), transparent 85%), transparent)",
          }}
        />
        <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-2 lg:items-center lg:py-28">
          <div>
            <span className="mb-6 inline-flex items-center rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              Enterprise Brand Decision Intelligence
            </span>
            <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
              Every asset, evaluated against your brand — with evidence, not opinion.
            </h1>
            <p className="mt-6 max-w-xl text-lg text-muted-foreground">
              BrandGuard compiles your guidelines into a structured Brand Genome, then scores every
              piece of content against it with a deterministic Decision Engine — every score
              traceable down to the exact evidence that produced it.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">
              <Button size="lg" asChild>
                <a href="/signup">
                  Get started <ArrowRight className="h-4 w-4" />
                </a>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <a href="/login">I have an account</a>
              </Button>
            </div>
            <dl className="mt-14 grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-4">
              {PRINCIPLES.map((p) => (
                <div key={p} className="border-t border-border pt-3">
                  <dt className="text-xs text-muted-foreground">{p}</dt>
                </div>
              ))}
            </dl>
          </div>

          {/* Abstract product preview — an original composition, not a
              literal screenshot, illustrating the BDI gauge + pipeline
              concept the real Analysis page implements. */}
          <div className="relative">
            <div className="rounded-2xl border border-border bg-card p-5 shadow-2xl shadow-black/10 ring-1 ring-foreground/5">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">Brand Distinctiveness Index</span>
                <span className="flex items-center gap-1 rounded-full bg-aligned/10 px-2 py-0.5 text-[11px] font-medium text-aligned">
                  <span className="h-1.5 w-1.5 rounded-full bg-aligned" /> Compliant
                </span>
              </div>
              <div className="flex items-end gap-2">
                <span className="text-5xl font-semibold text-foreground">87.4</span>
                <span className="mb-1.5 text-sm text-aligned">+12.6</span>
              </div>
              <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                <div className="h-full w-[87%] rounded-full bg-gradient-to-r from-primary to-aligned" />
              </div>

              <div className="mt-6 flex items-center gap-1.5">
                {["Applicability", "Planning", "Workers", "Fusion", "Decision"].map((stage, i) => (
                  <div key={stage} className="flex flex-1 items-center gap-1.5">
                    <div
                      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-medium ${
                        i < 4 ? "bg-aligned/15 text-aligned" : "bg-primary/15 text-primary"
                      }`}
                    >
                      {i + 1}
                    </div>
                    {i < 4 && <div className="h-px flex-1 bg-aligned/30" />}
                  </div>
                ))}
              </div>

              <div className="mt-6 space-y-2">
                {[
                  { label: "Visual Identity / Logo Usage", pct: 95, tone: "aligned" as const },
                  { label: "Tone Attributes", pct: 78, tone: "partial" as const },
                  { label: "Prohibited Language", pct: 34, tone: "misaligned" as const },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between rounded-lg bg-muted/60 px-3 py-2 text-xs">
                    <span className="text-foreground/80">{row.label}</span>
                    <span
                      className={`font-medium ${
                        row.tone === "aligned" ? "text-aligned" : row.tone === "partial" ? "text-partial" : "text-misaligned"
                      }`}
                    >
                      {row.pct}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="absolute -bottom-6 -right-6 -z-10 h-40 w-40 rounded-full bg-primary/20 blur-3xl" />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="border-t border-border bg-muted/30 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-sm font-medium uppercase tracking-wide text-primary">How it works</h2>
          <p className="mt-2 max-w-2xl text-2xl font-semibold text-foreground sm:text-3xl">
            From brand guidelines to a defensible, evidence-backed verdict.
          </p>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step, i) => (
              <div key={step.title} className="relative">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-card text-primary">
                  <step.icon className="h-5 w-5" />
                </div>
                <span className="absolute right-0 top-0 font-mono text-xs text-muted-foreground">0{i + 1}</span>
                <h3 className="mb-2 font-medium text-foreground">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature grid */}
      <section id="platform" className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-sm font-medium uppercase tracking-wide text-primary">Platform</h2>
          <p className="mt-2 max-w-2xl text-2xl font-semibold text-foreground sm:text-3xl">
            Built for governance, not just generation.
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="rounded-xl border border-border bg-card p-6">
                <f.icon className="mb-4 h-5 w-5 text-primary" />
                <h3 className="mb-2 font-medium text-foreground">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border py-20">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-6 text-center">
          <h2 className="text-2xl font-semibold text-foreground sm:text-3xl">
            Compile your first Brand Genome in minutes.
          </h2>
          <Button size="lg" asChild>
            <a href="/signup">
              Get started <ArrowRight className="h-4 w-4" />
            </a>
          </Button>
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 text-xs text-muted-foreground sm:flex-row">
          <span>© {new Date().getFullYear()} BrandGuard AI</span>
          <span>Enterprise Brand Decision Intelligence Platform</span>
        </div>
      </footer>
    </main>
  );
}
