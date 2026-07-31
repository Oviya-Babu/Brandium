import type { Config } from "tailwindcss";

// Placeholder theme — the actual design system (typography scale, color
// tokens, spacing) is a Phase 7 deliverable (CLAUDE.md §14 Milestone 13),
// not this foundation milestone. Kept minimal on purpose.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
