# verification

Two skills for the same failure: believing something that has never been
observed doing what it claims.

```bash
claude plugin install verification@hard-won-skills --yes
```

A green check is not evidence until it has been seen red: passing proves it
ran, only failing proves it was looking at the right thing. And a library's
name, its field names and its README are all claims; the bytecode is what
runs. Both skills replace trust with one cheap observation, and both were
earned the usual way: a check that could never have failed got reported as
coverage, and a "fix" that set an option to its own default advertised a
guarantee nobody had added.

If you install only one plugin from this marketplace, make it this one: it
changes how you read every green checkmark that follows.

## The skills

| Skill | What it does |
|---|---|
| [`prove-the-check-can-fail`](skills/prove-the-check-can-fail/README.md) | Introduce the defect the check exists to catch, watch it go red, restore, report both halves, before trusting or citing it |
| [`verify-dependency-behaviour`](skills/verify-dependency-behaviour/README.md) | When docs are absent and naming is suggestive: read the artifact that actually runs, and quote the constant, not the conclusion |

Each skill's README carries its triggers and a worked example; the `SKILL.md`
beside it is the procedure the agent follows.
