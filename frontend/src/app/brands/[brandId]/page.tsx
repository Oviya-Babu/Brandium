"use client";

import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  FileCheck2,
  Fingerprint,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

const EVIDENCE = [
  {
    icon: Fingerprint,
    label: "Brand voice",
    value: "Strong match",
    detail: "Tone, language & personality",
  },
  {
    icon: Target,
    label: "Visual identity",
    value: "Aligned",
    detail: "Color, composition & assets",
  },
  {
    icon: FileCheck2,
    label: "Brand rules",
    value: "8 / 8 passed",
    detail: "Governance & guidelines",
  },
];

const STEPS = [
  ["01", "Submit content", "Bring text, images or short-form video into the workspace."],
  ["02", "Generate evidence", "Specialized workers inspect the content against your Brand Genome."],
  ["03", "Make the decision", "The deterministic engine turns evidence into a defensible brand verdict."],
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#faf9ff] text-[#211d2b]">
      {/* HEADER */}
      <header className="mx-auto flex h-[76px] max-w-[1320px] items-center justify-between px-6 lg:px-10">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#7357c7] text-white shadow-sm">
            <ShieldCheck className="h-[19px] w-[19px]" />
          </div>
          <div>
            <p className="text-[15px] font-bold tracking-[-0.02em]">
              BrandGuard AI
            </p>
            <p className="hidden text-[9px] font-medium uppercase tracking-[0.18em] text-[#918b9d] sm:block">
              Brand Decision Intelligence
            </p>
          </div>
        </Link>

        <nav className="hidden items-center gap-8 text-[13px] font-medium text-[#706a79] md:flex">
          <a href="#how-it-works" className="transition hover:text-[#7357c7]">
            How it works
          </a>
          <a href="#evidence" className="transition hover:text-[#7357c7]">
            Evidence
          </a>
          <a href="#platform" className="transition hover:text-[#7357c7]">
            Platform
          </a>
        </nav>

        <div className="flex items-center gap-2.5">
          <Link
            href="/login"
            className="hidden rounded-xl px-4 py-2.5 text-[13px] font-semibold text-[#5d5668] transition hover:bg-white sm:block"
          >
            Log in
          </Link>
          <Link
            href="/signup"
            className="group flex items-center gap-2 rounded-xl bg-[#7357c7] px-4 py-2.5 text-[13px] font-semibold text-white shadow-[0_6px_18px_rgba(115,87,199,0.18)] transition hover:-translate-y-0.5 hover:bg-[#674ab9]"
          >
            Get started
            <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-0.5" />
          </Link>
        </div>
      </header>

      {/* HERO */}
      <section className="px-4 pb-8 pt-3 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1320px] overflow-hidden rounded-[30px] border border-[#e8e2f2] bg-white shadow-[0_18px_60px_rgba(72,54,110,0.07)]">
          <div className="grid min-h-[590px] lg:grid-cols-[0.92fr_1.08fr]">
            {/* LEFT */}
            <div className="relative overflow-hidden bg-[#f1ebfb] px-7 py-10 sm:px-10 lg:px-14 lg:py-14">
              <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-[#d9cafa]/50 blur-3xl" />
              <div className="absolute -bottom-24 -left-20 h-64 w-64 rounded-full bg-white/70 blur-3xl" />

              <div className="relative flex h-full flex-col">
                <div>
                  <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#dcd0f0] bg-white/60 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#7357c7]">
                    <Sparkles className="h-3 w-3" />
                    AI brand intelligence
                  </div>

                  <h1 className="max-w-[570px] text-[46px] font-semibold leading-[0.98] tracking-[-0.055em] text-[#292331] sm:text-[58px] lg:text-[64px]">
                    Is this content
                    <br />
                    <span className="text-[#7357c7]">really your brand?</span>
                  </h1>

                  <p className="mt-7 max-w-[490px] text-[16px] leading-7 text-[#6e6878]">
                    BrandGuard turns your brand guidelines into measurable
                    evidence — so every AI-generated asset can be evaluated
                    before it reaches your audience.
                  </p>

                  <div className="mt-8 flex flex-wrap gap-3">
                    <Link
                      href="/signup"
                      className="group inline-flex items-center gap-2 rounded-xl bg-[#7357c7] px-5 py-3 text-[13px] font-semibold text-white shadow-[0_8px_20px_rgba(115,87,199,0.2)] transition hover:-translate-y-0.5"
                    >
                      Explore BrandGuard
                      <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                    </Link>

                    <a
                      href="#how-it-works"
                      className="inline-flex items-center gap-2 rounded-xl border border-[#dcd3e8] bg-white/70 px-5 py-3 text-[13px] font-semibold text-[#5f586b] transition hover:bg-white"
                    >
                      See how it works
                      <ChevronRight className="h-4 w-4" />
                    </a>
                  </div>
                </div>

                <div className="mt-auto pt-12">
                  <p className="mb-3 text-[9px] font-bold uppercase tracking-[0.18em] text-[#9389a3]">
                    Built around evidence
                  </p>

                  <div className="flex flex-wrap gap-2">
                    {["Brand Genome", "Evidence-first", "Deterministic BDI"].map(
                      (item) => (
                        <div
                          key={item}
                          className="rounded-lg border border-[#ddd3ec] bg-white/60 px-3 py-2 text-[11px] font-medium text-[#665e70]"
                        >
                          {item}
                        </div>
                      ),
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* RIGHT — PRODUCT VISUAL */}
            <div className="relative flex items-center bg-[#fff] px-5 py-10 sm:px-8 lg:px-10">
              <div className="w-full">
                {/* top mini bar */}
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#9b94a4]">
                      Brand workspace
                    </p>
                    <p className="mt-1 text-[17px] font-semibold tracking-[-0.02em]">
                      Content evaluation
                    </p>
                  </div>

                  <div className="rounded-lg border border-[#e5e0eb] bg-[#faf9fc] px-3 py-2 text-[10px] font-semibold text-[#716a7c]">
                    Demo workspace
                  </div>
                </div>

                {/* main dashboard */}
                <div className="relative rounded-[22px] border border-[#e7e1ee] bg-[#fbfaff] p-4 shadow-[0_15px_40px_rgba(58,45,84,0.08)] sm:p-5">
                  <div className="grid gap-4 sm:grid-cols-[190px_1fr]">
                    {/* score */}
                    <div className="rounded-[17px] border border-[#e4dff0] bg-white p-5">
                      <div className="flex items-center justify-between">
                        <p className="text-[9px] font-bold uppercase tracking-[0.13em] text-[#928b9b]">
                          BDI score
                        </p>
                        <span className="h-2 w-2 rounded-full bg-[#7357c7]" />
                      </div>

                      <div className="mt-5 flex items-end gap-1">
                        <span className="text-[45px] font-semibold leading-none tracking-[-0.06em]">
                          87
                        </span>
                        <span className="mb-1 text-[15px] text-[#aaa4b1]">
                          .4
                        </span>
                      </div>

                      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-[#eeeaf5]">
                        <div className="h-full w-[87%] rounded-full bg-[#7357c7]" />
                      </div>

                      <div className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-[#f0ecf8] px-2.5 py-1.5 text-[10px] font-bold text-[#7357c7]">
                        <CheckCircle2 className="h-3 w-3" />
                        Brand aligned
                      </div>
                    </div>

                    {/* evidence */}
                    <div className="rounded-[17px] border border-[#e4dff0] bg-white p-5">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-[11px] font-semibold">
                            Evidence summary
                          </p>
                          <p className="mt-0.5 text-[9px] text-[#9992a1]">
                            Why this decision was made
                          </p>
                        </div>

                        <span className="rounded-md bg-[#f4f1f8] px-2 py-1 text-[9px] font-semibold text-[#756d7f]">
                          14 signals
                        </span>
                      </div>

                      <div className="mt-4 flex flex-col gap-2.5">
                        {EVIDENCE.map((item) => {
                          const Icon = item.icon;

                          return (
                            <div
                              key={item.label}
                              className="flex items-center gap-3 rounded-xl border border-[#eeeaf2] bg-[#fcfbfd] p-2.5"
                            >
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#f0ebf8] text-[#7357c7]">
                                <Icon className="h-4 w-4" />
                              </div>

                              <div className="min-w-0 flex-1">
                                <p className="text-[10px] font-semibold">
                                  {item.label}
                                </p>
                                <p className="truncate text-[8px] text-[#9a93a2]">
                                  {item.detail}
                                </p>
                              </div>

                              <span className="text-[9px] font-bold text-[#7357c7]">
                                {item.value}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* pipeline */}
                  <div className="mt-4 rounded-[17px] border border-[#e4dff0] bg-white p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-[#918a9b]">
                        Decision pipeline
                      </p>
                      <p className="text-[9px] text-[#aaa4b1]">
                        Evidence → Decision
                      </p>
                    </div>

                    <div className="mt-4 flex items-center">
                      {[
                        ["Content", "01"],
                        ["Evidence", "02"],
                        ["BDI", "03"],
                        ["Decision", "04"],
                      ].map(([label, number], index) => (
                        <div
                          key={label}
                          className="flex min-w-0 flex-1 items-center"
                        >
                          <div className="flex items-center gap-2">
                            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#eee9f7] text-[8px] font-bold text-[#7357c7]">
                              {number}
                            </div>
                            <span className="text-[9px] font-semibold text-[#615a6c]">
                              {label}
                            </span>
                          </div>

                          {index < 3 && (
                            <div className="mx-2 h-px flex-1 bg-[#e7e2ec]" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* floating badge */}
                <div className="relative -mt-3 ml-auto mr-3 flex w-fit items-center gap-2 rounded-xl border border-[#ddd5eb] bg-white px-3 py-2 shadow-[0_8px_25px_rgba(62,45,89,0.1)]">
                  <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#f0ebf8]">
                    <CheckCircle2 className="h-3.5 w-3.5 text-[#7357c7]" />
                  </div>
                  <div>
                    <p className="text-[9px] font-bold">Decision ready</p>
                    <p className="text-[8px] text-[#9992a1]">
                      Evidence chain complete
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PIPELINE STRIP */}
      <section className="px-4 py-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1320px] rounded-[22px] border border-[#e6e0ed] bg-white px-6 py-6 shadow-[0_8px_30px_rgba(72,54,110,0.04)]">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center">
            <div className="lg:w-[240px]">
              <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#7357c7]">
                The core loop
              </p>
              <p className="mt-1.5 text-[14px] font-semibold">
                One decision pipeline.
              </p>
            </div>

            <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
              {[
                ["01", "Content", "Your asset"],
                ["02", "Evidence", "Observable signals"],
                ["03", "BDI", "Deterministic score"],
                ["04", "Decision", "Explainable verdict"],
              ].map(([number, title, subtitle], index) => (
                <div key={title} className="flex flex-1 items-center">
                  <div className="flex w-full items-center gap-3 rounded-xl bg-[#faf9fc] px-3 py-3">
                    <span className="text-[9px] font-bold text-[#7357c7]">
                      {number}
                    </span>
                    <div>
                      <p className="text-[11px] font-semibold">{title}</p>
                      <p className="text-[8px] text-[#9b94a3]">{subtitle}</p>
                    </div>
                  </div>

                  {index < 3 && (
                    <ArrowRight className="mx-2 hidden h-3.5 w-3.5 shrink-0 text-[#b4adbc] sm:block" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1120px]">
          <div className="max-w-[600px]">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#7357c7]">
              How it works
            </p>
            <h2 className="mt-3 text-[34px] font-semibold tracking-[-0.045em] sm:text-[43px]">
              From brand guidelines
              <br />
              to a defensible decision.
            </h2>
            <p className="mt-4 text-[14px] leading-6 text-[#777080]">
              BrandGuard separates evidence from judgment. The system measures
              the content first, then explains what the measurements mean.
            </p>
          </div>

          <div className="mt-12 grid gap-3 md:grid-cols-3">
            {STEPS.map(([number, title, description]) => (
              <div
                key={number}
                className="group rounded-[20px] border border-[#e5dfeb] bg-white p-6 transition hover:-translate-y-1 hover:shadow-[0_12px_35px_rgba(72,54,110,0.07)]"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-[#7357c7]">
                    {number}
                  </span>
                  <ArrowRight className="h-4 w-4 text-[#b1a9b9] transition group-hover:translate-x-1 group-hover:text-[#7357c7]" />
                </div>

                <h3 className="mt-10 text-[17px] font-semibold">{title}</h3>
                <p className="mt-2.5 text-[12px] leading-5 text-[#817a89]">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* EVIDENCE */}
      <section
        id="evidence"
        className="border-y border-[#e7e1ec] bg-[#f3eef9] px-4 py-20 sm:px-6 lg:px-8"
      >
        <div className="mx-auto grid max-w-[1120px] gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#7357c7]">
              Evidence first
            </p>

            <h2 className="mt-3 text-[35px] font-semibold tracking-[-0.045em] sm:text-[44px]">
              Don&apos;t just get a score.
              <br />
              <span className="text-[#7357c7]">Know why.</span>
            </h2>

            <p className="mt-5 max-w-[470px] text-[14px] leading-6 text-[#777080]">
              Every decision can be traced back to observable evidence from
              your brand assets and approved guidelines.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {[
              ["Brand Genome", "A structured, version-controlled source of truth."],
              ["Specialized workers", "Inspect voice, visuals and brand-specific signals."],
              ["Decision Engine", "Computes the BDI without asking an LLM to decide."],
              ["Explainability", "Turns evidence into a clear human-readable reason."],
            ].map(([title, description]) => (
              <div
                key={title}
                className="rounded-[18px] border border-[#ded5e9] bg-white p-5"
              >
                <div className="mb-7 h-2 w-2 rounded-full bg-[#7357c7]" />
                <h3 className="text-[14px] font-semibold">{title}</h3>
                <p className="mt-2 text-[11px] leading-5 text-[#817989]">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PLATFORM */}
      <section id="platform" className="px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1120px]">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#7357c7]">
                Built for teams
              </p>
              <h2 className="mt-3 text-[34px] font-semibold tracking-[-0.045em] sm:text-[42px]">
                Brand intelligence,
                <br />
                built into the workflow.
              </h2>
            </div>

            <p className="max-w-[340px] text-[12px] leading-5 text-[#817989]">
              Governance, evidence, decisions and auditability in one
              enterprise workspace.
            </p>
          </div>

          <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              ["01", "Multi-tenant workspace", "Keep organizations, brands and evidence isolated."],
              ["02", "Versioned Brand Genome", "Know exactly which approved brand truth was evaluated."],
              ["03", "Secure asset intake", "Bring text, images and short-form video into one flow."],
              ["04", "Audit trail", "Track decisions and evidence across the workspace."],
              ["05", "Reports & analytics", "Turn individual evaluations into organization-level insight."],
              ["06", "Human approval", "Keep people in control of the final publishing decision."],
            ].map(([number, title, description]) => (
              <div
                key={number}
                className="rounded-[18px] border border-[#e5dfea] bg-white p-5"
              >
                <span className="text-[9px] font-bold text-[#7357c7]">
                  {number}
                </span>
                <h3 className="mt-6 text-[14px] font-semibold">{title}</h3>
                <p className="mt-2 text-[11px] leading-5 text-[#817989]">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 pb-10 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-[1120px] overflow-hidden rounded-[26px] border border-[#ddd2ec] bg-[#eee7f8] px-7 py-12 sm:px-10">
          <div className="flex flex-col justify-between gap-8 md:flex-row md:items-center">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#7357c7]">
                Brand decisions, backed by evidence
              </p>
              <h2 className="mt-3 max-w-[620px] text-[31px] font-semibold tracking-[-0.04em] sm:text-[38px]">
                Make every AI-generated asset answer to your brand.
              </h2>
            </div>

            <Link
              href="/signup"
              className="group inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[#7357c7] px-5 py-3 text-[13px] font-semibold text-white shadow-[0_8px_20px_rgba(115,87,199,0.18)] transition hover:-translate-y-0.5"
            >
              Start building
              <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="mx-auto flex max-w-[1120px] flex-col gap-4 border-t border-[#e7e2eb] px-4 py-8 text-[10px] text-[#9992a1] sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-center gap-2 font-semibold text-[#716a7c]">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#7357c7] text-white">
            <ShieldCheck className="h-3 w-3" />
          </div>
          BrandGuard AI
        </div>

        <p>Enterprise Brand Decision Intelligence Platform</p>
      </footer>
    </main>
  );
}