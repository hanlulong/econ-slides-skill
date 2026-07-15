# Talk structures: arcs, budgets, and cuts

How to plan a deck for each genre. Slide counts are for *content* slides;
title, section dividers, and appendix ride free.

## Slide budget

Plan ≈ 1.5–2 minutes per content slide, slower for key exhibits. Verify by
rehearsal logic, not arithmetic: a key table takes 3 minutes to land; a
section divider takes 10 seconds. Never plan 1 slide/minute (Cochrane,
Piazzesi) — you must leave slides up long enough to digest.

| Clock | Content slides | Appendix |
|---|---|---|
| 12–15 min (conference) | 8–10 | 5–15 |
| 20 min (conference/workshop) | 10–13 | 10–20 |
| 45–60 min (seminar) | 18–25 | 15–30 |
| 75–90 min (seminar/job talk) | 25–32 | 20–40 |

The appendix is the length-and-detail dial (Bellemare's "Magic Appendix
Trick"): a lean main line plus linked backups lets the same deck absorb
interruptions, questions, and venue changes.

## The paper-talk arc (all lengths — the spine)

1. **Title** — `[plain]`, de-counted, disclaimer footnote if needed.
2. **Motivation, 1–2 slides max** — one striking fact, anecdote, or policy
   question with a single figure. Not "the literature has long...". You
   have two slides to make them care (Shapiro).
3. **Question** — the research question in one sentence, as economics (a
   policy counterfactual, a parameter, a test of theory), not as a gap in
   the literature. Antecedents appear here as 2–4 gray inline citations
   (`\graycite`), never as a review slide.
4. **This paper (the punchline slide)** — numbered contributions with the
   headline magnitude stated ("raises productivity by 3.4%"), the key
   result colored with `\KeyIdea`, closing on a bold **Implication:** line.
   Assume the audience is about to leave: after this slide they can state
   what you found.
5. **Data / setting** — sources, unit of observation, N, period, one line
   per measure. Hide the cleaning pipeline ("no one wants to see your
   underwear" — Shapiro); one summary-stats slide at most, or none.
6. **Identification / model** — the design in one picture where possible
   (timeline, DAG, event-study). State the key assumption in words and the
   single most important threat with your answer to it. Equations follow
   the math rules in slide-rules.md: build in stages, annotate terms,
   full system to appendix.
7. **Main result** — the one exhibit that carries the paper, surgically
   rebuilt (exhibit-surgery.md), with the economic magnitude translated
   ("one SD of exposure ⇒ 0.7%").
8. **Supporting results / mechanism** — one idea per frame; robustness is
   a single bullet or one compressed slide pointing to appendix buttons.
9. **Conclusion** — mirrors the "This paper" slide (same numbering, same
   phrasing) plus the same **Implication:** line. End on the takeaway; no
   "Thank you / Questions?" slide (thank them with your voice).
10. **Appendix** — `\AppendixStart`, then backups with `\BackButton`s:
    full tables, extra robustness, the fuller lit slide (deploy only if
    asked), anticipated-question slides.

Preview-of-results dispute, resolved: preview the *bottom line* as one crisp
sentence on the "This paper" slide (Shapiro, Startz, Evans), but do not
pre-run the results tables (Cochrane's objection is to the long preview).

## Genre adjustments

### Short conference talk (12–20 min)

- The ten-step spine at one frame each already overfills a 15-minute
  budget. Merge to fit: motivation and question into one frame; policy
  implications into the conclusion; data to one frame or a single bullet
  on the design slide. A typical 15-minute deck: motivation+question,
  this-paper, data, design, main result, mechanism, conclusion — seven
  content frames plus appendix.
- Choose **model OR results**; the loser gets one slide (Evans).
- Cut in this order when over budget: literature → data minutiae →
  summary stats → theory (assumptions + predictions only) → robustness →
  maps/photos. Never cut the punchline slide or the main exhibit.
- Results as a chart, not a table, wherever possible.
- Assume zero protected time; the punchline must land by minute 3.

### Department seminar (60–90 min)

- The Sargent rule: reach the setup/model inside 10 minutes (Piazzesi).
- Expect combat: know which slides you will skip if behind and which
  appendix slides to deploy if ahead. Mark them while drafting.
- Orient at every transition ("model's on the table; now identification"),
  with roadmap slides that gray out completed sections.
- Design the opening to exploit the 10–15-minute protected window where it
  exists: question, contribution, preview land before hands go up.

### Job market talk (75–90 min)

- The talk's job is the job: engineer the **two-sentence takeaway** —
  (a) the exciting thing they learned, (b) the clever thing you did
  (Startz) — and land both in the first five minutes.
- Pitch to smart generalists ("JEP, not Econometrica"): most of the room
  has not read past your abstract.
- Three-act structure: accessible opening → one controlled technical dive
  that proves mastery → resurface to implications everyone follows.
- Point out your own holes first, credibly and briefly; a richer appendix
  than any other genre (the five people who read the paper will ask).

### Theory and structural talks (corpus is thin here; skill defaults)

- Replace the Data slide with **Environment** (agents, timing, information,
  in plain English before any math) and identification with **Mechanism**:
  the one economic force that drives the result, ideally as a picture.
- Propositions: statement in words → formal statement → intuition; proof
  sketch only if it *is* the contribution; full proof to appendix.
- Structural: model fit gets one exhibit ("Data | Model" table); the
  counterfactual is the punchline and gets the main-result treatment.
- A worked toy example built progressively across overlays is the seminar
  workhorse for hard theory — budget 2–3 slides for it in long formats.

## Retargeting a deck to a new venue

Never fork by commenting out frames (unmaintainable — the graveyard master
anti-pattern). Procedure:

1. Treat the richest existing deck as source of truth.
2. Rebuild the target as a **fresh file** that `\input`s shared frame
   modules or copies frames forward; drop whole frames per the cut order
   above rather than thinning every frame.
3. Anything cut from the main line moves to the appendix before it is
   deleted outright — questions follow the paper, not the venue.
4. Update `\date`, venue line, and the slide budget; recompile and re-run
   the checks; visually re-inspect (cuts orphan `\hyperlink` targets —
   `check_deck` and the compile log catch dead references).
5. Same paper, shorter clock ⇒ re-choose emphasis (Shapiro's scaling rule):
   a 15-minute cut is a different talk about the same paper, not the
   90-minute deck played fast.
