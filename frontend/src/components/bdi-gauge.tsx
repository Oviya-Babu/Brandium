"use client";

function toneForScore(score: number): string {
  if (score >= 75) return "var(--aligned)";
  if (score >= 50) return "var(--partial)";
  return "var(--misaligned)";
}

/**
 * Real SVG arc gauge driven by the Decision Engine's actual score — not
 * a static illustration. `stroke-dasharray`/`stroke-dashoffset` on a
 * circle is the standard dependency-free way to render this; no
 * charting library needed for a single value.
 */
export function BdiGauge({ score, size = 176 }: { score: number; size?: number }) {
  const stroke = 14;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, score));
  const offset = circumference * (1 - clamped / 100);
  const tone = toneForScore(clamped);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--muted)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={tone}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-semibold text-foreground">{clamped.toFixed(1)}</span>
        <span className="text-[11px] text-muted-foreground">/ 100</span>
      </div>
    </div>
  );
}
