# Slide rules: the layout law

Applied to every frame, in every genre. `scripts/check_deck.py` enforces the
measurable subset; the rest is your judgment on the rendered pages.

## Titles

- **One line. Always.** If a title wraps, rewrite it shorter — the fix is
  editorial, not typographic.
- Substantive slides get **assertion titles** carrying the takeaway
  ("Rollout timing is uncorrelated with municipal pre-trends");
  structural slides get short topic labels ("Data", "This paper",
  "Conclusion"). Sentence case throughout.
- The precise reading of the exhibit lives in **`\framesubtitle`**, not the
  title and not a body paragraph: title = claim, subtitle = "Log labor
  productivity; firm and year fixed effects; 95% CIs".
- Figure/table slides: the title states the message, never the axes
  ("Effects build over three years", not "Event-study estimates").

## Bullets and body text

- **1–4 top-level bullets** per slide (5 is the checker's hard cap). A
  results slide is often one figure + one bullet. Two nesting levels;
  never three.
- **Every bullet fits on one line.** Escalation path when it doesn't:
  1. Rewrite tighter (cut clauses, drop hedges).
  2. Split the payoff into an arrow run-in: `\item[$\Rightarrow$]` for the
     conclusion, `\item[$\checkmark$]` for done/confirmed items.
  3. Move the qualifying detail to `\framesubtitle` or the appendix.
  4. Last resort, one step down (`\small`) for that list only.
  Never wrap silently; never `\footnotesize` a whole slide to cram it.
- One sentence per line ≈ 45–75 characters (Goldsmith-Pinkham). Vertical
  whitespace (`\medskip`) between idea groups; hand-tune rhythm rather than
  cramming.
- Nothing on the slide you will not say out loud; screen space = emphasis
  (Shapiro). If attention lapsed for 30 seconds, the slide alone should let
  a listener catch back up (Meager).
- No prose walls: >15 text lines on a non-exhibit slide fails the checker.

## Overlays

- Allowed **only to build reasoning**: revealing an identification argument
  step by step, adding channels to a figure one at a time, "Data | Model"
  columns appearing after the data is absorbed.
- Always inside `\begin{overlayarea}{\textwidth}{<height>}` (or as full
  figure swaps `\includegraphics<1>…<2>`) so content never jumps between
  builds.
- Never `\pause` down a bullet list (the checker flags 3+ `\pause` per
  frame). If a reveal isn't rehearsed, show everything at once.
- Discussant decks: fully static.

## Math

- 1–3 display equations per slide, each introduced in words and each symbol
  explained *on that slide* — no one remembers notation across slides
  (Piazzesi). Prefer words to symbols where words are exact.
- Annotate terms in place: `\underbrace{...}_{\text{selection}}` with the
  economic meaning and sign; spotlight the term under discussion with
  `\KeyIdea` or an overlay color switch, one term at a time.
- Build the estimating equation in stages (baseline → add the interaction
  → add fixed effects), not as a wall. The full system, derivations, and
  proofs live in the appendix behind a button.
- Headline theoretical results go in a `ResultBox`.

## Color

- The theme's Okabe–Ito palette only: `cAccentA` (blue), `cAccentB`
  (vermillion), `cAccentC` (teal), `cAccentD` (amber), `cHighlight`
  (spotlight). Never raw `\color{red}`/`green` — and never a red-vs-green
  semantic pair (~8% of men can't see it).
- **One color per recurring concept, for the whole talk**: if the treatment
  effect is blue on slide 6, it is blue in every equation, bullet, figure
  line, and legend thereafter. The audience learns the mapping once.
- **Slide colors = figure colors.** Figures are rebuilt with the same hex
  values (see exhibit-surgery.md). A blue "broadband" line in the figure
  next to a vermillion "broadband" word in the text is a bug.
- ≤ 3 active concept colors on any one slide; `\KeyIdea` for the one
  punchline phrase, at most once per slide.

## Voice and anti-AI tells

- Slide text is telegraphic but human: verbs, concrete nouns, actual
  magnitudes. "Raises productivity 3.4%" not "has important implications
  for productivity".
- Banned on slides: "delve", "crucial(ly)", "notably", "landscape",
  "multifaceted", "novel insights", "shed light on", "it is worth noting",
  decorative em-dash chains, exclamation marks, rhetorical questions as
  filler, three-noun stacks.
- Vary slide composition: a deck where every slide is title + 3 bullets
  reads machine-made. Mix exhibit slides, one-bullet slides, a ResultBox
  slide, a picture-only slide with a `\Takeaway`.
- Numbers: 2–3 significant digits on slides; units on every number; state
  what the parentheses are (SEs? clustered by what?) in the exhibit note.

## Slide-count sanity (checker-visible symptoms of deeper problems)

| Symptom | Real problem |
|---|---|
| Title wraps | The claim isn't distilled yet |
| 6+ bullets | Two slides, or the point isn't chosen |
| Font shrunk to fit | The content belongs in the appendix |
| 4+ colors active | The color code has no meaning |
| `\pause` chain | Overlay as decoration |
| Wall of text | The paper is being pasted, not presented |
