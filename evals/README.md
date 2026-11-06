# Trigger evals

Seven cases for `claude plugin eval`: three requests econ-slides should handle
(paper to talk, discussant slides, retargeting a deck) and four it should
leave alone (a paper's discussion section, a PowerPoint deck, editing an
introduction, a referee report). The negative cases mirror the description's
boundaries: PowerPoint, Keynote and Google Slides are out of scope, paper
writing belongs to econ-write, and referee reports to econ-review. Each case has one `tool_used: Skill` grader; the negative
cases require zero econ-slides invocations in both arms.

Run them from the repository root, before and after any change to the skill's
`description`:

```bash
claude plugin eval . --runs 3
```

Each run is a full Claude Code session on your own credentials. Results go to
`evals/results/`, which is ignored by git.
