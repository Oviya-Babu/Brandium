"use client";

import Link from "next/link";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  FileSearch,
  GitBranch,
  Lock,
  ScanSearch,
  ServerCog,
  ShieldCheck,
  Sparkles,
  Upload,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";

const SIGNALS = [
  {
    name: "Brand Voice",
    value: "92%",
    status: "Strong match",
  },
  {
    name: "Visual Identity",
    value: "89%",
    status: "Strong match",
  },
  {
    name: "Messaging",
    value: "86%",
    status: "Aligned",
  },
  {
    name: "Distinctiveness",
    value: "84%",
    status: "Above threshold",
  },
];

const STEPS = [
  {
    number: "01",
    icon: GitBranch,
    title: "Build the Brand Genome",
    description:
      "Turn brand identity, voice, visual language, and policies into structured evidence.",
  },
  {
    number: "02",
    icon: Upload,
    title: "Submit AI content",
    description:
      "Bring generated text, images, or short-form content into the analysis pipeline.",
  },
  {
    number: "03",
    icon: ScanSearch,
    title: "Extract evidence",
    description:
      "Specialized workers inspect the asset and create measurable evidence signals.",
  },
  {
    number: "04",
    icon: ShieldCheck,
    title: "Make the decision",
    description:
      "The deterministic engine evaluates evidence and produces an explainable verdict.",
  },
];

const FEATURES = [
  {
    icon: GitBranch,
    title: "Brand Genome",
    description:
      "A structured and version-controlled source of truth for brand identity.",
  },
  {
    icon: FileSearch,
    title: "Evidence-first analysis",
    description:
      "Every decision is grounded in observable evidence rather than opaque model opinions.",
  },
  {
    icon: ShieldCheck,
    title: "Deterministic Decision Engine",
    description:
      "Consistent scoring and policy evaluation across every analyzed asset.",
  },
  {
    icon: Lock,
    title: "Tenant isolation",
    description:
      "Organizations, brands, assets, and intelligence stay securely separated.",
  },
  {
    icon: ServerCog,
    title: "Local-first LLM",
    description:
      "Use an organization-controlled LLM for explanations and recommendations.",
  },
  {
    icon: CheckCircle2,
    title: "Human sign-off",
    description:
      "AI supports the workflow while people retain the final decision.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#fbfaff] text-slate-900">
      {/* Background atmosphere */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-[600px] w-[600px] rounded-full bg-violet-200/30 blur-[110px]" />
        <div className="absolute right-[-220px] top-[180px] h-[600px] w-[600px] rounded-full bg-blue-200/20 blur-[120px]" />
        <div className="absolute bottom-[-250px] left-[30%] h-[500px] w-[500px] rounded-full bg-fuchsia-200/15 blur-[120px]" />
      </div>

      {/* HEADER */}
      <header className="sticky top-0 z-50 border-b border-slate-200/60 bg-white/75 backdrop-blur-2xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-100 text-violet-700">
              <Sparkles className="h-4 w-4" />
            </div>

            <div>
              <p className="text-sm font-bold tracking-tight text-slate-950">
                BrandGuard AI
              </p>
              <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                Decision Intelligence
              </p>
            </div>
          </Link>

          <nav className="hidden items-center gap-8 md:flex">
            <a
              href="#how-it-works"
              className="text-sm font-medium text-slate-500 transition hover:text-violet-700"
            >
              How it works
            </a>

            <a
              href="#platform"
              className="text-sm font-medium text-slate-500 transition hover:text-violet-700"
            >
              Platform
            </a>

            <a
              href="#principles"
              className="text-sm font-medium text-slate-500 transition hover:text-violet-700"
            >
              Why BrandGuard
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button
                variant="ghost"
                className="hidden text-slate-600 hover:bg-violet-50 hover:text-violet-700 sm:inline-flex"
              >
                Log in
              </Button>
            </Link>

            <Link href="/signup">
              <Button className="rounded-xl bg-slate-950 px-5 shadow-lg shadow-slate-200 hover:bg-slate-800">
                Get started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-6 pb-20 pt-16 lg:px-8 lg:pb-28 lg:pt-24">
          <div className="grid items-center gap-14 lg:grid-cols-[0.82fr_1.18fr]">
            {/* LEFT */}
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/80 px-4 py-2 shadow-sm">
                <span className="flex h-2 w-2 rounded-full bg-violet-500" />
                <span className="text-xs font-bold text-violet-700">
                  Enterprise Brand Decision Intelligence
                </span>
              </div>

              <h1 className="max-w-xl text-5xl font-bold leading-[1.02] tracking-[-0.045em] text-slate-950 sm:text-6xl">
                Is this content
                <span className="block text-violet-600">
                  really your brand?
                </span>
              </h1>

              <p className="mt-7 max-w-lg text-base leading-7 text-slate-600 sm:text-lg">
                BrandGuard AI validates whether AI-generated content is
                distinctively yours — using evidence, deterministic scoring,
                and explainable decisions.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link href="/signup">
                  <Button
                    size="lg"
                    className="w-full rounded-xl bg-violet-600 px-7 shadow-xl shadow-violet-200 transition hover:-translate-y-0.5 hover:bg-violet-700 sm:w-auto"
                  >
                    Start building
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>

                <a href="#how-it-works">
                  <Button
                    size="lg"
                    variant="outline"
                    className="w-full rounded-xl border-slate-200 bg-white/80 px-7 hover:bg-violet-50 sm:w-auto"
                  >
                    Explore the system
                  </Button>
                </a>
              </div>

              {/* Small proof row */}
              <div className="mt-9 flex flex-wrap gap-x-5 gap-y-3">
                {[
                  "Evidence-first",
                  "Deterministic",
                  "Human-controlled",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2 text-xs font-medium text-slate-500"
                  >
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            {/* RIGHT PRODUCT EXPERIENCE */}
            <div className="relative">
              {/* floating glow */}
              <div className="absolute -inset-8 rounded-[3rem] bg-violet-300/20 blur-3xl" />

              {/* floating evidence pill */}
              <div className="absolute -left-7 top-16 z-20 hidden rounded-2xl border border-white/80 bg-white/90 p-3 shadow-xl backdrop-blur-xl xl:block">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600">
                    <Check className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                      Decision
                    </p>
                    <p className="text-sm font-bold text-slate-900">
                      Brand aligned
                    </p>
                  </div>
                </div>
              </div>

              {/* floating score */}
              <div className="absolute -right-6 bottom-20 z-20 hidden rounded-2xl border border-white/80 bg-white/90 px-4 py-3 shadow-xl backdrop-blur-xl xl:block">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  BDI score
                </p>
                <div className="mt-1 flex items-end gap-1">
                  <span className="text-2xl font-bold text-violet-700">
                    87.4
                  </span>
                  <span className="mb-1 text-xs text-slate-400">/100</span>
                </div>
              </div>

              {/* MAIN APP WINDOW */}
              <div className="relative rounded-[2rem] border border-white bg-white/80 p-2 shadow-[0_30px_90px_-25px_rgba(76,29,149,0.28)] backdrop-blur-xl">
                <div className="overflow-hidden rounded-[1.6rem] border border-slate-200/80 bg-[#f7f6fb]">
                  {/* fake browser/app bar */}
                  <div className="flex items-center justify-between border-b border-slate-200/80 bg-white/70 px-5 py-3">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
                      <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
                      <span className="h-2.5 w-2.5 rounded-full bg-slate-200" />
                    </div>

                    <div className="rounded-lg bg-slate-100 px-4 py-1.5 text-[9px] font-medium text-slate-400">
                      brandguard / analysis / 2048
                    </div>

                    <Sparkles className="h-3.5 w-3.5 text-violet-400" />
                  </div>

                  <div className="p-5 sm:p-7">
                    {/* title */}
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-violet-500">
                          Brand analysis
                        </p>
                        <h3 className="mt-1 text-lg font-bold text-slate-950">
                          Campaign Asset #2048
                        </h3>
                      </div>

                      <div className="flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        <span className="text-[10px] font-bold text-emerald-700">
                          PASS
                        </span>
                      </div>
                    </div>

                    {/* SCORE + DECISION */}
                    <div className="mt-6 grid gap-4 sm:grid-cols-[1.2fr_0.8fr]">
                      <div className="rounded-2xl border border-violet-100 bg-white p-5">
                        <div className="flex items-center justify-between">
                          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                            Brand Distinctiveness Index
                          </p>
                          <Zap className="h-4 w-4 text-violet-500" />
                        </div>

                        <div className="mt-3 flex items-end gap-2">
                          <span className="text-4xl font-bold tracking-tight text-slate-950">
                            87.4
                          </span>
                          <span className="mb-1.5 text-xs text-slate-400">
                            / 100
                          </span>
                        </div>

                        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                          <div className="h-full w-[87.4%] rounded-full bg-gradient-to-r from-violet-500 to-violet-400" />
                        </div>

                        <div className="mt-2 flex justify-between text-[9px] font-medium text-slate-400">
                          <span>Needs review</span>
                          <span>Strongly distinctive</span>
                        </div>
                      </div>

                      <div className="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-5">
                        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                          Decision
                        </p>

                        <div className="mt-4 flex items-center gap-3">
                          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-emerald-500 shadow-sm">
                            <CheckCircle2 className="h-5 w-5" />
                          </div>

                          <div>
                            <p className="font-bold text-slate-900">Pass</p>
                            <p className="mt-0.5 text-[10px] text-slate-500">
                              Meets brand policy
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* PIPELINE */}
                    <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-5">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-bold text-slate-900">
                            Evidence pipeline
                          </p>
                          <p className="mt-1 text-[10px] text-slate-400">
                            Decision supported by 4 measurable signals
                          </p>
                        </div>

                        <div className="rounded-lg bg-violet-50 px-2.5 py-1 text-[10px] font-bold text-violet-600">
                          LIVE
                        </div>
                      </div>

                      <div className="mt-4 space-y-2">
                        {SIGNALS.map((signal) => (
                          <div
                            key={signal.name}
                            className="group flex items-center justify-between rounded-xl border border-transparent bg-slate-50 px-4 py-3 transition hover:border-violet-100 hover:bg-violet-50/50"
                          >
                            <div className="flex min-w-0 items-center gap-3">
                              <div className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm">
                                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                              </div>

                              <div className="min-w-0">
                                <p className="truncate text-xs font-semibold text-slate-800">
                                  {signal.name}
                                </p>
                                <p className="text-[9px] text-slate-400">
                                  {signal.status}
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center gap-3">
                              <div className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-slate-200 sm:block">
                                <div
                                  className="h-full rounded-full bg-emerald-400"
                                  style={{ width: signal.value }}
                                />
                              </div>

                              <span className="text-xs font-bold text-slate-700">
                                {signal.value}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* EXPLANATION */}
                    <div className="mt-4 flex gap-3 rounded-2xl border border-violet-100 bg-violet-50/70 p-4">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-violet-600 shadow-sm">
                        <Sparkles className="h-3.5 w-3.5" />
                      </div>

                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-violet-600">
                          Explainability
                        </p>
                        <p className="mt-1 text-[10px] leading-5 text-slate-600">
                          Content strongly matches the defined brand voice,
                          visual identity, and messaging policy.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* BRAND STATEMENT */}
          <div className="mt-20 border-t border-slate-200/70 pt-8">
            <div className="grid gap-8 md:grid-cols-3 md:items-center">
              <div className="md:col-span-1">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
                  The problem
                </p>
              </div>

              <div className="md:col-span-2">
                <p className="text-xl font-medium leading-8 tracking-tight text-slate-700">
                  AI can generate content that looks great.
                  <span className="text-violet-600">
                    {" "}
                    BrandGuard answers whether it still feels uniquely yours.
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PRINCIPLES */}
      <section
        id="principles"
        className="border-y border-slate-200/70 bg-white/70"
      >
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-8">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                icon: ShieldCheck,
                title: "Deterministic",
                text: "The decision engine produces consistent, rule-backed outcomes.",
              },
              {
                icon: FileSearch,
                title: "Evidence-first",
                text: "Every verdict is connected to structured evidence.",
              },
              {
                icon: Lock,
                title: "Secure by design",
                text: "Tenant boundaries keep organizational intelligence isolated.",
              },
              {
                icon: ServerCog,
                title: "Controlled AI",
                text: "LLMs explain decisions without becoming the decision-maker.",
              },
            ].map((item) => {
              const Icon = item.icon;

              return (
                <div
                  key={item.title}
                  className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg hover:shadow-violet-100/50"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-violet-600">
                    <Icon className="h-5 w-5" />
                  </div>

                  <h3 className="mt-5 text-sm font-bold text-slate-900">
                    {item.title}
                  </h3>

                  <p className="mt-2 text-xs leading-6 text-slate-500">
                    {item.text}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works">
        <div className="mx-auto max-w-7xl px-6 py-24 lg:px-8">
          <div className="max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-violet-600">
              How it works
            </p>

            <h2 className="mt-4 text-4xl font-bold tracking-[-0.03em] text-slate-950 sm:text-5xl">
              A decision pipeline built around evidence.
            </h2>

            <p className="mt-5 text-base leading-7 text-slate-500">
              BrandGuard transforms brand identity into a measurable decision
              layer between AI generation and publication.
            </p>
          </div>

          <div className="relative mt-14">
            <div className="absolute left-[12%] right-[12%] top-8 hidden border-t border-dashed border-violet-200 lg:block" />

            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
              {STEPS.map((step) => {
                const Icon = step.icon;

                return (
                  <div
                    key={step.number}
                    className="relative rounded-3xl border border-slate-200 bg-white p-7 shadow-sm"
                  >
                    <div className="relative z-10 flex items-center justify-between">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-violet-100 bg-violet-50 text-violet-600">
                        <Icon className="h-5 w-5" />
                      </div>

                      <span className="text-xs font-bold text-violet-200">
                        {step.number}
                      </span>
                    </div>

                    <h3 className="mt-7 text-sm font-bold text-slate-900">
                      {step.title}
                    </h3>

                    <p className="mt-3 text-xs leading-6 text-slate-500">
                      {step.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* PLATFORM */}
      <section id="platform" className="bg-[#f3f0fa]">
        <div className="mx-auto max-w-7xl px-6 py-24 lg:px-8">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.22em] text-violet-600">
                Platform
              </p>

              <h2 className="mt-4 text-4xl font-bold tracking-[-0.03em] text-slate-950 sm:text-5xl">
                The intelligence layer for your brand.
              </h2>
            </div>

            <p className="max-w-xl text-sm leading-7 text-slate-500">
              From brand governance to evidence extraction, deterministic
              scoring, explanations, and human approval — BrandGuard brings
              the complete decision flow together.
            </p>
          </div>

          <div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;

              return (
                <div
                  key={feature.title}
                  className="group rounded-3xl border border-white bg-white/80 p-7 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-violet-100/50"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-50 text-violet-600 transition group-hover:bg-violet-100">
                    <Icon className="h-5 w-5" />
                  </div>

                  <h3 className="mt-6 text-sm font-bold text-slate-900">
                    {feature.title}
                  </h3>

                  <p className="mt-3 text-xs leading-6 text-slate-500">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-24 lg:px-8">
        <div className="relative mx-auto max-w-6xl overflow-hidden rounded-[2.5rem] border border-violet-200 bg-white px-7 py-16 shadow-[0_30px_80px_-35px_rgba(76,29,149,0.3)] sm:px-14">
          <div className="absolute -right-32 -top-32 h-80 w-80 rounded-full bg-violet-200/40 blur-[90px]" />
          <div className="absolute -bottom-32 -left-32 h-80 w-80 rounded-full bg-blue-200/30 blur-[90px]" />

          <div className="relative grid gap-10 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-violet-100 text-violet-600">
                <Sparkles className="h-5 w-5" />
              </div>

              <h2 className="mt-6 max-w-2xl text-4xl font-bold tracking-[-0.04em] text-slate-950 sm:text-5xl">
                Make AI-generated content recognizably yours.
              </h2>

              <p className="mt-5 max-w-xl text-sm leading-7 text-slate-500">
                Build a measurable, explainable layer of brand intelligence
                between generation and publication.
              </p>
            </div>

            <Link href="/signup">
              <Button
                size="lg"
                className="rounded-xl bg-violet-600 px-7 shadow-lg shadow-violet-200 hover:bg-violet-700"
              >
                Get started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-8 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
              <Sparkles className="h-4 w-4" />
            </div>

            <span className="text-sm font-bold text-slate-800">
              BrandGuard AI
            </span>
          </Link>

          <p className="text-xs text-slate-400">
            Enterprise Brand Decision Intelligence Platform
          </p>
        </div>
      </footer>
    </main>
  );
}