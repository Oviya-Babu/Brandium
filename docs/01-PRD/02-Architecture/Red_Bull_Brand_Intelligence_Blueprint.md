# Red Bull Brand Brain — Brand Intelligence Blueprint

**Status:** Approved design artifact — implementation roadmap for Sprint 1.1's Brand Intelligence content. Not a Phase spec, not a schema change: this document maps real Red Bull knowledge onto the existing, frozen `Brand → BrandGenome → GenomeCategory → GenomeComponent → Assertion` model, one Knowledge Domain at a time.

## Ground rule this blueprint is built against

The architecture is frozen and stays frozen: `Brand` → `BrandGenome` → `GenomeCategory` (6 fixed values, closed) → `GenomeComponent` (named units *within* a Category) → `Assertion` (the atomic claim). Every Knowledge Domain below must terminate in one or more real `(GenomeCategory, GenomeComponent)` pairs, because that is the only shape `genome_compiler.py` and the Decision Engine can ever consume.

**One load-bearing fact this blueprint relies on, verified in the code, not assumed:** `GenomeComponent.name` is a plain `String` column, not a database enum — only `GenomeCategoryName` (the 6 categories) is a closed enum. The current Component list (5/4/3/3/3/1 per category) lives entirely in one Python dict, `brand_governance/genome_taxonomy.py`, and that module's own docstring calls itself "a companion schema reference" for Phase 1 §12's explicitly *open* question ("Component-level taxonomy detail... left to a companion schema reference, to be finalized"). So: extending that dict with new, well-justified Components is not "new infrastructure" or "redesigning the architecture" — it is filling in a gap the architecture itself designed to be filled in later, requires zero migration (no DB enum, no new table), and only affects Genomes compiled *after* the change (Phase 1 §9: taxonomy changes are forward-only, never retroactive) — so it cannot touch Apple's already-compiled Genome. Where a Red Bull Knowledge Domain doesn't fit cleanly into an existing Component, this blueprint proposes a specific new Component name under the correct existing Category, flagged explicitly as **[NEW COMPONENT]**. Nothing here proposes a new Category — that set is genuinely closed.

Every domain entry below answers, in order: **Why it matters · What BrandGuard evaluates · Features workers compare · Assertion types generated · Policies it can drive · Impact on Distinctiveness scoring · Genome mapping · Authority.**

---

## I. Company Identity & Brand Philosophy → `Values & Mission`

### I.1 Corporate Identity & Origin
- **Why:** Grounds every other domain in who the brand actually is (Austrian, founded 1987, Dietrich Mateschitz/Chaleo Yoovidhya) — without it, positioning claims have no anchor to check for authenticity drift.
- **Evaluates:** Whether generated copy invents a false corporate history/origin story or misattributes the brand.
- **Features to compare:** Named-entity mentions of founding facts in text assets.
- **Assertion types:** Factual, high-confidence, low-ambiguity (`structured`-friendly: founding year, founders, HQ country).
- **Policies:** Low-weight sanity-check rule, not score-driving — a `critical_rule` only if a generated asset actively contradicts a founding fact.
- **Distinctiveness impact:** Minimal directly; mostly a guard-rail, not a scoring lever.
- **Maps to:** `values_mission → Organizational Values` (existing).
- **Authority:** Explicit.

### I.2 Brand Philosophy & Worldview
- **Why:** Red Bull is explicitly *not* selling a beverage on functional merits — it sells a worldview ("give wings to people and ideas," daring/limit-pushing as identity). This is the single highest-leverage domain for judging whether an asset "feels like Red Bull" versus "feels like any energy drink."
- **Evaluates:** Whether an asset's underlying attitude (confident/daring/irreverent vs. cautious/corporate/safe) matches brand philosophy, independent of literal keyword matches.
- **Features to compare:** Text sentiment/register; for images, subject behavior/context (risk-taking, motion, altitude, speed vs. static/safe framing).
- **Assertion types:** Qualitative but evaluable (e.g. "content tone conveys confidence and momentum, never caution or apology") — the hardest kind for a Worker to check but the most brand-defining.
- **Policies:** High category weight justification — this is *why* `messaging_positioning`/`values_mission` deserve real weight in Red Bull's Policy, not an afterthought.
- **Distinctiveness impact:** High — this is the domain most responsible for separating "authentically Red Bull" from "generic energy-drink AI slop."
- **Maps to:** `values_mission → Cause & Purpose Alignment` + **[NEW COMPONENT]** `values_mission → Brand Worldview & Philosophy` (existing "Organizational Values" is too narrow for this — it's about *attitude*, not stated corporate values).
- **Authority:** Explicit.

### I.3 Mission Statement
- **Why:** FR-001 onboarding baseline; every Genome needs at least one explicit mission claim.
- **Evaluates:** Direct mission-alignment checks for copy that claims purpose/impact.
- **Features to compare:** Text claims mapped against "give wings to people and ideas."
- **Assertion types:** Single canonical factual assertion, very high confidence.
- **Policies:** Rarely score-driving alone; supports Recommendation narration ("this copy doesn't connect to the brand's stated mission").
- **Distinctiveness impact:** Low-medium.
- **Maps to:** `values_mission → Mission Statement` (existing).
- **Authority:** Explicit.

### I.4 Cause & Purpose Alignment (Wings for Life)
- **Why:** A concrete, well-documented, checkable philanthropic program (spinal cord injury research, the World Run's no-fixed-finish-line format) — real evidence a generic AI asset would never know to reference correctly.
- **Evaluates:** Whether cause-marketing content correctly represents Wings for Life vs. a generic "we support charity" platitude.
- **Features to compare:** Specific factual details (cause area, event mechanic) vs. vague substitutes.
- **Assertion types:** Specific factual claims, high confidence.
- **Policies:** Supports a "specificity over platitude" recommendation rule.
- **Distinctiveness impact:** Medium — a strong differentiator against generic "corporate social responsibility" AI copy.
- **Maps to:** `values_mission → Cause & Purpose Alignment` (existing).
- **Authority:** Explicit.

### I.5 Sustainability & Responsibility
- **Why:** Listed as a candidate domain, but genuinely thin in Red Bull's public messaging (unlike, say, Patagonia) — sustainability is not a load-bearing pillar of this brand's actual public positioning.
- **Evaluates:** N/A in practice — flagged so we don't fabricate a domain the brand doesn't actually emphasize.
- **Recommendation:** **Skip.** Including a manufactured sustainability domain would itself be exactly the kind of "invent claims not present in the source" failure `genome_compiler.py`'s own extraction prompt is designed to prevent. Revisit only if real public evidence turns up during implementation.

---

## II. Visual Identity System → `Visual Identity`

### II.1 Logo System
- **Why:** The single most recognizable brand asset; near-zero tolerance for drift.
- **Evaluates:** Correct mark (two charging bulls + yellow sun disc), correct lockup, no fabricated logo variants.
- **Features to compare:** Vision-worker object/shape detection against the described mark.
- **Assertion types:** Highly specific, high-confidence, near-binary (present/correct vs. absent/wrong).
- **Policies:** Strong candidate for a `critical_rule` (Visual Identity, Logo Usage) — logo misrepresentation is a compliance-adjacent failure, not just a style miss.
- **Distinctiveness impact:** High but binary — doesn't scale a score up much, but a failure here should dominate.
- **Maps to:** `visual_identity → Logo Usage` (existing).
- **Authority:** Explicit.

### II.2 Color System
- **Why:** Red/blue/yellow-gold + silver can livery is instantly recognizable even without the logo in frame.
- **Evaluates:** Palette adherence in generated imagery.
- **Features to compare:** Dominant/accent color extraction vs. the defined palette (with real approximate hex/Pantone references, not vague "red and blue").
- **Assertion types:** Structured, machine-checkable (`{attribute: primary_color, value: "#CC1E4A"}`-shaped) — one of the best candidates in the whole Genome for a clean structured predicate.
- **Policies:** Moderate-weight, quantitative scoring input.
- **Distinctiveness impact:** High and continuous (not binary) — good scoring signal.
- **Maps to:** `visual_identity → Color Palette` (existing).
- **Authority:** Explicit.

### II.3 Typography System
- **Why:** Bold uppercase sans-serif wordmark is part of brand recognition, especially in text-overlay marketing assets.
- **Evaluates:** Typeface weight/case/style conformance where text appears in-image or as a described spec.
- **Features to compare:** OCR'd in-image type style vs. the defined typographic rules.
- **Assertion types:** Structured where possible (weight, case), qualitative otherwise.
- **Policies:** Low-moderate weight — supporting evidence, rarely alone decisive.
- **Distinctiveness impact:** Low-medium.
- **Maps to:** `visual_identity → Typography` (existing).
- **Authority:** Explicit.

### II.4 Photography & Imagery Style
- **Why:** Arguably Red Bull's *strongest* visual tell after the logo: dynamic, backlit, frozen-mid-motion action photography, never static studio product shots. This is precisely the domain most predictive of "AI slop vs. real Red Bull creative," since generic AI compositions default to centered, evenly-lit, static framing.
- **Evaluates:** Whether an image's photographic *treatment* (not just subject matter) matches brand style.
- **Features to compare:** Motion blur/freeze-frame cues, lighting direction/contrast, subject-in-environment vs. isolated-on-white.
- **Assertion types:** Qualitative, evaluable, and this is exactly where the AI Slop KB (§ IX below) is meant to be cross-referenced — a "fake/inconsistent depth of field" or "unrealistic lighting" Slop pattern is the direct *negative* of this domain's positive claims.
- **Policies:** High weight — this is a primary Distinctiveness Worker input.
- **Distinctiveness impact:** Very high.
- **Maps to:** `visual_identity → Imagery & Photography Style` (existing).
- **Authority:** Explicit.

### II.5 Composition & Layout Conventions
- **Why:** Dynamic diagonal framing and tight action cropping vs. generic centered/symmetrical layouts — again a direct counter-signal to common AI-slop composition defaults.
- **Evaluates:** Layout/framing conventions.
- **Features to compare:** Symmetry/centeredness metrics, crop tightness, negative-space usage.
- **Assertion types:** Qualitative, comparative against Slop KB's "overly symmetrical / centered layout" pattern.
- **Policies:** Moderate weight, pairs with Photography domain.
- **Distinctiveness impact:** High.
- **Maps to:** `visual_identity → Layout & Composition` (existing).
- **Authority:** Explicit.

### II.6 Motion & Energy
- **Why:** Called out explicitly as a candidate domain, and it is genuinely distinct from "photography style" — it's about *implied kinetic energy* (mid-air athletes, speed, momentum) as a brand-defining visual trait in its own right, referenced across virtually every other visual/sponsorship domain (F1, extreme sports, Stratos).
- **Evaluates:** Whether an image conveys energy/momentum vs. static blandness.
- **Features to compare:** Motion cues (blur, pose, camera angle implying speed) as a distinct signal from lighting/color.
- **Assertion types:** Qualitative.
- **Policies:** Supports Distinctiveness scoring specifically, less relevant to compliance.
- **Distinctiveness impact:** High.
- **Maps to:** **[NEW COMPONENT]** `visual_identity → Motion & Energy` (distinct enough from "Imagery & Photography Style" — a photo can be technically on-style but visually static, which this Component is meant to catch on its own).
- **Authority:** Explicit (derived from the same guideline material as II.4/II.5).

---

## III. Packaging & Product System

### III.1 Packaging & Container Design
- **Why:** The slim can silhouette + silver/blue/red livery is recognizable even cropped or partially obscured.
- **Evaluates:** Can/bottle form and livery accuracy when product packaging appears in an asset.
- **Features to compare:** Container shape/proportions, livery color placement.
- **Assertion types:** Structured, high-confidence.
- **Policies:** Moderate weight, mostly relevant to product-shot assets specifically.
- **Distinctiveness impact:** Medium (asset-type-dependent — irrelevant for pure lifestyle/sponsorship content).
- **Maps to:** `visual_identity → Logo Usage` is too narrow; **[NEW COMPONENT]** `visual_identity → Packaging & Product Form`.
- **Authority:** Explicit.

### III.2 Product Portfolio & Line Architecture
- **Why:** Original/Sugarfree/Zero/editions are distinct sub-brands with the same master identity — relevant to check that generated content doesn't misrepresent which product it's depicting.
- **Evaluates:** Product-line accuracy in text/label claims.
- **Features to compare:** Named product variant vs. described portfolio.
- **Assertion types:** Structured factual list.
- **Policies:** Low weight, mostly a factual-accuracy guard-rail.
- **Distinctiveness impact:** Low.
- **Maps to:** `messaging_positioning → Positioning Statements` (existing — product-line facts support positioning claims, don't need their own Component).
- **Authority:** Explicit.

---

## IV. Verbal Identity & Brand Personality → `Verbal Identity`

### IV.1 Tone of Voice
- **Why:** Bold, confident, self-aware, playful — never apologetic or corporate. This is the text-domain equivalent of II.4 (Photography Style): the strongest single tell for text-based AI slop.
- **Evaluates:** Register/attitude of generated copy.
- **Features to compare:** Text-worker sentiment/register classification vs. defined tone attributes.
- **Assertion types:** Qualitative, evaluable, high brand-defining weight.
- **Policies:** High weight in Verbal Identity's internal component weighting.
- **Distinctiveness impact:** Very high for text/video assets.
- **Maps to:** `verbal_identity → Tone Attributes` (existing).
- **Authority:** Explicit.

### IV.2 Vocabulary & Prohibited Language
- **Why:** Explicit "never sound cautious/apologetic/safety-first" rule is a concrete, checkable negative constraint — one of the cleanest `critical_rule` candidates in the entire Genome.
- **Evaluates:** Presence of disallowed hedging/cautious language patterns.
- **Features to compare:** Lexical pattern matching for hedge words/apologetic phrasing.
- **Assertion types:** Structured-friendly (a list of prohibited terms/patterns is about as machine-checkable as brand voice gets).
- **Policies:** Strong `critical_rule` candidate — a single clearly-prohibited phrase should be able to move a verdict.
- **Distinctiveness impact:** Medium, but high policy/compliance leverage.
- **Maps to:** `verbal_identity → Prohibited or Discouraged Language` (existing).
- **Authority:** Explicit.

### IV.3 Brand Personality Traits
- **Why:** Distinct from "tone" (how it's said) — this is *who the brand is as a character* (daring, irreverent, self-aware, never boastful-for-its-own-sake). Listed explicitly as a candidate domain and genuinely separable from Tone Attributes in how a Worker would check it (personality shows up in *what* the copy chooses to talk about, not just *how*).
- **Evaluates:** Whether the "character" behind the copy matches brand personality vs. a generic corporate voice.
- **Features to compare:** Topic/framing choices, not just word-level tone.
- **Assertion types:** Qualitative.
- **Policies:** Supports Recommendation narration quality more than raw scoring.
- **Distinctiveness impact:** Medium-high.
- **Maps to:** **[NEW COMPONENT]** `verbal_identity → Brand Personality` (kept separate from Tone Attributes deliberately, per above).
- **Authority:** Explicit.

### IV.4 Sentence-Level Style & Copy Conventions
- **Why:** Short, punchy, confident sentence construction is itself a checkable stylistic fingerprint.
- **Evaluates:** Sentence length/structure patterns.
- **Features to compare:** Syntactic features (length, imperative mood usage, punctuation style).
- **Assertion types:** Structured (quantitative thresholds are plausible here, e.g. average sentence length).
- **Policies:** Low-moderate weight.
- **Distinctiveness impact:** Low-medium.
- **Maps to:** `verbal_identity → Sentence-Level Style Conventions` (existing).
- **Authority:** Explicit.

---

## V. Messaging & Positioning → `Messaging & Positioning`

### V.1 Core Value Propositions
- **Why:** "Performance/energy for moments of mental and physical peak" — the functional-benefit anchor beneath the lifestyle branding.
- **Evaluates:** Whether claimed benefits align with the brand's actual value proposition (vs. generic "boosts energy" claims any competitor could make).
- **Features to compare:** Claim specificity/uniqueness.
- **Assertion types:** Qualitative + some structured claims.
- **Policies:** Moderate weight.
- **Distinctiveness impact:** Medium.
- **Maps to:** `messaging_positioning → Core Value Propositions` (existing).
- **Authority:** Explicit.

### V.2 Approved Taglines & Key Messages
- **Why:** "Red Bull Gives You Wiiings" — including the real, documented, legally-motivated spelling ("Wiiings," not "Wings") is a genuinely high-value, highly specific, easily-verified factual assertion that a generic AI asset would almost certainly get wrong (using "Wings" or inventing a different tagline).
- **Evaluates:** Exact tagline usage/misuse.
- **Features to compare:** Exact string/near-string match in copy.
- **Assertion types:** Extremely high-confidence, structured (`exact_string` predicate) — one of the single best Assertions in the whole Genome for demonstrating deterministic, explainable evaluation.
- **Policies:** Strong scoring input; could support a targeted Recommendation ("use the approved spelling").
- **Distinctiveness impact:** High, and cleanly explainable — great demo material.
- **Maps to:** `messaging_positioning → Approved Taglines & Key Messages` (existing).
- **Authority:** Explicit.

### V.3 Positioning Statements
- **Why:** "Not a sports drink — a catalyst for daring" is the umbrella positioning claim everything else supports.
- **Evaluates:** Category-framing accuracy (energy/performance brand vs. generic "soft drink" framing).
- **Features to compare:** Category language in copy.
- **Assertion types:** Qualitative.
- **Policies:** Moderate-high weight.
- **Distinctiveness impact:** Medium-high.
- **Maps to:** `messaging_positioning → Positioning Statements` (existing).
- **Authority:** Explicit.

### V.4 Storytelling & Narrative Style
- **Why:** Explicitly called out as a candidate domain — Red Bull markets almost exclusively through narrative content (Stratos, athlete documentaries, Media House) rather than direct product claims. This is a distinct *format* pattern from "tone" or "positioning."
- **Evaluates:** Whether content is framed as a story/moment (event-driven, human-stakes narrative) vs. direct-sell advertising copy.
- **Features to compare:** Narrative structure cues (protagonist/stakes/moment) vs. feature-benefit ad copy structure.
- **Assertion types:** Qualitative.
- **Policies:** Supports Recommendation quality (e.g. "this reads like a direct-sell ad, not a Red Bull story").
- **Distinctiveness impact:** Medium-high, especially for video/long-form text.
- **Maps to:** **[NEW COMPONENT]** `messaging_positioning → Storytelling & Narrative Style`.
- **Authority:** Explicit (the pattern itself is stated brand strategy) + Exemplar (Stratos etc. as evidence).

---

## VI. Sponsorship & Cultural Positioning

*(This whole cluster is genuinely Red Bull-specific — no other seeded brand in this system would have anything like it — and it is where most of the brand's actual public content volume lives. All Exemplar authority: observational evidence of positioning-in-action, per Phase 1 §4, never prescriptive rules.)*

### VI.1 Formula 1 & Motorsport Branding
- **Why:** Oracle Red Bull Racing is Red Bull's single largest, most technically sophisticated sponsorship platform — real, current, well-documented ($500M/5yr deal, real technology-partnership narrative).
- **Evaluates:** Motorsport-context content for correct team/livery/partner references and "performance under pressure" framing.
- **Features to compare:** Team livery colors (same red/navy/yellow family, motorsport-specific application), technology/performance narrative framing.
- **Assertion types:** Factual (sponsor names, dates) + qualitative (framing).
- **Policies:** Supports positioning-consistency scoring, not compliance-critical.
- **Distinctiveness impact:** Medium — mostly relevant when motorsport content is actually present in the asset.
- **Maps to:** `messaging_positioning → Positioning Statements` for the framing; **[NEW COMPONENT]** `messaging_positioning → Sponsorship & Cultural Platforms` for the factual sponsorship-property details (this Component absorbs VI.1-VI.6 below, so we're not creating six near-duplicate Components for six sponsorship properties).
- **Authority:** Exemplar.

### VI.2 Extreme Sports Branding
- **Why:** Rampage, Cliff Diving World Series, 800+ sponsored athletes, €1B+ sponsorship spend — the deepest, most voluminous evidence base for "what does authentic Red Bull creative content actually look like."
- **Evaluates:** Whether extreme-sports-context content matches real sponsored-property conventions vs. generic "extreme sports stock footage" framing.
- **Features to compare:** Specific named properties/athletes vs. generic action-sports imagery with no brand-specific grounding.
- **Assertion types:** Qualitative + factual (named properties).
- **Policies:** Supports Distinctiveness scoring — this is precisely the domain that should penalize "generic extreme-sports stock photography" (a named AI Slop pattern, § IX below).
- **Distinctiveness impact:** High.
- **Maps to:** `messaging_positioning → Sponsorship & Cultural Platforms`.
- **Authority:** Exemplar.

### VI.3 Athlete Sponsorship & Endorsement Patterns
- **Why:** How Red Bull frames athletes (as daring individuals pushing limits, not generic "brand ambassadors") is a distinct, checkable narrative convention.
- **Evaluates:** Athlete-endorsement content framing.
- **Features to compare:** Individual-achievement/risk framing vs. generic celebrity-endorsement framing.
- **Assertion types:** Qualitative.
- **Policies:** Supports Recommendation narration.
- **Distinctiveness impact:** Medium.
- **Maps to:** `messaging_positioning → Sponsorship & Cultural Platforms`.
- **Authority:** Exemplar.

### VI.4 Event Branding (Stratos, Flugtag, Wings for Life World Run)
- **Why:** Red Bull invents its own branded events rather than only sponsoring existing ones — Stratos (2012 stratospheric jump) is the single most-cited example of Red Bull's "content as proof, not advertising" philosophy anywhere in public brand discourse.
- **Evaluates:** Whether event-context content matches the real "engineered spectacle, live-broadcast, proof-not-claim" pattern.
- **Features to compare:** Event-specific factual grounding vs. generic "extreme stunt" framing.
- **Assertion types:** Factual (specific events/dates) + qualitative (the philosophy behind them, linking back to I.2).
- **Policies:** Supports Distinctiveness scoring and Recommendation specificity.
- **Distinctiveness impact:** High — very hard for a generic AI asset to fabricate this specifically and correctly.
- **Maps to:** `messaging_positioning → Sponsorship & Cultural Platforms`.
- **Authority:** Exemplar.

### VI.5 Red Bull Media House & Content Strategy
- **Why:** Red Bull operates as an actual media company (The Red Bulletin, Servus TV, Terra Mater Factual Studios) — content-quality and production-value expectations are themselves part of the brand standard, not incidental.
- **Evaluates:** Production-value/content-format expectations (documentary-style, high production quality) vs. low-effort generic ad content.
- **Features to compare:** Content format/production-value cues.
- **Assertion types:** Qualitative.
- **Policies:** Supports Distinctiveness scoring for long-form/video-adjacent assets specifically.
- **Distinctiveness impact:** Medium (asset-type-dependent).
- **Maps to:** `messaging_positioning → Sponsorship & Cultural Platforms`.
- **Authority:** Exemplar.

### VI.6 Campaign Style Patterns
- **Why:** Explicitly listed as a candidate domain — the recognizable *format* Red Bull campaigns take (stunt/spectacle + real-time broadcast + minimal direct product messaging) is itself a checkable pattern, distinct from any single campaign's content.
- **Evaluates:** Campaign-format conventions.
- **Features to compare:** Structural campaign features (stunt-centric, low product-forward messaging).
- **Assertion types:** Qualitative.
- **Policies:** Supports Recommendation quality.
- **Distinctiveness impact:** Medium.
- **Maps to:** `messaging_positioning → Sponsorship & Cultural Platforms`.
- **Authority:** Exemplar.

### VI.7 Social Media Patterns
- **Why:** Listed as a candidate domain. Public social content is real, current, high-volume Exemplar evidence, but genuinely thinner in verifiable, citable specifics than F1/Stratos/Rampage without deep platform-specific research.
- **Evaluates:** Social-native content conventions (short-form, athlete-POV, real-time event coverage).
- **Recommendation:** **Include, but scope tightly** to what's independently verifiable (posting cadence/format conventions, not attempting to catalogue specific viral posts) — flagged as the one sponsorship-cluster domain most likely to need light-touch treatment relative to the others.
- **Maps to:** `verbal_identity → Sentence-Level Style Conventions` (short-form copy conventions) + `messaging_positioning → Sponsorship & Cultural Platforms` (format conventions) — no new Component needed, this domain is a thinner overlay on two existing ones rather than a first-class pillar.
- **Authority:** Exemplar.

---

## VII. Compliance & Legal → `Compliance & Legal`

### VII.1 Regulatory Constraints (Caffeine Labeling)
- **Why:** EU Regulation 1169/2011 is a real, specific, externally-verifiable legal requirement (>150mg caffeine/litre triggers mandatory labeling; Red Bull is at 320mg/L) — the single most concrete compliance fact available for this brand.
- **Evaluates:** Whether marketing content omits required context when making caffeine/energy claims.
- **Features to compare:** Presence/absence of required disclaimer language near caffeine-related claims.
- **Assertion types:** Structured, regulatory-citation-grade (exact threshold, exact required wording).
- **Policies:** **The** clearest `critical_rule` candidate in the entire Genome — this is exactly the kind of assertion that should be able to force a Non-Compliant verdict regardless of aggregate score.
- **Distinctiveness impact:** N/A — this is a compliance gate, not a distinctiveness signal, and should be weighted/treated that way in Policy.
- **Maps to:** `compliance_legal → Regulatory Constraints` (existing).
- **Authority:** Explicit.

### VII.2 Mandatory Disclaimers
- **Why:** The exact required wording ("High caffeine content. Not recommended for children or pregnant or breast-feeding women") is itself a checkable string, not just a policy area.
- **Evaluates:** Exact/near-exact disclaimer text presence when product packaging/claims appear.
- **Features to compare:** OCR'd or literal text match against the required wording.
- **Assertion types:** Exact-string structured predicate — extremely clean for deterministic checking.
- **Policies:** `critical_rule` target.
- **Distinctiveness impact:** N/A (compliance gate).
- **Maps to:** `compliance_legal → Mandatory Disclaimers` (existing).
- **Authority:** Explicit.

### VII.3 Trademark & Attribution Usage
- **Why:** Standard but necessary — correct ® / trademark usage conventions for the wordmark and tagline.
- **Evaluates:** Trademark symbol presence/placement where required.
- **Features to compare:** Symbol presence adjacent to protected marks.
- **Assertion types:** Structured.
- **Policies:** Low-moderate weight compliance check.
- **Distinctiveness impact:** N/A.
- **Maps to:** `compliance_legal → Trademark & Attribution Usage` (existing).
- **Authority:** Explicit.

---

## VIII. Accessibility → `Accessibility`

- **Why:** Optional category (Phase 1 §3) — doesn't block Genome activation.
- **Recommendation:** **Leave thin/unpopulated for Red Bull** — no genuine, citable, brand-specific public accessibility guideline exists to summarize honestly. Populating it would mean fabricating content, which is the one thing every layer of this architecture (the compiler's own extraction prompt included) is explicitly built to refuse to do.

---

## Genome Taxonomy Extension (approved)

Five new Components across three existing Categories — all additive, all forward-only, zero migration:

| Category | New Component | Absorbs domains |
|---|---|---|
| `visual_identity` | **Motion & Energy** | II.6 |
| `visual_identity` | **Packaging & Product Form** | III.1 |
| `verbal_identity` | **Brand Personality** | IV.3 |
| `messaging_positioning` | **Storytelling & Narrative Style** | V.4 |
| `messaging_positioning` | **Sponsorship & Cultural Platforms** | VI.1-VI.6 |

Every other domain above lands in an existing Component unchanged.

---

## IX. AI Slop Knowledge Base — independent domain design

The Slop KB is global and brand-agnostic by design (DR-004) — its domains are organized by *how* generic-AI-content characteristics manifest, not by brand, and each domain is written to be the direct negative counterpart of a Red Bull visual/verbal domain above wherever one exists (cross-referenced below) so a future Distinctiveness Worker can compare "does this look like Red Bull" against "does this look like generic AI slop" as two sides of the same evaluation.

### IX.1 Compositional & Structural Genericness
- **Why:** Templated, centered, symmetrical layouts are a generative-model default, not a deliberate design choice.
- **Evaluates:** Layout genericness.
- **Features:** Symmetry metrics, subject-centering, rule-of-thirds-as-the-only-idea.
- **Assertion types:** Qualitative + some measurable geometry.
- **Policies:** Feeds a Distinctiveness-suppression signal, not a compliance rule.
- **Distinctiveness impact:** Direct negative correlate of II.5 (Composition & Layout Conventions).
- **Patterns in this domain:** generic/templated composition, overly symmetrical/centered layout, stock-photo layout conventions.

### IX.2 Photographic & Rendering Artifacts
- **Why:** Diffusion-model-specific visual tells (malformed details, fake bokeh, physically inconsistent lighting, plastic skin) are mechanically distinct from "bad photography" — they're specifically *synthetic* tells.
- **Evaluates:** Presence of generative-artifact signatures.
- **Features:** Anatomical malformation, DOF consistency, shadow-direction consistency, skin-texture uniformity.
- **Assertion types:** Qualitative, some checklist-structured.
- **Policies:** Direct Distinctiveness-suppression signal; a strong hit here can be near-disqualifying regardless of other scores.
- **Distinctiveness impact:** Direct negative correlate of II.4 (Photography & Imagery Style).
- **Patterns:** diffusion rendering artifacts, plastic/over-smoothed skin, fake/inconsistent depth of field, unrealistic/inconsistent lighting.

### IX.3 Stock & Corporate Photography Sameness
- **Why:** Distinct failure mode from IX.2 — not a rendering *error*, but a *correctly-rendered, brand-generic* image (interchangeable across any company).
- **Evaluates:** Genericness even when technically well-executed.
- **Features:** Interchangeability against any brand — "could this be relabeled for a competitor with zero change."
- **Assertion types:** Qualitative, comparative.
- **Policies:** Distinctiveness-suppression signal.
- **Distinctiveness impact:** Direct negative correlate of II.4/VI.2 (real sponsored-property specificity vs. generic stock action photography).
- **Patterns:** corporate stock photography sameness, repetitive diffusion patterning (background/texture tiling).

### IX.4 Typographic & Pipeline Genericness
- **Why:** Both a style failure (default/wrong typeface) and a technical tell (watermark/training-artifact remnants) belong together as "the type/production layer reveals the pipeline."
- **Evaluates:** Typographic conformance + generation-artifact leakage.
- **Features:** Typeface identity, kerning/legibility, ghosted watermark/seam detection.
- **Assertion types:** Structured where OCR-able.
- **Policies:** Direct Distinctiveness-suppression signal.
- **Distinctiveness impact:** Direct negative correlate of II.3 (Typography System).
- **Patterns:** generic AI-default typography, watermark/pipeline artifact remnants.

### IX.5 Copywriting & Messaging Genericness
- **Why:** The text-domain equivalent of IX.1-IX.4 — brand-agnostic phrasing that reveals prompt-generated rather than brand-voiced copy.
- **Evaluates:** Copy genericness/interchangeability.
- **Features:** Boilerplate CTA detection, superlative-density, prompt-artifact phrasing ("cinematic," "elevate," "seamless synergy").
- **Assertion types:** Lexical-pattern structured (very machine-checkable).
- **Policies:** Direct Distinctiveness-suppression signal.
- **Distinctiveness impact:** Direct negative correlate of IV.1/IV.2/IV.4 (Tone, Vocabulary, Sentence-Level Style).
- **Patterns:** prompt-cliché phrasing, repetitive CTA boilerplate, overused marketing superlative language.

---

## What this blueprint deliberately does not do

- No new tables, columns, enums, or migrations (the one taxonomy-dict extension above is Python data, not schema).
- No new API surface.
- No fabricated domains where public evidence is genuinely thin (Accessibility, Sustainability) — flagged and scoped down rather than invented.

## Implementation sequencing

Implemented one Knowledge Domain cluster at a time, each reviewed before compiling into the Genome:
1. Genome Taxonomy Extension (the 5 new Components above)
2. Visual Identity System (II.1-II.6) + Packaging & Product System (III)
3. Compliance & Legal (VII) — highest-value, cleanest factual grounding
4. Verbal Identity & Brand Personality (IV)
5. Messaging & Positioning (V)
6. Company Identity & Brand Philosophy (I)
7. Sponsorship & Cultural Positioning (VI)
