#!/usr/bin/env python3
"""Check a speaker script against its deck, clock, and oral standard.

Usage:
    python3 scripts/check_script.py script.tex --deck talk.tex
        (--slot-minutes TOTAL | --speaking-minutes ALLOCATION)
        [--genre conference|seminar|job-talk|discussant] [--wpm 135] [--json]

Planned speech is the opening plus main-deck blocks. Conditional Q&A is
reported separately. With ``--slot-minutes``, planned speech is compared with
a genre window of the total session:

  conference   75--80 percent (20--25 percent for questions)
  seminar,     60--70 percent (30--40 percent for interruptions and
  job-talk     questions; Piazzesi plans to talk 1 hour of a 1.5-hour slot)
  discussant   at most 80 percent, with no floor

Only an overrun fails. A script below the window gets a warning: a scope
decision, never filler. With ``--speaking-minutes``, the stated allocation is
a ceiling for prepared speech and the question period is outside this check.
``--wpm`` (default 135) is the speaking pace; time a rehearsal and pass the
speaker's own rate, which is often slower in a second language.

Exit 1 on sync, timing overrun, missing-opening, or click failures; exit 2
when an input is missing; exit 3 if the checker crashes. Per-block word
ranges, minute-label discrepancies, an underrun, and sentence-shape notices
are review warnings rather than fill targets. Q&A blocks may cover a selected
subset of high-probability backups.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import re
import sys
from pathlib import Path
from typing import Any

BANNED = [
    "delve", "crucial", "crucially", "notably", "landscape", "multifaceted",
    "novel insights", "shed light on", "it is worth noting", "groundbreaking",
    "pivotal",
]
# Main-frame explanations are paper dependent: a theorem, design, or central
# exhibit may deserve materially more time than a transition slide.  Fixed word
# ceilings turn into accidental content rules and can encourage padding short
# blocks.  These absolute bounds are therefore used only when no minute budget
# is supplied.  Timed blocks are evaluated against their own delivery budget.
MAIN_UNTIMED_REVIEW_MIN, MAIN_UNTIMED_REVIEW_MAX = 8, 340
TIMED_BLOCK_TOLERANCE_SHARE = 0.20
TIMED_BLOCK_TOLERANCE_MINUTES = 0.25
ROADMAP_HARD_MIN, ROADMAP_PREFERRED_LO = 20, 25
ROADMAP_PREFERRED_HI, ROADMAP_HARD_MAX = 45, 60
OPENING_HARD_MIN, OPENING_HARD_MAX = 35, 100
OPENING_PREFERRED_LO, OPENING_PREFERRED_HI = 40, 70
QA_HARD_MIN, QA_HARD_MAX = 25, 120
QA_PREFERRED_LO, QA_PREFERRED_HI = 40, 90
# Planned speech as a share of a total session, by genre: (floor, ceiling).
# Conference slots keep 20--25% for questions. Seminars and job talks expect
# interruptions: Piazzesi plans 60 of 90 minutes; Startz says to leave time for
# them. A discussant has a ceiling only; shorter discussions are common.
# Piazzesi: "Stopping early is fine ... but not by more than 10 min".
EARLY_END_LIMIT_MINUTES = 10.0
SPEECH_SHARE = {
    "conference": (0.75, 0.80),
    "seminar": (0.60, 0.70),
    "job-talk": (0.60, 0.70),
    "discussant": (0.0, 0.80),
}


def strip_comments(src: str) -> str:
    """Remove unescaped TeX comments without deleting line breaks."""
    return re.sub(r"(?<!\\)%[^\n]*", "", src)


def tex_tree(path: Path, seen: set[Path] | None = None,
             root: Path | None = None) -> str:
    """Read TeX source with local input/include files expanded in place.

    A nested \\input is resolved from the main file's folder first, as TeX
    does when it builds there, then from the including file's folder.
    """
    if seen is None:
        seen = set()
    resolved = path.resolve()
    if resolved in seen or not resolved.is_file():
        return ""
    seen.add(resolved)
    root = root or resolved.parent
    try:
        src = strip_comments(resolved.read_text(encoding="utf-8",
                                                errors="replace"))
    except OSError:
        return ""

    def expand(match: re.Match) -> str:
        child = Path(match.group(1).strip())
        if child.suffix == "":
            child = child.with_suffix(".tex")
        if not child.is_absolute():
            child = next((folder / child for folder in (root, resolved.parent)
                          if (folder / child).is_file()), root / child)
        return tex_tree(child, seen, root)

    return re.sub(r"\\(?:input|include)\s*\{([^{}]+)\}", expand, src)


def braced(src: str, pos: int) -> tuple[str, int] | None:
    """Read one balanced {...} argument at or after pos."""
    while pos < len(src) and src[pos].isspace():
        pos += 1
    if pos >= len(src) or src[pos] != "{":
        return None
    start = pos + 1
    depth = 1
    pos += 1
    while pos < len(src) and depth:
        if src[pos] == "{" and (pos == 0 or src[pos - 1] != "\\"):
            depth += 1
        elif src[pos] == "}" and (pos == 0 or src[pos - 1] != "\\"):
            depth -= 1
        pos += 1
    if depth:
        return None
    return src[start:pos - 1], pos


def command_calls(src: str, name: str, nargs: int) -> list[dict[str, Any]]:
    """Return balanced arguments and positions for calls to a TeX command."""
    calls: list[dict[str, Any]] = []
    for match in re.finditer(rf"\\{re.escape(name)}\b", src):
        pos = match.end()
        args: list[str] = []
        for _ in range(nargs):
            parsed = braced(src, pos)
            if parsed is None:
                break
            value, pos = parsed
            args.append(value)
        if len(args) == nargs:
            calls.append({"start": match.start(), "end": pos, "args": args})
    return calls


def clean_title(value: str) -> str:
    """Return a synchronization key without purely visual TeX wrappers.

    A deck may color a recurring concept inside a frame title while the
    rehearsal script keeps the same words in plain text.  Those are the same
    spoken title and should synchronize.  Unknown semantic macros are kept so
    paper-specific title commands such as ``\\KeyQuestion`` still have to match.
    """
    wrappers = {
        "textcolor": (2, 1),
        "colorbox": (2, 1),
        "alert": (1, 0),
        "textbf": (1, 0),
        "textit": (1, 0),
        "emph": (1, 0),
        "underline": (1, 0),
        "texorpdfstring": (2, 0),
    }
    for _ in range(5):
        previous = value
        for name, (nargs, keep) in wrappers.items():
            for call in reversed(command_calls(value, name, nargs)):
                value = value[:call["start"]] + call["args"][keep] + value[call["end"]:]
        if value == previous:
            break
    value = value.replace(r"\&", "&").replace("~", " ")
    return re.sub(r"\s+", " ", value).strip()


def overlay_specs(body: str) -> list[str]:
    """Extract Beamer overlay specs from overlay-bearing TeX contexts.

    Searching for every ``<...>`` pair mistakes ordinary math such as
    ``0 < x < 2`` for presentation builds. Overlay specs follow commands,
    environments, items, or Beamer's list-wide ``[<+->]`` option.
    """
    located: list[tuple[int, str]] = []
    for match in re.finditer(
            r"\\[A-Za-z@]+\*?\s*(?:[+.]\s*)?<([^>]*)>", body):
        located.append((match.start(), match.group(1)))
    for match in re.finditer(
            r"\\begin\s*\{[^{}]+\}\s*<([^>]*)>", body):
        located.append((match.start(), match.group(1)))
    for match in re.finditer(
            r"\\begin\s*\{(?:itemize|enumerate)\}\s*"
            r"\[\s*<([^>]*)>\s*\]", body):
        located.append((match.start(), match.group(1)))
    located.sort(key=lambda item: item[0])
    return [spec for _position, spec in located]


def overlay_max(body: str) -> int:
    nums: list[int] = []
    relative_builds = 0
    for spec in overlay_specs(body):
        # handout:0 is a mode selector, not a presentation build.
        spec = re.sub(r"handout:\d+", "", spec)
        nums.extend(int(n) for n in re.findall(r"\d+", spec))
        if "+" in spec:
            relative_builds += 1
    return max(nums + ([relative_builds] if relative_builds else []), default=1)


def has_semantic_build(body: str) -> bool:
    """False when the only overlay specifications are bullet reveals."""
    without_items = re.sub(r"\\item\s*<[^>]*>", r"\\item", body)
    # Beamer's list-wide reveal shorthand is still just bullet sequencing:
    #   \begin{itemize}[<+->] ...
    without_items = re.sub(
        r"(\\begin\s*\{(?:itemize|enumerate)\})\s*\[\s*<[^>]*>\s*\]",
        r"\1",
        without_items,
    )
    without_items = re.sub(
        r"(\\begin\s*\{(?:itemize|enumerate)\})\s*<[^>]*>",
        r"\1",
        without_items,
    )
    # Spotlighting a term is a semantic transition; so are relative overlays
    # such as <+->. Only ordinary bullet reveals are intentionally ignored.
    return any(re.search(r"(?:\d|\+)", spec)
               for spec in overlay_specs(without_items))


def appendix_start(src: str) -> int:
    """Locate an actual appendix invocation after \begin{document}."""
    document = src.find("\\begin{document}")
    start = document if document >= 0 else 0
    positions: list[int] = []
    for pattern in (r"\\AppendixStart\b", r"\\appendix\b"):
        for match in re.finditer(pattern, src[start:]):
            pos = start + match.start()
            prefix = src[max(start, pos - 60):pos]
            if re.search(r"\\(?:new|renew|provide)command\s*\{\s*$", prefix):
                continue
            positions.append(pos)
    return min(positions, default=-1)


def deck_frames(deck_src: str) -> list[dict[str, Any]]:
    """Parse titled Beamer frames in source order."""
    src = strip_comments(deck_src)
    appendix_at = appendix_start(src)
    frames: list[dict[str, Any]] = []
    for match in re.finditer(r"\\begin\s*\{frame\}", src):
        pos = match.end()
        while pos < len(src) and src[pos].isspace():
            pos += 1
        # Beamer accepts an overlay specification before frame options.
        frame_overlay = ""
        if pos < len(src) and src[pos] == "<":
            end_overlay = src.find(">", pos + 1)
            if end_overlay < 0:
                continue
            frame_overlay = src[pos + 1:end_overlay]
            pos = end_overlay + 1
            while pos < len(src) and src[pos].isspace():
                pos += 1
        if pos < len(src) and src[pos] == "[":
            end_opt = src.find("]", pos + 1)
            if end_opt < 0:
                continue
            pos = end_opt + 1
        title = ""
        parsed_title = braced(src, pos)
        if parsed_title:
            title, pos = parsed_title
        end = src.find("\\end{frame}", pos)
        if end < 0:
            continue
        body = src[pos:end]
        if not title:
            ft = command_calls(body, "frametitle", 1)
            if ft:
                title = ft[0]["args"][0]
        title = clean_title(title)
        if title:
            overlay_source = body
            if frame_overlay:
                overlay_source = rf"\frameoverlay<{frame_overlay}>" + body
            frames.append({
                "title": title,
                "start": match.start(),
                "appendix": appendix_at >= 0 and match.start() > appendix_at,
                "overlays": overlay_max(overlay_source),
                "semantic_build": has_semantic_build(overlay_source),
            })
    return frames


def remove_command_with_arg(text: str, name: str) -> str:
    """Remove a command and its balanced first argument."""
    calls = command_calls(text, name, 1)
    for call in reversed(calls):
        text = text[:call["start"]] + " " + text[call["end"]:]
    return text


def zero_arg_macros(src: str) -> dict[str, str]:
    """Collect simple zero-argument newcommand definitions.

    Generated deck/script pairs keep spoken number phrases in results.tex.
    Counting an unexpanded ``\\ResMainSpoken`` as zero words understates the
    rehearsal clock, so expand the safe, common zero-argument subset.
    """
    macros: dict[str, str] = {}
    pattern = re.compile(
        r"\\(?:new|renew|provide)command\s*\{\s*\\([A-Za-z@]+)\s*\}"
    )
    for match in pattern.finditer(src):
        pos = match.end()
        while pos < len(src) and src[pos].isspace():
            pos += 1
        if pos < len(src) and src[pos] == "[":
            end = src.find("]", pos + 1)
            if end < 0 or src[pos + 1:end].strip() not in {"", "0"}:
                continue
            pos = end + 1
        parsed = braced(src, pos)
        if parsed is not None:
            macros[match.group(1)] = parsed[0]
    return macros


def expand_zero_arg_macros(text: str, macros: dict[str, str]) -> str:
    """Expand simple shared-result macros, including nested definitions."""
    if not macros:
        return text
    for _ in range(8):
        changed = False
        for name, value in macros.items():
            text, count = re.subn(
                rf"\\{re.escape(name)}\b", lambda _match, repl=value: repl, text
            )
            changed = changed or count > 0
        if not changed:
            break
    return text


def spoken_text(body: str, macros: dict[str, str] | None = None) -> str:
    """Reduce a script body to words that are intended to be spoken."""
    text = expand_zero_arg_macros(body, macros or {})
    for name in ("Cue", "footnote", "marginpar"):
        text = remove_command_with_arg(text, name)
    text = re.sub(r"\[\s*(?:Click\s*\d+|pause|beat|breathe)\s*\]", " ", text,
                  flags=re.I)
    text = re.sub(r"\\Click\s*\{\d+\}|\\Pause\b", " ", text)
    text = re.sub(r"\$[^$]*\$|\\\([^)]*\\\)|\\\[[^]]*\\\]", " ", text,
                  flags=re.S)
    text = text.replace(r"\&", "and").replace("~", " ")
    # Keep arguments of ordinary formatting commands; discard command names.
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:['\u2019-][A-Za-z0-9]+)*", text))


def time_minutes(hint: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:min|minute)", hint, re.I)
    return float(match.group(1)) if match else None


def opening_block(src: str, macros: dict[str, str] | None = None) -> dict[str, Any] | None:
    calls = command_calls(src, "scriptopening", 2)
    if calls:
        hint, body = calls[0]["args"]
        text = spoken_text(body, macros)
        return {"title": "Opening", "time": clean_title(hint),
                "minutes_hint": time_minutes(hint), "words": word_count(text),
                "body": text, "start": calls[0]["start"], "kind": "opening"}

    # Backward-compatible fallback for older templates.
    match = re.search(r"\\section\*?\{Opening[^}]*\}", src, re.I)
    if not match:
        return None
    end_match = re.search(r"\\section\*?\{Main deck[^}]*\}", src[match.end():], re.I)
    end = match.end() + end_match.start() if end_match else len(src)
    body = src[match.end():end]
    text = spoken_text(body, macros)
    return {"title": "Opening", "time": "unlabeled", "minutes_hint": None,
            "words": word_count(text), "body": text, "start": match.start(),
            "kind": "opening"}


def qa_start(src: str) -> int:
    # Search only the document body. The official template defines
    # \ScriptAppendix in the preamble and that definition itself contains a
    # literal "Q&A appendix" section; treating either as the split point makes
    # every real main block look conditional.
    document = src.find("\\begin{document}")
    start = document if document >= 0 else 0
    positions = []
    for match in re.finditer(r"\\ScriptAppendix\b", src[start:]):
        absolute = start + match.start()
        prefix = src[max(start, absolute - 60):absolute]
        if re.search(r"\\(?:new|renew|provide)command\s*\{\s*$", prefix):
            continue
        positions.append(absolute)
    if positions:
        return min(positions)
    qsec = re.search(
        r"\\section\*?\{[^}]*Q\s*\\?&\s*A[^}]*\}", src[start:], re.I
    )
    if qsec:
        positions.append(start + qsec.start())
    return min(positions, default=len(src) + 1)


def script_blocks(script_src: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    src = strip_comments(script_src)
    macros = zero_arg_macros(src)
    qpos = qa_start(src)
    blocks: list[dict[str, Any]] = []
    for call in command_calls(src, "scriptframe", 3):
        title, hint, body = call["args"]
        text = spoken_text(body, macros)
        kind = "qa" if call["start"] > qpos else "main"
        clicks = [int(match.group(1) or match.group(2)) for match in re.finditer(
            r"\[Click\s*(\d+)\]|\\Click\s*\{(\d+)\}", body, re.I
        )]
        blocks.append({
            "title": clean_title(title), "time": clean_title(hint),
            "minutes_hint": time_minutes(hint), "words": word_count(text),
            "clicks": clicks, "body": text, "start": call["start"], "kind": kind,
        })
    return opening_block(src, macros), blocks


def ordered_subsequence(needles: list[str], haystack: list[str]) -> bool:
    """Whether ``needles`` occur in order, preserving duplicate occurrences."""
    cursor = 0
    for needle in needles:
        while cursor < len(haystack) and haystack[cursor] != needle:
            cursor += 1
        if cursor == len(haystack):
            return False
        cursor += 1
    return True


def occurrence_lookup(items: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    """Map repeated titles by occurrence rather than assuming title uniqueness."""
    seen: defaultdict[str, int] = defaultdict(int)
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for item in items:
        title = item["title"]
        seen[title] += 1
        result[(title, seen[title])] = item
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("script", type=Path)
    ap.add_argument("--deck", type=Path, required=True)
    clock = ap.add_mutually_exclusive_group(required=True)
    clock.add_argument(
        "--slot-minutes", type=float,
        help="total session length, including the question period")
    clock.add_argument(
        "--speaking-minutes", type=float,
        help="explicit prepared-speaking allocation; Q&A is outside this clock")
    ap.add_argument(
        "--genre", choices=sorted(SPEECH_SHARE), default="conference",
        help=("talk genre for a --slot-minutes clock: conference 75-80%% "
              "speech, seminar/job-talk 60-70%%, discussant at most 80%% "
              "(default conference)"))
    ap.add_argument(
        "--wpm", type=float, default=135.0,
        help="speaking pace in words per minute (default 135); use the "
             "speaker's timed rehearsal rate")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.slot_minutes is not None and args.slot_minutes <= 0:
        ap.error("--slot-minutes must be positive")
    if args.speaking_minutes is not None and args.speaking_minutes <= 0:
        ap.error("--speaking-minutes must be positive")
    if args.wpm <= 0:
        ap.error("--wpm must be positive")

    for path in (args.script, args.deck):
        if not path.exists():
            print(f"error: {path} not found", file=sys.stderr)
            return 2

    frames = deck_frames(tex_tree(args.deck))
    opening, blocks = script_blocks(tex_tree(args.script))
    main_frames = [f for f in frames if not f["appendix"]]
    appendix_frames = [f for f in frames if f["appendix"]]
    main_blocks = [b for b in blocks if b["kind"] == "main"]
    qa_blocks = [b for b in blocks if b["kind"] == "qa"]
    findings: list[str] = []
    warnings: list[str] = []

    main_titles = [f["title"] for f in main_frames]
    appendix_titles = [f["title"] for f in appendix_frames]
    scripted_main_titles = [b["title"] for b in main_blocks]

    main_counts = Counter(main_titles)
    scripted_counts = Counter(scripted_main_titles)
    for title in sorted(main_counts.keys() | scripted_counts.keys()):
        extra = scripted_counts[title] - main_counts[title]
        missing = main_counts[title] - scripted_counts[title]
        if extra > 0:
            findings.append(
                f"[title-sync] {extra} main script occurrence(s) have no "
                f"main-deck frame: {title!r}")
        if missing > 0:
            findings.append(
                f"[title-sync] {missing} main-deck occurrence(s) have no "
                f"main script block: {title!r}")
    if main_counts == scripted_counts and scripted_main_titles != main_titles:
        findings.append("[title-sync] main script blocks are not in deck order")

    scripted_qa_titles = [b["title"] for b in qa_blocks]
    appendix_counts = Counter(appendix_titles)
    qa_counts = Counter(scripted_qa_titles)
    for title in sorted(qa_counts.keys()):
        extra = qa_counts[title] - appendix_counts[title]
        if extra > 0:
            findings.append(
                f"[title-sync] {extra} Q&A occurrence(s) have no appendix "
                f"frame: {title!r}")
    if all(qa_counts[title] <= appendix_counts[title] for title in qa_counts) \
            and not ordered_subsequence(scripted_qa_titles, appendix_titles):
        findings.append("[title-sync] Q&A blocks are not in appendix order")

    if opening is None:
        findings.append("[opening] no title-slide opening found; use \\scriptopening")
    elif not OPENING_HARD_MIN <= opening["words"] <= OPENING_HARD_MAX:
        warnings.append(
            f"[word-budget] opening: {opening['words']} words "
            f"(review range {OPENING_HARD_MIN}--{OPENING_HARD_MAX})")
    elif not OPENING_PREFERRED_LO <= opening["words"] <= OPENING_PREFERRED_HI:
        warnings.append(
            f"[word-budget] opening: {opening['words']} words; preferred "
            f"{OPENING_PREFERRED_LO}--{OPENING_PREFERRED_HI}")
    if opening:
        low = opening["body"].lower()
        for phrase in BANNED:
            if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", low):
                warnings.append(f"[oral-tells] opening: banned phrase {phrase!r}")
        for sentence in re.split(r"[.!?]", opening["body"]):
            count = word_count(sentence)
            if count > 35:
                warnings.append(
                    f"[oral-tells] opening: {count}-word sentence; split it for the ear")
                break

    frame_occurrences = {
        "main": occurrence_lookup(main_frames),
        "qa": occurrence_lookup(appendix_frames),
    }
    block_occurrences: dict[str, defaultdict[str, int]] = {
        "main": defaultdict(int),
        "qa": defaultdict(int),
    }
    for block in blocks:
        words = block["words"]
        if block["kind"] == "main":
            is_roadmap = block["title"].strip().lower() == "roadmap"
            if is_roadmap:
                if words < ROADMAP_HARD_MIN or words > ROADMAP_HARD_MAX:
                    warnings.append(
                        f"[word-budget] {block['title']!r}: {words} words "
                        f"(review range {ROADMAP_HARD_MIN}--{ROADMAP_HARD_MAX})")
                elif words < ROADMAP_PREFERRED_LO or words > ROADMAP_PREFERRED_HI:
                    warnings.append(
                        f"[word-budget] {block['title']!r}: {words} words; "
                        f"preferred {ROADMAP_PREFERRED_LO}--{ROADMAP_PREFERRED_HI}")
            elif block["minutes_hint"] is None and (
                words < MAIN_UNTIMED_REVIEW_MIN
                or words > MAIN_UNTIMED_REVIEW_MAX
            ):
                warnings.append(
                    f"[word-budget] {block['title']!r}: {words} words without "
                    "a minute budget; review the delivery load rather than "
                    "padding or trimming to a fixed target")
            if block["minutes_hint"] is None:
                warnings.append(
                    f"[time-label] {block['title']!r}: add a numeric minute budget")
            else:
                spoken_minutes = words / args.wpm
                tolerance = max(
                    TIMED_BLOCK_TOLERANCE_MINUTES,
                    block["minutes_hint"] * TIMED_BLOCK_TOLERANCE_SHARE,
                )
                if abs(block["minutes_hint"] - spoken_minutes) > tolerance:
                    warnings.append(
                        f"[time-label] {block['title']!r}: {block['time']} versus "
                        f"{spoken_minutes:.1f} min at {args.wpm:g} wpm; "
                        "rehearse, relabel, or redistribute substantive content")
        else:
            if words < QA_HARD_MIN or words > QA_HARD_MAX:
                warnings.append(
                    f"[word-budget] Q&A {block['title']!r}: {words} words "
                    f"(review range {QA_HARD_MIN}--{QA_HARD_MAX})")
            elif words < QA_PREFERRED_LO or words > QA_PREFERRED_HI:
                warnings.append(
                    f"[word-budget] Q&A {block['title']!r}: {words} words; "
                    f"preferred {QA_PREFERRED_LO}--{QA_PREFERRED_HI}")

        low = block["body"].lower()
        for phrase in BANNED:
            if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", low):
                warnings.append(f"[oral-tells] {block['title']!r}: banned phrase {phrase!r}")
        for sentence in re.split(r"[.!?]", block["body"]):
            count = word_count(sentence)
            if count > 35:
                warnings.append(
                    f"[oral-tells] {block['title']!r}: {count}-word sentence; split it for the ear")
                break
        first_sentence = re.split(r"[.!?]", block["body"], maxsplit=1)[0]
        first_words = word_count(first_sentence)
        if block["kind"] == "main" and first_words > 18:
            warnings.append(
                f"[oral-tells] {block['title']!r}: first sentence has "
                f"{first_words} words; consider a shorter declarative opening")

        kind = block["kind"]
        block_occurrences[kind][block["title"]] += 1
        frame = frame_occurrences[kind].get(
            (block["title"], block_occurrences[kind][block["title"]])
        )
        if frame and frame["semantic_build"] and frame["overlays"] > 1:
            expected = list(range(2, frame["overlays"] + 1))
            if block["clicks"] != expected:
                findings.append(
                    f"[click-sync] {block['title']!r}: semantic builds require "
                    f"clicks {expected}, found {block['clicks']}")
        if block["clicks"] and frame:
            if any(click < 2 for click in block["clicks"]):
                findings.append(
                    f"[click-sync] {block['title']!r}: click numbers start at 2")
            if not frame["semantic_build"]:
                findings.append(
                    f"[click-sync] {block['title']!r}: click tracks only bullet reveals; "
                    "change the evidence or remove the click")
            too_high = [click for click in block["clicks"] if click > frame["overlays"]]
            if too_high:
                findings.append(
                    f"[click-sync] {block['title']!r}: [Click {max(too_high)}] but "
                    f"the frame has only {frame['overlays']} builds")

    if opening and opening["minutes_hint"] is None:
        warnings.append("[time-label] opening: add a numeric minute budget")
    elif opening and opening["minutes_hint"] is not None:
        spoken_minutes = opening["words"] / args.wpm
        ratio = opening["minutes_hint"] / max(spoken_minutes, 0.01)
        if abs(opening["minutes_hint"] - spoken_minutes) > 0.25 \
                and not 0.50 <= ratio <= 1.75:
            warnings.append(
                f"[time-label] opening: {opening['time']} versus "
                f"{spoken_minutes:.1f} min at {args.wpm:g} wpm")

    planned_items = ([opening] if opening else []) + main_blocks
    planned_words = sum(item["words"] for item in planned_items)
    qa_words = sum(item["words"] for item in qa_blocks)
    talking_minutes = planned_words / args.wpm
    if args.slot_minutes is not None:
        timing_mode = "total-session"
        share_lo, share_hi = SPEECH_SHARE[args.genre]
        lower, upper = args.slot_minutes * share_lo, args.slot_minutes * share_hi
        qa_lower = args.slot_minutes - upper
        qa_upper = args.slot_minutes - lower
        window = (f"{lower:.1f}--{upper:.1f}" if share_lo
                  else f"at most {upper:.1f}")
        if talking_minutes > upper:
            findings.append(
                f"[total-time] {talking_minutes:.1f} min of planned speech at "
                f"{args.wpm:g} wpm overruns the {args.genre} window for a "
                f"{args.slot_minutes:g}-min total session ({window} min, "
                f"leaving at least {qa_lower:.1f} min for questions); cut "
                "scope, never speed up")
        elif talking_minutes < lower:
            shortfall = lower - talking_minutes
            if shortfall > EARLY_END_LIMIT_MINUTES:
                advice = (f"that is more than the {EARLY_END_LIMIT_MINUTES:g} "
                          "minutes early Piazzesi accepts, so add scope from "
                          "the paper or confirm that a shorter talk is intended")
            else:
                advice = ("ending a little early is fine, so decide on scope "
                          "rather than add filler")
            warnings.append(
                f"[total-time] {talking_minutes:.1f} min of planned speech at "
                f"{args.wpm:g} wpm ends {shortfall:.1f} min before the "
                f"{args.genre} window ({window} min of "
                f"{args.slot_minutes:g}); {advice}")
    else:
        timing_mode = "speaking-time"
        lower, upper = 0.0, args.speaking_minutes
        qa_lower = qa_upper = None
        if talking_minutes > args.speaking_minutes:
            findings.append(
                f"[total-time] {talking_minutes:.1f} min of planned speech "
                f"exceeds the explicit {args.speaking_minutes:g}-min speaking "
                "allocation; Q&A is outside this clock")

    hinted = [item["minutes_hint"] for item in planned_items]
    hinted_total = sum(value for value in hinted if value is not None)
    if hinted and all(value is not None for value in hinted):
        if args.slot_minutes is not None:
            # Only an overrun matters; a short plan is a scope decision.
            if hinted_total > upper:
                warnings.append(
                    f"[time-label] declared main budgets sum to {hinted_total:.1f} min, "
                    f"above the {args.genre} window ceiling of {upper:.1f} min")
        elif hinted_total > upper:
            warnings.append(
                f"[time-label] declared main budgets sum to {hinted_total:.1f} min; "
                f"explicit speaking allocation is {upper:.1f} min")
        if abs(hinted_total - talking_minutes) > max(1.0, talking_minutes * 0.30):
            warnings.append(
                f"[time-label] declared {hinted_total:.1f} min versus "
                f"{talking_minutes:.1f} min at {args.wpm:g} wpm")

    cumulative_words = 0
    block_report: list[dict[str, Any]] = []
    for item in planned_items:
        cumulative_words += item["words"]
        block_report.append({
            "title": item["title"], "kind": item["kind"],
            "words": item["words"], "time_hint": item["time"],
            "cumulative_minutes": round(cumulative_words / args.wpm, 1),
        })

    result = {
        "main_blocks": len(main_blocks),
        "qa_blocks": len(qa_blocks),
        "planned_words": planned_words,
        "qa_words": qa_words,
        "talking_minutes": round(talking_minutes, 1),
        "declared_minutes": round(hinted_total, 1),
        "timing_mode": timing_mode,
        "genre": args.genre if args.slot_minutes is not None else None,
        "wpm": args.wpm,
        "speech_window_minutes": ([round(lower, 1), round(upper, 1)]
                                  if args.slot_minutes is not None else None),
        "slot_minutes": args.slot_minutes,
        "speaking_minutes": args.speaking_minutes,
        "qa_minutes": ([round(qa_lower, 1),
                        round(qa_upper, 1) if lower else None]
                       if qa_lower is not None else None),
        "unused_speaking_minutes": (
            round(max(0.0, args.speaking_minutes - talking_minutes), 1)
            if args.speaking_minutes is not None else None),
        "blocks": block_report,
        "findings": findings,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.slot_minutes is not None:
            reserve = (f"{qa_lower:.1f}--{qa_upper:.1f}" if lower
                       else f"at least {qa_lower:.1f}")
            clock_summary = (
                f"{args.genre} window {window} min, Q&A reserve "
                f"{reserve} min of the {args.slot_minutes:g}-min session")
        else:
            clock_summary = (
                f"explicit speaking allocation {args.speaking_minutes:g} min; "
                "Q&A outside this clock")
        print(
            f"{args.script.name}: opening + {len(main_blocks)} main blocks, "
            f"{planned_words} words = {talking_minutes:.1f} min at "
            f"{args.wpm:g} wpm; "
            f"{clock_summary}; {len(qa_blocks)} conditional blocks / "
            f"{qa_words} words")
        for item in block_report:
            print(
                f"  {item['words']:>3} words  {item['cumulative_minutes']:>4.1f} min  "
                f"{item['title']}")
        for warning in warnings:
            print(f"  warning {warning}")
        for finding in findings:
            print(f"  {finding}")
        if not findings:
            if args.slot_minutes is not None:
                print("  in sync and within the total-session timing ceiling")
            else:
                print("  in sync and within the explicit speaking allocation")
    return 0 if not findings else 1


def run() -> int:
    """Run main(), keeping a crash (exit 3) apart from script findings (exit 1)."""
    for stream in (sys.stdout, sys.stderr):  # Windows ANSI code pages
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    try:
        return main()
    except Exception as exc:  # noqa: BLE001  (report, never pass as a verdict)
        import traceback
        traceback.print_exc()
        print(f"error: check_script.py crashed ({type(exc).__name__}: {exc}). "
              "No verdict was produced; exit 3 means the checker failed, not "
              "the script.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(run())
