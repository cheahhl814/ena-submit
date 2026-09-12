---
name: ena-submit-battle-test
description: Phase 5 of ena-submit. Runs 8+ structural smoke tests: frontmatter coherence across all 5 sub-skill SKILL.md files, signature-library completeness (≥ 3 entries each in preflight/qc/debug), docs-corpus freshness (every tool in pixi.toml has docs-corpus/<tool>/README.md), pixi.toml parses, bin/skill-update-check.py parses, README hygiene (no machine-specific paths, no unfilled slots), git init status. Writes `battle-test-report.md` with PASS/PASS-WITH-WARNINGS/FAIL.
version: 1.0.0
updated: "2026-09-12"
triggers:
  - "battle-test the skill"
  - "verify skill integrity"
  - "structural smoke test"
  - "skill quality gate"
---

# Battle-Test: Skill Structural Integrity

> **v1.0.0.** Verify the new skill is structurally sound before declaring it ready.

## Audience

This sub-skill serves two purposes:

- **AI Agents**: Triggered by the phrases above. Must run all evidence collection steps, then write the artifact.
- **Human Users**: Provides a transparent audit trail.

## When to Use This Skill

Use this skill if:

- Verify the new skill is structurally sound (frontmatter coherence, signature-library completeness, docs-corpus freshness, pixi.toml parse, README hygiene).
- Get a PASS / PASS-WITH-WARNINGS / FAIL verdict before shipping the skill to GitHub.

Do NOT use this skill if:

- You have not yet scaffolded the skill — run `build/skill-builder` first.

## 0. Inputs / Outputs contract

### Inputs (consumed)

| Path | Source | Required? |
| --- | --- | --- |
| `$RUN_DIR/SKILL.md` | this skill | yes |
| `$RUN_DIR/README.md` | this skill | yes |
| `$RUN_DIR/pixi.toml` | this skill | yes |
| `$RUN_DIR/preflight/, build/, qc/, debug/ sub-skill SKILL.md files` | this skill | yes |
| `$RUN_DIR/docs-corpus/` | this skill | yes |

### Outputs (produced)

| Path | Owner | Format | Notes |
| --- | --- | --- | --- |
| `$RUN_DIR/battle-test-report.md` | this skill | Markdown | PASS / PASS-WITH-WARNINGS / FAIL |

### Verdict gate

The next phase **refuses to run** unless `$RUN_DIR/battle-test-report.md` overall verdict is `PASS` or `PASS-WITH-WARNINGS`. A `FAIL` verdict stops the pipeline.

## 0.5 Ask-User Stop Points

This sub-skill has **3 stop points** (SP1–SP3). Each fires only when the evidence is ambiguous. The format is **Evidence + Recommend + Options**. If the evidence is unambiguous, the agent auto-picks the default and proceeds silently.

### SP1 — Frontmatter version mismatch across sub-skills

| Trigger | Evidence check | Action |
| --- | --- | --- |
| the version field in any sub-skill's `SKILL.md` does not match the orchestrator's `version` | grep -E '^version:' across all SKILL.md files in this skill | Ask: "Sub-skill `<X>` declares version `<V1>` but the orchestrator declares `<V2>`. Pick: (A) bump `<X>` to `<V2>`, (B) downgrade the orchestrator to `<V1>`, (C) accept the mismatch (PASS-WITH-WARNINGS)" |

**Auto-pick when**: all versions match. Default: proceed..

### Operating rule

> **Auto-pick when the evidence is unambiguous; ask when the agent genuinely cannot decide.** When asking, present the evidence first, then the recommendation, then 2–4 concrete options. Do not ask "what do you want?" — ask "I see X, recommend Y, which one of A/B/C?"

## Description

This skill is the **structural verification (battle-test)** phase of the ena-submit pipeline. It computes evidence and emits a machine-readable artifact plus a human-readable audit.

## Prerequisites

- **Environment**: pixi env with the required tools.
- **Upstream Evidence**: the new skill itself (SKILL.md, README.md, pixi.toml, all sub-skill SKILL.md files, docs-corpus/, bin/skill-update-check.py)..

## Procedure

The procedure has **three phases**: (1) gather inputs, (2) compute evidence, (3) write outputs.

### 1. Gather inputs from the user

Ask once, in one question batch if possible:

| Input | Required? | Default if absent |
| --- | --- | --- |
| `--execution` flag (optional — runs real tools if available) | no | off |

### 2. Compute evidence (always run; never skip)

Each numbered step produces a line in the evidence file and a column in the report.

```bash
# Frontmatter version coherence
grep -E '^version:' $(find . -name 'SKILL.md')
```

### 3. Write outputs

#### 3a) `battle-test-report.md` schema

```json
{
  "checks_passed": "8",
  "verdict": "PASS"
}
```

#### 3b) `battle-test-report.md` template

```markdown
# Battle-Test: Skill Structural Integrity report

Run:        $RUN_DIR
Generated:  <ISO8601>
Pipeline:   ena-submit v1.0.0

## Overall verdict

**PASS** ✅ *(or PASS-WITH-WARNINGS ⚠️ / FAIL ❌)*

<one-line summary>

## Evidence

| Check | Verdict | Value | Threshold |
|---|---|---|---|
| Frontmatter coherence (5 SKILL.md files) | ✅ | 8/8 | all pass |
| Signature-library completeness | ✅ | ≥ 3 entries per sub-skill | ≥ 3 |
| Docs-corpus freshness | ✅ | 7/7 tools covered | all tools in pixi.toml covered |
| pixi.toml parses | ✅ | pixi lock --dry-run | exit 0 |
| bin/skill-update-check.py parses | ✅ | py_compile | exit 0 |
| README hygiene (no machine paths, no unfilled slots) | ✅ | 0 hits | 0 hits |
| git init status | ✅ | clean | initialised + clean |
| .gitignore covers work/ + docs-corpus/.fingerprints | ✅ | present | both entries present |

## Recommendations

- If PASS, the skill is ready to ship. `git add -A && git commit -m 'v1.0.0: initial scaffold' && git push -u origin master` and `rsync -av --delete` to `~/.pi/agent/skills/ena-submit/`.
- If PASS-WITH-WARNINGS, surface the warnings and decide whether to ship or fix first.

## Handoff

If verdict is `PASS` or `PASS-WITH-WARNINGS`, hand off to: `(end of pipeline — ship the skill)`.

## Reproducibility

- battle-test-report.md: $RUN_DIR/battle-test-report.md
- evidence: $RUN_DIR/battle-test-evidence.txt
- this report: $RUN_DIR/battle-test-report.md (regenerable via this skill)
```

## Interpretation Guidelines

- **PASS**: all evidence checks pass with confident values. Proceed to next phase.
- **PASS-WITH-WARNINGS**: at least one check is in warning territory. Proceed but surface the warnings.
- **FAIL**: at least one check fails. **Stop** and ask the user to fix.

## Troubleshooting — Signature library

When this sub-skill fails or produces unexpected output, match the failure against these patterns. **Always** read the actual error before concluding.

| Signature in stderr / log | Likely cause | Suggested fix |
| --- | --- | --- |
| `command not found` | pixi env missing the tool | `pixi add <tool>`. |
| `ModuleNotFoundError: pkg_resources` | Python ≥ 3.12 + setuptools ≥ 81 | `pixi add 'setuptools<81'`. |
| `disk full` | Less than recommended disk space | Free up disk or move `$RUN_DIR` to a larger disk. |
| `Permission denied` | Wrong ownership | `chown -R $USER:$USER $RUN_DIR`. |
| `no such file or directory` | Input path wrong | Verify the path with `ls -la`. |
| `verdict: BEHIND-BY-N` from `pixi run update-check` | Upstream `github.com/cheahhl814/ena-submit` is ahead of the deployed copy | Re-deploy per AGENTS.md §4a: `rsync -a --exclude='.git' @skills/ena-submit/ ~/.pi/agent/skills/ena-submit/` then `diff -rq` to verify. The script prints the canonical fix on `BEHIND-BY-N`. |
| `verdict: OFFLINE` / `NO-ORIGIN` from `pixi run update-check` | No network or no `origin` remote — informational, exit code 2 | Re-run when online, or `git remote add origin https://github.com/cheahhl814/ena-submit.git` if the remote is missing. |

## Verification

- [ ] `$RUN_DIR/battle-test-report.md` exists and is valid JSON.
- [ ] `$RUN_DIR/battle-test-report.md` exists with overall verdict.
- [ ] `$RUN_DIR/battle-test-evidence.txt` exists with raw evidence.
- [ ] Overall verdict is `PASS` or `PASS-WITH-WARNINGS` (not `FAIL`) before proceeding to next phase.

## Output contract

This skill produces:

- `$RUN_DIR/battle-test-report.md` (machine contract)
- `$RUN_DIR/battle-test-report.md` (human audit)
- `$RUN_DIR/battle-test-evidence.txt` (raw evidence)

It does **not** produce any other artifact. The next sub-skill does that.

## What NOT to do

- Do **not** skip the evidence collection. Every recommendation must be cited back to a measured value.
- Do **not** hand-write the artifact without running the evidence collection first.
- Do **not** override a `FAIL` verdict.
- Do **not** proceed to the next phase if the artifact is missing.
- Do **not** re-run this sub-skill without deleting the artifact first — the existence of the artifact is the stage-detection signal.

## Handoff

After this sub-skill writes `$RUN_DIR/battle-test-report.md` and `$RUN_DIR/battle-test-report.md`:

- **If verdict is `PASS` or `PASS-WITH-WARNINGS`** → hand off to `(end of pipeline — ship the skill)`.
- **If verdict is `FAIL`** → stop. List the failing checks and ask the user to fix them.

The recommended message:

> Battle-Test: Skill Structural Integrity complete. Overall verdict: `<verdict>`. Next: invoke `(end of pipeline — ship the skill)` with the artifact defaults.
