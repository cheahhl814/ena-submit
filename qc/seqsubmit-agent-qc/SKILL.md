---
name: seqsubmit-agent-qc
description: Phase 3 of seqsubmit-agent. Parses the per-mode output directory (reads/ or metagenomic_assemblies/ or mags/, bins/) and `multiqc/`, collects accession numbers, MAGs/bins manifest, coverage files, and the MultiQC report. Writes `seqsubmit-report.md` (the per-submission audit report) and `qc-summary.md` (the machine-readable summary).
version: 1.0.0
updated: "2026-09-12"
triggers:
  - "build ENA submission report"
  - "summarise accession numbers"
  - "qc seqsubmit output"
  - "collect MAG accessions"
---

# ENA Submission QC + Accession Summary

> **v1.0.0.** Aggregate the per-mode accession receipts and write the final submission report.

## Audience

This sub-skill serves two purposes:

- **AI Agents**: Triggered by the phrases above. Must run all evidence collection steps, then write the artifact.
- **Human Users**: Provides a transparent audit trail.

## When to Use This Skill

Use this skill if:

- Collect accession numbers per sample after a successful ENA submission.
- Aggregate the per-mode outputs (manifest TSVs, MultiQC report, MAGs/bins metadata) into a single audit-trail report.

Do NOT use this skill if:

- The pipeline run failed — route to `debug/seqsubmit-agent-debug` first.

## 0. Inputs / Outputs contract

### Inputs (consumed)

| Path | Source | Required? |
| --- | --- | --- |
| `$RUN_DIR/run-summary.md` | build/seqsubmit-agent-runner | yes |
| `$RUN_DIR/outdir/<mode>/` | build | yes (mode-specific) |
| `$RUN_DIR/outdir/multiqc/` | build | no (but aggregated when present) |

### Outputs (produced)

| Path | Owner | Format | Notes |
| --- | --- | --- | --- |
| `$RUN_DIR/seqsubmit-report.md` | this skill | Markdown | per-submission audit report (the deliverable) |
| `$RUN_DIR/qc-summary.md` | this skill | Markdown | machine-readable summary table |

### Verdict gate

The next phase **refuses to run** unless `$RUN_DIR/seqsubmit-report.md` overall verdict is `GO` or `GO-WITH-WARNINGS`. A `NO-GO` verdict stops the pipeline.

## 0.5 Ask-User Stop Points

This sub-skill has **3 stop points** (SP1–SP3). Each fires only when the evidence is ambiguous. The format is **Evidence + Recommend + Options**. If the evidence is unambiguous, the agent auto-picks the default and proceeds silently.

### SP1 — Outdir missing per-mode output

| Trigger | Evidence check | Action |
| --- | --- | --- |
| `outdir/<mode>/` is missing the expected submission-receipt files (e.g. `*_webin_cli.log`, `manifest.tsv`, `genome_metadata.tsv`) | file-glob against the mode-specific expected outputs | Ask: "The per-mode output dir is missing expected submission files. Pick: (A) the run did not actually submit (re-run with `--test_upload false`), (B) the run hit an error mid-flight (route to debug), (C) accept the partial output and report what's there" |

**Auto-pick when**: all expected files are present. Default: proceed..

### Operating rule

> **Auto-pick when the evidence is unambiguous; ask when the agent genuinely cannot decide.** When asking, present the evidence first, then the recommendation, then 2–4 concrete options. Do not ask "what do you want?" — ask "I see X, recommend Y, which one of A/B/C?"

## Description

This skill is the **output (qc)** phase of the seqsubmit-agent pipeline. It computes evidence and emits a machine-readable artifact plus a human-readable audit.

## Prerequisites

- **Environment**: pixi env with the required tools.
- **Upstream Evidence**: run-summary.md + the per-mode outdir/ tree produced by nf-core/seqsubmit..

## Procedure

The procedure has **three phases**: (1) gather inputs, (2) compute evidence, (3) write outputs.

### 1. Gather inputs from the user

Ask once, in one question batch if possible:

| Input | Required? | Default if absent |
| --- | --- | --- |
| Submission mode (mags/bins/metagenomic_assemblies/reads) | yes | from params.json |

### 2. Compute evidence (always run; never skip)

Each numbered step produces a line in the evidence file and a column in the report.

```bash
# Mode-specific output inventory
ls -la $OUTDIR/$MODE/
```

### 3. Write outputs

#### 3a) `qc-summary.md` schema

```json
{
  "samples_submitted": "10",
  "verdict": "GO"
}
```

#### 3b) `seqsubmit-report.md` template

```markdown
# ENA Submission QC + Accession Summary report

Run:        $RUN_DIR
Generated:  <ISO8601>
Pipeline:   seqsubmit-agent v1.0.0

## Overall verdict

**GO** ✅ *(or GO-WITH-WARNINGS ⚠️ / NO-GO ❌)*

<one-line summary>

## Evidence

| Check | Verdict | Value | Threshold |
|---|---|---|---|
| Per-mode output dir present | ✅ | outdir/mags/ | exists |
| Accession receipts | ✅ | 10/10 samples have accessions | ≥ 90% of samples have non-empty accessions |
| MAGs/bins manifest (mags/bins mode) | ✅ | genome_metadata.tsv | exists when mode is mags/bins |
| MultiQC report | ✅ | multiqc_report.html | exists |
| Pipeline info complete | ✅ | trace + timeline + report | all 3 present |

## Recommendations

- Submit is complete. `seqsubmit-report.md` is the audit-trail deliverable.
- If verdict is NO-GO (failed samples), surface the per-sample failure to the user; they can re-run with `--test_upload false` to actually submit.

## Handoff

If verdict is `GO` or `GO-WITH-WARNINGS`, hand off to: `(end of pipeline — deliverable is seqsubmit-report.md)`.

## Reproducibility

- qc-summary.md: $RUN_DIR/qc-summary.md
- evidence: $RUN_DIR/qc-evidence.txt
- this report: $RUN_DIR/seqsubmit-report.md (regenerable via this skill)
```

## Interpretation Guidelines

- **GO**: all evidence checks pass with confident values. Proceed to next phase.
- **GO-WITH-WARNINGS**: at least one check is in warning territory. Proceed but surface the warnings.
- **NO-GO**: at least one check fails. **Stop** and ask the user to fix.

## Troubleshooting — Signature library

When this sub-skill fails or produces unexpected output, match the failure against these patterns. **Always** read the actual error before concluding.

| Signature in stderr / log | Likely cause | Suggested fix |
| --- | --- | --- |
| `command not found` | pixi env missing the tool | `pixi add <tool>`. |
| `ModuleNotFoundError: pkg_resources` | Python ≥ 3.12 + setuptools ≥ 81 | `pixi add 'setuptools<81'`. |
| `disk full` | Less than recommended disk space | Free up disk or move `$RUN_DIR` to a larger disk. |
| `Permission denied` | Wrong ownership | `chown -R $USER:$USER $RUN_DIR`. |
| `no such file or directory` | Input path wrong | Verify the path with `ls -la`. |
| `verdict: BEHIND-BY-N` from `pixi run update-check` | Upstream `github.com/cheahhl814/seqsubmit-agent` is ahead of the deployed copy | Re-deploy per AGENTS.md §4a: `rsync -a --exclude='.git' @skills/seqsubmit-agent/ ~/.pi/agent/skills/seqsubmit-agent/` then `diff -rq` to verify. The script prints the canonical fix on `BEHIND-BY-N`. |
| `verdict: OFFLINE` / `NO-ORIGIN` from `pixi run update-check` | No network or no `origin` remote — informational, exit code 2 | Re-run when online, or `git remote add origin https://github.com/cheahhl814/seqsubmit-agent.git` if the remote is missing. |

## Verification

- [ ] `$RUN_DIR/qc-summary.md` exists and is valid JSON.
- [ ] `$RUN_DIR/seqsubmit-report.md` exists with overall verdict.
- [ ] `$RUN_DIR/qc-evidence.txt` exists with raw evidence.
- [ ] Overall verdict is `GO` or `GO-WITH-WARNINGS` (not `NO-GO`) before proceeding to next phase.

## Output contract

This skill produces:

- `$RUN_DIR/qc-summary.md` (machine contract)
- `$RUN_DIR/seqsubmit-report.md` (human audit)
- `$RUN_DIR/qc-evidence.txt` (raw evidence)

It does **not** produce any other artifact. The next sub-skill does that.

## What NOT to do

- Do **not** skip the evidence collection. Every recommendation must be cited back to a measured value.
- Do **not** hand-write the artifact without running the evidence collection first.
- Do **not** override a `NO-GO` verdict.
- Do **not** proceed to the next phase if the artifact is missing.
- Do **not** re-run this sub-skill without deleting the artifact first — the existence of the artifact is the stage-detection signal.

## Handoff

After this sub-skill writes `$RUN_DIR/seqsubmit-report.md` and `$RUN_DIR/qc-summary.md`:

- **If verdict is `GO` or `GO-WITH-WARNINGS`** → hand off to `(end of pipeline — deliverable is seqsubmit-report.md)`.
- **If verdict is `NO-GO`** → stop. List the failing checks and ask the user to fix them.

The recommended message:

> ENA Submission QC + Accession Summary complete. Overall verdict: `<verdict>`. Next: invoke `(end of pipeline — deliverable is seqsubmit-report.md)` with the artifact defaults.
