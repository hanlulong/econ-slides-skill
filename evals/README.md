# Trigger evals

Six cases for `claude plugin eval`: three requests econ-slides should handle
(paper to talk, discussant slides, retargeting a deck) and three it should
leave alone (a paper's discussion section, a PowerPoint deck, editing an
introduction). Each case has one `tool_used: Skill` grader; the negative
cases require zero econ-slides invocations in both arms.

Run them from the repository root, before and after any change to the skill's
`description`:

```bash
claude plugin eval . --runs 3
```

Each run is a full Claude Code session on your own credentials. Results go to
`evals/results/`, which is ignored by git.
