---
name: seqsubmit-agent-runner
description: Phase 2 of seqsubmit-agent. Constructs the `nextflow run nf-core/seqsubmit` command from `params.json` (mode, profile, input, centre_name, submission_study, outdir), starts the run, and watches the work directory. Writes `run-summary.md` + the Nextflow trace/timeline/report into `$RUN_DIR/trace/`, `$RUN_DIR/timeline/`, `$RUN_DIR/report/`. Does NOT author a local DSL2 runner — the upstream pipeline is the executor.
version: 1.0.0
updated: "2026-09-12"
triggers:
  - "run seqsubmit"
  - "submit to ENA"
  - "run nf-core/seqsubmit"
  - "execute seqsubmit pipeline"
  - "start ENA submission"
---

# Run nf-core/seqsubmit

> **v1.0.0.** Invoke the upstream nf-core/seqsubmit pipeline with the preflight-validated inputs.

## Audience

This sub-skill serves two purposes:

- **AI Agents**: Triggered by the phrases above. Must run all evidence collection steps, then write the artifact.
- **Human Users**: Provides a transparent audit trail.

## When to Use This Skill

Use this skill if:

- Submit a batch of samples to ENA via the upstream nf-core/seqsubmit pipeline at version 1.0.0.
- Run on the ENA test server (`--test_upload true`) to dry-run the submission before a real push.

Do NOT use this skill if:

- You want to author your own Nextflow pipeline — this skill wraps the existing upstream, not a new one.

## 0. Inputs / Outputs contract

### Inputs (consumed)

| Path | Source | Required? |
| --- | --- | --- |
| `$RUN_DIR/preflight.md` | preflight | yes (verdict ≥ GO-WITH-WARNINGS) |
| `$RUN_DIR/params.json` | preflight | yes |

### Outputs (produced)

| Path | Owner | Format | Notes |
| --- | --- | --- | --- |
| `$RUN_DIR/run-summary.md` | this skill | Markdown | run log + accession table (if any) |
| `$RUN_DIR/trace/` | this skill | Nextflow trace TSV | nf-core standard |
| `$RUN_DIR/timeline/` | this skill | Nextflow timeline HTML | nf-core standard |
| `$RUN_DIR/report/` | this skill | Nextflow report HTML | nf-core standard |

### Verdict gate

The next phase **refuses to run** unless `$RUN_DIR/run-summary.md` overall verdict is `GO` or `GO-WITH-WARNINGS`. A `NO-GO` verdict stops the pipeline.

## 0.5 Ask-User Stop Points

This sub-skill has **4 stop points** (SP1–SP4). Each fires only when the evidence is ambiguous. The format is **Evidence + Recommend + Options**. If the evidence is unambiguous, the agent auto-picks the default and proceeds silently.

### SP1 — Container profile not available

| Trigger | Evidence check | Action |
| --- | --- | --- |
| `docker --version` (or `singularity --version`, `podman --version`, `conda --version`) returns nothing for the chosen profile | missing container runtime vs `--profile <X>` choice | Ask: "Container runtime for profile `<X>` is not on PATH. Pick: (A) install the runtime now, (B) switch to `--profile conda` (slower but no daemon), (C) abort" |

**Auto-pick when**: the chosen runtime is on PATH. Default: proceed..

### Operating rule

> **Auto-pick when the evidence is unambiguous; ask when the agent genuinely cannot decide.** When asking, present the evidence first, then the recommendation, then 2–4 concrete options. Do not ask "what do you want?" — ask "I see X, recommend Y, which one of A/B/C?"

## Description

This skill is the **execution (run)** phase of the seqsubmit-agent pipeline. It computes evidence and emits a machine-readable artifact plus a human-readable audit.

## Prerequisites

- **Environment**: pixi env with the required tools.
- **Upstream Evidence**: preflight.md (GO/GO-WITH-WARNINGS) + params.json (mode, profile, outdir)..

## Procedure

The procedure has **three phases**: (1) gather inputs, (2) compute evidence, (3) write outputs.

### 1. Gather inputs from the user

Ask once, in one question batch if possible:

| Input | Required? | Default if absent |
| --- | --- | --- |
| Container profile (docker|singularity|podman|conda|test) | yes | docker |
| `--outdir` | yes | ask |
| `--upload_tpa true|false` | no | false |
| `--test_upload true|false` | no | true (recommended) |

### 2. Compute evidence (always run; never skip)

Each numbered step produces a line in the evidence file and a column in the report.

```bash
# Verify container runtime
command -v docker || command -v singularity || command -v podman || command -v conda
```

### 3. Write outputs

#### 3a) `run-summary.md` schema

```json
{
  "status": "submitted",
  "accessions": "[{sample, accession, receipt}]"
}
```

#### 3b) `run-summary.md` template

```markdown
# Run nf-core/seqsubmit report

Run:        $RUN_DIR
Generated:  <ISO8601>
Pipeline:   seqsubmit-agent v1.0.0

## Overall verdict

**GO** ✅ *(or GO-WITH-WARNINGS ⚠️ / NO-GO ❌)*

<one-line summary>

## Evidence

| Check | Verdict | Value | Threshold |
|---|---|---|---|
| Container runtime | ✅ | docker 27.x | one of docker/singularity/podman/conda |
| Nextflow version | ✅ | 25.10.4 | ≥ 25.04.0 (nf-core/seqsubmit 1.0.0) |
| Pipeline pulled | ✅ | nf-core/seqsubmit 1.0.0 | exact tag |
| Webin secrets set | ✅ | ENA_WEBIN + ENA_WEBIN_PASSWORD | non-empty |
| Run submission | ✅ | submitted to ENA test server | test_upload=true → OK; =false → real submission |

## Recommendations

- After run completes, hand off to `qc/seqsubmit-agent-qc` to build the accession summary.
- If run failed, route to `debug/seqsubmit-agent-debug` with the failing stderr.

## Handoff

If verdict is `GO` or `GO-WITH-WARNINGS`, hand off to: `qc/seqsubmit-agent-qc`.

## Reproducibility

- run-summary.md: $RUN_DIR/run-summary.md
- evidence: $RUN_DIR/run.log
- this report: $RUN_DIR/run-summary.md (regenerable via this skill)
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

- [ ] `$RUN_DIR/run-summary.md` exists and is valid JSON.
- [ ] `$RUN_DIR/run-summary.md` exists with overall verdict.
- [ ] `$RUN_DIR/run.log` exists with raw evidence.
- [ ] Overall verdict is `GO` or `GO-WITH-WARNINGS` (not `NO-GO`) before proceeding to next phase.

## Output contract

This skill produces:

- `$RUN_DIR/run-summary.md` (machine contract)
- `$RUN_DIR/run-summary.md` (human audit)
- `$RUN_DIR/run.log` (raw evidence)

It does **not** produce any other artifact. The next sub-skill does that.

## What NOT to do

- Do **not** skip the evidence collection. Every recommendation must be cited back to a measured value.
- Do **not** hand-write the artifact without running the evidence collection first.
- Do **not** override a `NO-GO` verdict.
- Do **not** proceed to the next phase if the artifact is missing.
- Do **not** re-run this sub-skill without deleting the artifact first — the existence of the artifact is the stage-detection signal.

## Handoff

After this sub-skill writes `$RUN_DIR/run-summary.md` and `$RUN_DIR/run-summary.md`:

- **If verdict is `GO` or `GO-WITH-WARNINGS`** → hand off to `qc/seqsubmit-agent-qc`.
- **If verdict is `NO-GO`** → stop. List the failing checks and ask the user to fix them.

The recommended message:

> Run nf-core/seqsubmit complete. Overall verdict: `<verdict>`. Next: invoke `qc/seqsubmit-agent-qc` with the artifact defaults.
