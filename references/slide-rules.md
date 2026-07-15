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
- **Top-anchor sparse text frames.** Beamer vertically centers, which
  leaves a dead band under the title on short slides. For text-only frames
  with ≤4 bullets use `\begin{frame}[t]{...}` with a `\medskip` after the
  title, so the body sits near the title the way a hand-tuned deck does.
  Exhibit frames stay centered.
- **Bullet spacing by role** (theme default is 0.45em; override in-list
  with `\setlength{\itemsep}{...}` after `\begin{itemize}`): contribution
  and conclusion lists breathe at ~0.9em; ordinary content lists 0.45–0.6em;
  genuinely dense lists may tighten to ~0.3em before splitting the frame.
- **Generous between ideas, tight within an idea.** An arrow-led
  sub-conclusion belongs to the bullet above it — pull it up so it hugs
  its parent instead of floating a full itemsep away:
  `\item[$\Rightarrow$]` preceded by `\vspace*{-0.5em}`. The eye then
  reads bullet+arrow as one unit and the wide gaps as idea boundaries.
- Single-bullet frames: tighten the indent locally with
  `{\setlength{\leftmargini}{1em} \begin{itemize} ... \end{itemize}}`.
- Nothing on the slide you will not say out loud; screen space = emphasis
  (Shapiro). If attention lapsed for 30 seconds, the slide alone should let
  a listener catch back up (Meager).
- No prose walls: >15 text lines on a non-exhibit slide fails the checker.

## Filling space with depth, not breadth

Minimal is the floor, not the goal: a frame with two short bullets over a
sea of white is a missed opportunity. When a frame has room AND the paper
has something genuinely interesting to add, deepen the *same* point — never
add a new one. The enrichment moves, in order of preference:

1. **A one-line framing sentence** above a numbered list — the "This
   paper" and Conclusion slides open with one plain-text line setting up
   the contributions, never with a bare enumerate.
2. **Sharper `\framesubtitle`** — the precise reading of the exhibit
   (sample, units, specification) instead of a vague one.
3. **An arrow-led intuition line** — `\item[$\Rightarrow$]` carrying the
   economic logic or the "so what" of the bullet above it.
4. **A gray parenthetical** — `\graycite{}` with the closest antecedent, a
   benchmark magnitude ("about half the college wage premium"), or the
   institutional detail that pre-empts a question.
5. **A small annotated equation** — one term `\underbrace`d with its
   meaning, if the mechanism is the point.
6. **A larger exhibit** — let the figure fill the frame rather than pad
   the text.

Never enrich with filler, a second idea, or detail the speaker will not
say out loud. If nothing interesting exists to add, the white space stays —
space is emphasis.

## Color consistency across the deck

Declare the concept→color map once, before drafting, at the top of the
`.tex`, and alias the concepts so slides never reference raw accents:

```latex
% COLOR MAP (one color per concept, held for the whole talk):
%   treatment/broadband = cAccentA   mechanism/model = cAccentC
\colorlet{cTreat}{cAccentA}
\colorlet{cModel}{cAccentC}
```

Slides and rebuilt figures use `cTreat`/`cModel`, so a concept cannot
change color between slide 6 and slide 12. Audit the map during the visual
pass: same concept, same color, every appearance — and no accent used
without a meaning.

## Overlays

- Allowed **only to build reasoning**: revealing an identification argument
  step by step, adding channels to a figure one at a time, "Data | Model"
  columns appearing after the data is absorbed.
- Always inside `\begin{overlayarea}{\textwidth}{<height>}` (or as full
  figure swaps `\includegraphics<1>…<2>`) so content never jumps between
  builds.
- **Make every `\only`/figure swap handout-safe**: tag which variant the
  handout keeps — `\only<1|handout:0>{build}\only<2|handout:1>{final}` —
  otherwise `[handout]` mode overprints all variants on one slide.
  `\item<2->` needs no spec (it simply shows).
- Never `\pause` down a bullet list (the checker flags 3+ `\pause` per
  frame). If a reveal isn't rehearsed, show everything at once.
- Discussant decks: fully static.

## Math

- 1–3 display equations per slide, each introduced in words and each symbol
  explained *on that slide* — no one remembers notation across slides
  (Piazzesi). Prefer words to symbols where words are exact.
- Build the estimating equation in stages (baseline → add the interaction
  → add fixed effects), not as a wall. The full system, derivations, and
  proofs live in the appendix behind a button.
- Headline theoretical results go in a `ResultBox`.

### Defining new notation (the discipline)

Every **key, new, or nonstandard** symbol is defined at its first
appearance, on the same slide, and the definition is *economic*, not
lexical:

1. **The `where` line**, directly under the display, in plain economic
   language: "where $\kappa$ governs how fast prices adjust and
   $\rho$ is the persistence of the shock" — never "where $\kappa$ is a
   parameter". If the `where` line needs more than one sentence, the
   equation carries too many new symbols — split the build.
2. **In-place naming for composite terms**:
   `\underbrace{...}_{\text{adjustment cost $>0$}}` — the economic name
   *plus the sign* whenever the sign drives the argument; compact sign
   tags via `\overbrace{...}^{\scriptscriptstyle(+)}`.
3. **Color as identity for the talk's key objects**: introduce a central
   object once with its concept color and name
   (`\textcolor{cModel}{u^{NK}}`, per the color map); afterwards the color
   alone carries the identity across every equation, bullet, and figure.
4. **Spotlight one term at a time** when walking a decomposition:
   `{\color<2>{cHighlight}\underbrace{...}_{...}}` — discuss term by term
   over overlays, never all at once.
5. **Re-ground returning notation**: when a symbol reappears after several
   slides, remind rather than assume — a parenthetical "(recall $\kappa$ =
   price-adjustment cost)" or the `\framesubtitle`.

What NOT to define: standard objects (logs, expectations, $i$/$t$
subscripts, OLS notation). Defining the obvious clutters exactly where
clean definition should stand out — knowing what needs no definition is
half the discipline.

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
