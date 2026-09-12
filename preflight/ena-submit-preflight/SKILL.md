---
name: ena-submit-preflight
description: Phase 1 of ena-submit. Validates the submission samplesheet (column set per `--mode`), confirms `ENA_WEBIN` and `ENA_WEBIN_PASSWORD` environment variables are set, confirms the native tools this run's mode needs are on PATH (ena-webin-cli always; barrnap/tRNAscan-SE/CheckM2/CAT/CoverM for mags/bins), resolves the study accession or study-registration file, and writes `preflight.md` + `params.json` with verdict GO / GO-WITH-WARNINGS / NO-GO. Mode-to-schema mapping follows the nf-core/seqsubmit docs (vendored in docs-corpus/), used here only as a specification.
version: 1.0.0
updated: "2026-09-12"
triggers:
  - "preflight ENA submission"
  - "validate Webin credentials"
  - "check seqsubmit samplesheet"
  - "resolve study accession"
---

# ENA Submission Preflight

> **v1.0.0.** Validate samplesheet, Webin credentials, native tool availability, and study metadata before invoking `ena-webin-cli` directly.

## Audience

This sub-skill serves two purposes:

- **AI Agents**: Triggered by the phrases above. Must run all evidence collection steps, then write the artifact.
- **Human Users**: Provides a transparent audit trail.

## When to Use This Skill

Use this skill if:

- Validate the samplesheet column set against the chosen `--mode` (reads/metagenomic_assemblies/mags/bins) before invoking the upstream pipeline.
- Confirm ENA Webin credentials and study accession are resolvable so the upstream `webin-cli` calls do not fail mid-submission.

Do NOT use this skill if:

- You have not yet chosen a submission mode — pick one of `reads | metagenomic_assemblies | mags | bins` first.

## 0. Inputs / Outputs contract

### Inputs (consumed)

| Path | Source | Required? |
| --- | --- | --- |
| `$RUN_DIR/samplesheet.csv` | user | yes |
| `$RUN_DIR/study_accession_or_metadata.{txt,tsv}` | user | yes (one of) |

### Outputs (produced)

| Path | Owner | Format | Notes |
| --- | --- | --- | --- |
| `$RUN_DIR/preflight.md` | this skill | Markdown | human audit trail |
| `$RUN_DIR/params.json` | this skill | JSON | machine contract for the run sub-skill |
| `$RUN_DIR/preflight_evidence.txt` | this skill | text | raw evidence |

### Verdict gate

The next phase **refuses to run** unless `$RUN_DIR/preflight.md` overall verdict is `GO` or `GO-WITH-WARNINGS`. A `NO-GO` verdict stops the pipeline.

## 0.5 Ask-User Stop Points

This sub-skill has **5 stop points** (SP1–SP5). Each fires only when the evidence is ambiguous. The format is **Evidence + Recommend + Options**. If the evidence is unambiguous, the agent auto-picks the default and proceeds silently.

### SP1 — Mode / samplesheet mismatch

| Trigger | Evidence check | Action |
| --- | --- | --- |
| the samplesheet columns do not match the expected columns for `--mode` (reads/metagenomic_assemblies/mags/bins) | csv header diff vs the mode-specific required columns in `params.json: submission_modes` | Ask: "The samplesheet columns don't match the expected schema for `--mode <X>`. Pick: (A) I'll re-emit the samplesheet now, (B) auto-derive the mode from the header (best-match), (C) abort" |

**Auto-pick when**: the header exactly matches the expected schema for the chosen `--mode`. Default: proceed..

### SP2 — Required native tool missing from PATH

| Trigger | Evidence check | Action |
| --- | --- | --- |
| `ena-webin-cli` is missing (any mode), or `--mode` is mags/bins and one of barrnap/tRNAscan-SE/checkm2/CAT/coverm/multiqc is missing | `command -v <tool>` loop against the mode-specific tool list | Ask: "`<tool>` is not on PATH. Pick: (A) `pixi install` to resolve it from this skill's pinned `pixi.toml`, (B) install it manually and re-run preflight, (C) abort" |

**Auto-pick when**: every tool required for the chosen `--mode` resolves via `command -v`. Default: proceed.

### Operating rule

> **Auto-pick when the evidence is unambiguous; ask when the agent genuinely cannot decide.** When asking, present the evidence first, then the recommendation, then 2–4 concrete options. Do not ask "what do you want?" — ask "I see X, recommend Y, which one of A/B/C?"

## Description

This skill is the **input validation (preflight)** phase of the ena-submit pipeline. It computes evidence and emits a machine-readable artifact plus a human-readable audit.

## Prerequisites

- **Environment**: pixi env with the required tools.
- **Upstream Evidence**: user-provided samplesheet + study accession + Webin credentials in the `ENA_WEBIN` / `ENA_WEBIN_PASSWORD` environment variables.

## Procedure

The procedure has **three phases**: (1) gather inputs, (2) compute evidence, (3) write outputs.

### 1. Gather inputs from the user

Ask once, in one question batch if possible:

| Input | Required? | Default if absent |
| --- | --- | --- |
| `--mode` (reads | metagenomic_assemblies | mags | bins) | yes | ask |
| `--input` samplesheet.csv | yes | ask |
| `--centre_name` | yes | ask |
| `--submission_study` accession OR `--study_metadata` file | yes (one of) | ask |
| ENA Webin credentials | yes | ask user to `export ENA_WEBIN=Webin-XXX; export ENA_WEBIN_PASSWORD=...` |

### 2. Compute evidence (always run; never skip)

Each numbered step produces a line in the evidence file and a column in the report.

```bash
# Mode detection — read `--mode` (or derive from samplesheet header)
MODE=$1; awk -F, 'NR==1{for(i=1;i<=NF;i++) h[i]=$i; print h[1]}' "$SAMPLESHEET"

# ena-webin-cli is required for every mode
command -v ena-webin-cli && ena-webin-cli --version

# Webin credentials — plain env vars, no Nextflow secrets store involved
[ -n "$ENA_WEBIN" ] && echo "ENA_WEBIN set (len ${#ENA_WEBIN})"
[ -n "$ENA_WEBIN_PASSWORD" ] && echo "ENA_WEBIN_PASSWORD set (redacted)"

# Mode-specific tool audit — only mags/bins need the genome_evaluation QC tools
if [ "$MODE" = "mags" ] || [ "$MODE" = "bins" ]; then
  for tool in barrnap tRNAscan-SE checkm2 CAT coverm; do
    command -v "$tool" || echo "MISSING: $tool"
  done
  command -v multiqc || echo "MISSING: multiqc"
fi
```

### 3. Write outputs

#### 3a) `params.json` schema

```json
{
  "mode": "mags",
  "verdict": "GO"
}
```

#### 3b) `preflight.md` template

```markdown
# ENA Submission Preflight report

Run:        $RUN_DIR
Generated:  <ISO8601>
Pipeline:   ena-submit v1.0.0

## Overall verdict

**GO** ✅ *(or GO-WITH-WARNINGS ⚠️ / NO-GO ❌)*

<one-line summary>

## Evidence

| Check | Verdict | Value | Threshold |
|---|---|---|---|
| Mode resolved | ✅ | mags | one of reads|metagenomic_assemblies|mags|bins |
| Samplesheet columns | ✅ | all required present | matches mode schema |
| `ena-webin-cli` on PATH | ✅ | ena-webin-cli 8.x | required for every mode |
| Webin env var ENA_WEBIN | ✅ | set (len 14) | starts with Webin- |
| Webin env var ENA_WEBIN_PASSWORD | ✅ | set (redacted) | non-empty |
| genome_evaluation tools on PATH (mags/bins only) | ✅ | barrnap, tRNAscan-SE, checkm2, CAT, coverm all found | required only when mode is mags/bins |
| `multiqc` on PATH (mags/bins only) | ✅ | multiqc 1.x | required only when mode is mags/bins |
| Study accession OR metadata file | ✅ | PRJEB12345 | accession OR existing file |
| Output directory writable | ✅ | /path/to/outdir | writable |

## Recommendations

- Proceed to `build/ena-submit-runner` with the validated samplesheet and resolved mode.
- If GO-WITH-WARNINGS: surface the warning column to the user before proceeding.

## Handoff

If verdict is `GO` or `GO-WITH-WARNINGS`, hand off to: `build/ena-submit-runner`.

## Reproducibility

- params.json: $RUN_DIR/params.json
- evidence: $RUN_DIR/preflight_evidence.txt
- this report: $RUN_DIR/preflight.md (regenerable via this skill)
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
| `verdict: BEHIND-BY-N` from `pixi run update-check` | Upstream `github.com/cheahhl814/ena-submit` is ahead of the deployed copy | Re-deploy per AGENTS.md §4a: `rsync -a --exclude='.git' @skills/ena-submit/ ~/.pi/agent/skills/ena-submit/` then `diff -rq` to verify. The script prints the canonical fix on `BEHIND-BY-N`. |
| `verdict: OFFLINE` / `NO-ORIGIN` from `pixi run update-check` | No network or no `origin` remote — informational, exit code 2 | Re-run when online, or `git remote add origin https://github.com/cheahhl814/ena-submit.git` if the remote is missing. |

## Verification

- [ ] `$RUN_DIR/params.json` exists and is valid JSON.
- [ ] `$RUN_DIR/preflight.md` exists with overall verdict.
- [ ] `$RUN_DIR/preflight_evidence.txt` exists with raw evidence.
- [ ] Overall verdict is `GO` or `GO-WITH-WARNINGS` (not `NO-GO`) before proceeding to next phase.

## Output contract

This skill produces:

- `$RUN_DIR/params.json` (machine contract)
- `$RUN_DIR/preflight.md` (human audit)
- `$RUN_DIR/preflight_evidence.txt` (raw evidence)

It does **not** produce any other artifact. The next sub-skill does that.

## What NOT to do

- Do **not** skip the evidence collection. Every recommendation must be cited back to a measured value.
- Do **not** hand-write the artifact without running the evidence collection first.
- Do **not** override a `NO-GO` verdict.
- Do **not** proceed to the next phase if the artifact is missing.
- Do **not** re-run this sub-skill without deleting the artifact first — the existence of the artifact is the stage-detection signal.

## Handoff

After this sub-skill writes `$RUN_DIR/preflight.md` and `$RUN_DIR/params.json`:

- **If verdict is `GO` or `GO-WITH-WARNINGS`** → hand off to `build/ena-submit-runner`.
- **If verdict is `NO-GO`** → stop. List the failing checks and ask the user to fix them.

The recommended message:

> ENA Submission Preflight complete. Overall verdict: `<verdict>`. Next: invoke `build/ena-submit-runner` with the artifact defaults.
