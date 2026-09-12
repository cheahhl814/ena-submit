---
name: ena-submit-debug
description: Phase 4 (optional) of ena-submit. Reads the failing stderr / Nextflow log / ENA Webin CLI receipt and matches it against the signature library (e.g. 'Webin authentication failed', 'checkm2_db not found', 'samplesheet missing column <X>', 'study accession already has private status'). Writes `debug-report.md` with diagnosis + fix.
version: 1.0.0
updated: "2026-09-12"
triggers:
  - "debug ENA submission failure"
  - "interpret seqsubmit error"
  - "Webin CLI error"
  - "nf-core/seqsubmit failed"
---

# Debug: ENA Submission Failures

> **v1.0.0.** Interpret nf-core/seqsubmit failures via the signature library and recommend a fix.

## Audience

This sub-skill serves two purposes:

- **AI Agents**: Triggered by the phrases above. Must run all evidence collection steps, then write the artifact.
- **Human Users**: Provides a transparent audit trail.

## When to Use This Skill

Use this skill if:

- Diagnose a failing `nextflow run nf-core/seqsubmit` invocation by matching the stderr against the signature library.
- Surface a concrete, runnable fix (e.g. reset Webin secrets, re-download the CheckM2 database, fix a samplesheet column).

Do NOT use this skill if:

- The run succeeded — you do not need a debug pass.

## 0. Inputs / Outputs contract

### Inputs (consumed)

| Path | Source | Required? |
| --- | --- | --- |
| `$RUN_DIR/run.log` | build/ena-submit-runner | yes |
| `$RUN_DIR/preflight.md` | preflight | yes |

### Outputs (produced)

| Path | Owner | Format | Notes |
| --- | --- | --- | --- |
| `$RUN_DIR/debug-report.md` | this skill | Markdown | diagnosis + fix |

### Verdict gate

The next phase **refuses to run** unless `$RUN_DIR/debug-report.md` overall verdict is `RECOVERABLE` or `RECOVERABLE`. A `BLOCKED` verdict stops the pipeline.

## 0.5 Ask-User Stop Points

This sub-skill has **5 stop points** (SP1–SP5). Each fires only when the evidence is ambiguous. The format is **Evidence + Recommend + Options**. If the evidence is unambiguous, the agent auto-picks the default and proceeds silently.

### SP1 — Failure signature not in library

| Trigger | Evidence check | Action |
| --- | --- | --- |
| the stderr / log does not match any of the 5+ entries in the signature library | grep against the signature library table below returns 0 matches | Ask: "The failure does not match a known signature. Pick: (A) run a short investigation loop (re-read docs-corpus, re-run with `-with-dump-hashes` etc.), (B) escalate to the user with the raw stderr, (C) abort" |

**Auto-pick when**: a known signature matches. Default: emit the diagnosis from the library entry..

### Operating rule

> **Auto-pick when the evidence is unambiguous; ask when the agent genuinely cannot decide.** When asking, present the evidence first, then the recommendation, then 2–4 concrete options. Do not ask "what do you want?" — ask "I see X, recommend Y, which one of A/B/C?"

## Description

This skill is the **failure-interpretation (debug)** phase of the ena-submit pipeline. It computes evidence and emits a machine-readable artifact plus a human-readable audit.

## Prerequisites

- **Environment**: pixi env with the required tools.
- **Upstream Evidence**: failing stderr + the preflight.md + run-summary.md that the failure invalidated..

## Procedure

The procedure has **three phases**: (1) gather inputs, (2) compute evidence, (3) write outputs.

### 1. Gather inputs from the user

Ask once, in one question batch if possible:

| Input | Required? | Default if absent |
| --- | --- | --- |
| Failing command + stderr | yes | ask |
| Mode (mags/bins/metagenomic_assemblies/reads) | yes | from params.json |

### 2. Compute evidence (always run; never skip)

Each numbered step produces a line in the evidence file and a column in the report.

```bash
# Match stderr against the signature library
grep -F -f sigs.txt $RUN_DIR/run.log
```

### 3. Write outputs

#### 3a) `debug-report.md` schema

```json
{
  "signature": "WEBIN_AUTH_FAILED",
  "verdict": "RECOVERABLE"
}
```

#### 3b) `debug-report.md` template

```markdown
# Debug: ENA Submission Failures report

Run:        $RUN_DIR
Generated:  <ISO8601>
Pipeline:   ena-submit v1.0.0

## Overall verdict

**RECOVERABLE** ✅ *(or RECOVERABLE ⚠️ / BLOCKED ❌)*

<one-line summary>

## Evidence

| Check | Verdict | Value | Threshold |
|---|---|---|---|
| Signature match | ✅ | WEBIN_AUTH_FAILED | one of the entries in the library |
| Recoverable vs blocked | ✅ | RECOVERABLE | non-blocked → re-run preflight or run |
| Suggested fix | ✅ | re-set Nextflow secrets | concrete command |

## Recommendations

- Apply the fix, then loop back to the relevant sub-skill (usually preflight or run).
- If BLOCKED, escalate to the user — the failure is environmental (e.g. ENA service outage, study-private conflict).

## Handoff

If verdict is `RECOVERABLE` or `RECOVERABLE`, hand off to: `(loops back to the sub-skill whose artifact the failure invalidated)`.

## Reproducibility

- debug-report.md: $RUN_DIR/debug-report.md
- evidence: $RUN_DIR/debug-evidence.txt
- this report: $RUN_DIR/debug-report.md (regenerable via this skill)
```

## Interpretation Guidelines

- **RECOVERABLE**: all evidence checks pass with confident values. Proceed to next phase.
- **RECOVERABLE**: at least one check is in warning territory. Proceed but surface the warnings.
- **BLOCKED**: at least one check fails. **Stop** and ask the user to fix.

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

- [ ] `$RUN_DIR/debug-report.md` exists and is valid JSON.
- [ ] `$RUN_DIR/debug-report.md` exists with overall verdict.
- [ ] `$RUN_DIR/debug-evidence.txt` exists with raw evidence.
- [ ] Overall verdict is `RECOVERABLE` or `RECOVERABLE` (not `BLOCKED`) before proceeding to next phase.

## Output contract

This skill produces:

- `$RUN_DIR/debug-report.md` (machine contract)
- `$RUN_DIR/debug-report.md` (human audit)
- `$RUN_DIR/debug-evidence.txt` (raw evidence)

It does **not** produce any other artifact. The next sub-skill does that.

## What NOT to do

- Do **not** skip the evidence collection. Every recommendation must be cited back to a measured value.
- Do **not** hand-write the artifact without running the evidence collection first.
- Do **not** override a `BLOCKED` verdict.
- Do **not** proceed to the next phase if the artifact is missing.
- Do **not** re-run this sub-skill without deleting the artifact first — the existence of the artifact is the stage-detection signal.

## Handoff

After this sub-skill writes `$RUN_DIR/debug-report.md` and `$RUN_DIR/debug-report.md`:

- **If verdict is `RECOVERABLE` or `RECOVERABLE`** → hand off to `(loops back to the sub-skill whose artifact the failure invalidated)`.
- **If verdict is `BLOCKED`** → stop. List the failing checks and ask the user to fix them.

The recommended message:

> Debug: ENA Submission Failures complete. Overall verdict: `<verdict>`. Next: invoke `(loops back to the sub-skill whose artifact the failure invalidated)` with the artifact defaults.
