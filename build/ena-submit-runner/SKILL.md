---
name: ena-submit-runner
description: Phase 2 of ena-submit. Native execution engine — no Nextflow. Reads `params.json` (mode, centre_name, submission_study, samplesheet) and for `mags`/`bins` mode runs the genome_evaluation QC tools directly (barrnap, tRNAscan-SE, CheckM2, CAT, CoverM) to fill in any missing samplesheet metadata (RNA_presence, completeness/contamination, NCBI_lineage, genome_coverage), then builds the per-sample ena-webin-cli manifest(s) and invokes `ena-webin-cli` directly against the ENA test server (default) or production server. Writes `run-summary.md` + `run.log` + the raw ena-webin-cli receipt/report files under `$RUN_DIR/webin-cli/`.
version: 1.0.0
updated: "2026-09-12"
triggers:
  - "run ena-submit"
  - "submit to ENA"
  - "execute ENA submission"
  - "invoke ena-webin-cli"
  - "start ENA submission"
---

# Run: native ena-webin-cli submission

> **v1.0.0.** Run the genome_evaluation QC tools (mags/bins only) and invoke `ena-webin-cli` directly with the preflight-validated inputs. Stage order and manifest formats follow the nf-core/seqsubmit spec (`docs-corpus/nf-core-seqsubmit/`) as a reference only — nf-core/seqsubmit itself is never invoked.

## Audience

This sub-skill serves two purposes:

- **AI Agents**: Triggered by the phrases above. Must run all evidence collection steps, then write the artifact.
- **Human Users**: Provides a transparent audit trail.

## When to Use This Skill

Use this skill if:

- Submit a batch of samples to ENA by invoking `ena-webin-cli` directly, with the QC tools it depends on (mags/bins mode) run natively beforehand.
- Run against the ENA test server (`test_upload=true`, the default) to dry-run the submission before a real push.

Do NOT use this skill if:

- You want a Nextflow/nf-core execution engine — this skill deliberately does not shell out to Nextflow. It is the executor itself.

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
| `$RUN_DIR/run.log` | this skill | text | raw stdout/stderr of every tool invocation, in order |
| `$RUN_DIR/webin-cli/` | this skill | ena-webin-cli output dir (`--outputDir`) | per-sample receipt/report XML + submission log, as produced by `ena-webin-cli` itself |
| `$RUN_DIR/qc/` | this skill | per-tool output dirs (mags/bins only) | `qc/<sample>/{coverage,rna/barrnap,rna/trnascanse,taxonomy,checkm2}/` |
| `$RUN_DIR/multiqc/` | this skill | MultiQC report (mags/bins only) | `multiqc_report.html` + `multiqc_data/` |

### Verdict gate

The next phase **refuses to run** unless `$RUN_DIR/run-summary.md` overall verdict is `GO` or `GO-WITH-WARNINGS`. A `NO-GO` verdict stops the pipeline.

## 0.5 Ask-User Stop Points

This sub-skill has **4 stop points** (SP1–SP4). Each fires only when the evidence is ambiguous. The format is **Evidence + Recommend + Options**. If the evidence is unambiguous, the agent auto-picks the default and proceeds silently.

### SP1 — Real (production) submission requested

| Trigger | Evidence check | Action |
| --- | --- | --- |
| `params.json: test_upload` is `false` (or the user explicitly asks for a production submission) | `test_upload` field in `params.json`, AND `preflight.md` verdict | Ask: "This will submit to the LIVE ENA server — irreversible (you can only suppress + re-upload afterward). Pick: (A) confirm and proceed to production, (B) switch back to the TEST server (`test_upload=true`) first, (C) abort" |

**Auto-pick when**: `test_upload` is `true` (or absent — the default). Default: proceed to the TEST server without asking. **Never** auto-pick a production submission — this stop point cannot be skipped even if the evidence looks unambiguous.

### Operating rule

> **Auto-pick when the evidence is unambiguous; ask when the agent genuinely cannot decide.** When asking, present the evidence first, then the recommendation, then 2–4 concrete options. Do not ask "what do you want?" — ask "I see X, recommend Y, which one of A/B/C?"

## Description

This skill is the **execution (run)** phase of the ena-submit pipeline. It computes evidence and emits a machine-readable artifact plus a human-readable audit.

## Prerequisites

- **Environment**: pixi env with `ena-webin-cli` on PATH always, plus `barrnap`/`tRNAscan-SE`/`checkm2`/`CAT`/`coverm`/`multiqc` when `mode` is `mags`/`bins`.
- **Upstream Evidence**: `preflight.md` (verdict GO/GO-WITH-WARNINGS) + `params.json` (mode, centre_name, submission_study or study_metadata, samplesheet path, test_upload, upload_tpa).

## Procedure

The procedure has **three phases**: (1) gather inputs, (2) compute evidence (run the QC tools + build manifests + invoke ena-webin-cli), (3) write outputs. Step 2 differs per `mode`; the stage order below follows the nf-core/seqsubmit output.md spec (`docs-corpus/nf-core-seqsubmit/output.md`), used only as a reference for ordering and manifest shape.

### 1. Gather inputs from the user

Everything below should already be resolved from `params.json`; only ask if a required field is missing.

| Input | Required? | Default if absent |
| --- | --- | --- |
| `mode` (reads\|metagenomic_assemblies\|mags\|bins) | yes | from `params.json` |
| `centre_name` | yes | from `params.json` |
| `submission_study` accession OR `study_metadata` file | yes (one of) | from `params.json` |
| `test_upload` (true\|false) | no | `true` (SP1 gates a `false` value) |
| `upload_tpa` (true\|false) | no | `false` |
| CheckM2 / CAT database paths (mags/bins only) | no | download on first use per docs-corpus notes (may be slow) |

### 2. Compute evidence (always run; never skip)

Each numbered step produces a line in `run.log` and a row in the report. All commands run inside the pixi env; every invocation's stdout/stderr is appended to `$RUN_DIR/run.log`.

#### 2a. `mags` / `bins` mode — genome_evaluation QC, per sample, before manifest build

Only run a given tool for a sample if the corresponding samplesheet column is empty (the samplesheet may already carry pre-computed values — never recompute what's already provided). Order follows `docs-corpus/nf-core-seqsubmit/output.md`: coverage → RNA prediction → taxonomy → completeness/contamination.

```bash
SAMPLE_DIR="$RUN_DIR/qc/$SAMPLE_ID"
mkdir -p "$SAMPLE_DIR"

# 1) genome_coverage — CoverM, only if the samplesheet's genome_coverage cell is empty
#    (needs fastq_1[/fastq_2] for the source reads)
coverm genome --coupled "$FASTQ_1" "$FASTQ_2" \
    --genome-fasta-files "$FASTA" \
    --threads "$THREADS" \
    --output-file "$SAMPLE_DIR/coverage/genome_coverage.tsv" \
    2>&1 | tee -a "$RUN_DIR/run.log"

# 2) RNA_presence — barrnap (rRNA) + tRNAscan-SE (tRNA), only if RNA_presence is empty
barrnap --quiet --lencutoff 0.8 --reject 0.5 "$FASTA" > "$SAMPLE_DIR/rna/barrnap/${SAMPLE_ID}.gff" \
    2>> "$RUN_DIR/run.log"
tRNAscan-SE -B -Q "$FASTA" \
    -o "$SAMPLE_DIR/rna/trnascanse/${SAMPLE_ID}.out" \
    -m "$SAMPLE_DIR/rna/trnascanse/${SAMPLE_ID}.stats" \
    2>&1 | tee -a "$RUN_DIR/run.log"
# RNA_presence = true iff >=1 of {23S,16S,5S} rRNA AND >=18 tRNAs are found (MISAG/MIMAG rule)

# 3) NCBI_lineage — CAT, only if NCBI_lineage is empty (needs a prepared CAT database, $CAT_DB)
CAT contigs -c "$FASTA" -d "$CAT_DB/db" -t "$CAT_DB/tax" -o "$SAMPLE_DIR/taxonomy/${SAMPLE_ID}" \
    2>&1 | tee -a "$RUN_DIR/run.log"
CAT add_names -i "$SAMPLE_DIR/taxonomy/${SAMPLE_ID}.ORF2LCA.txt" \
    -o "$SAMPLE_DIR/taxonomy/${SAMPLE_ID}.named.tsv" -t "$CAT_DB/tax" --only_official \
    2>&1 | tee -a "$RUN_DIR/run.log"

# 4) completeness / contamination / stats_generation_software — CheckM2, only if both cells are empty
#    (needs a prepared CheckM2 database, $CHECKM2_DB)
checkm2 predict --threads "$THREADS" --input "$FASTA" \
    --output-directory "$SAMPLE_DIR/checkm2" --database_path "$CHECKM2_DB" \
    2>&1 | tee -a "$RUN_DIR/run.log"
# completeness/contamination come from checkm2/quality_report.tsv columns Completeness/Contamination
```

After per-sample QC, merge the computed columns back into the working samplesheet (`$RUN_DIR/genome_metadata.tsv`) — this is the source the manifest-building step reads.

#### 2b. Build the ena-webin-cli manifest(s)

One manifest per sample/entry, following the `--context` for the mode (per `docs-corpus/ena-webin-cli/README.md`):

| `mode` | `--context` | Manifest fields (from the samplesheet / genome_metadata.tsv row) |
| --- | --- | --- |
| `reads` | `reads` | `NAME`, `STUDY` (submission_study), `SAMPLE` (sample_accession), `PLATFORM`, `INSTRUMENT`, `LIBRARY_SOURCE`, `LIBRARY_SELECTION`, `LIBRARY_STRATEGY`, `INSERT_SIZE`, `FASTQ` (fastq_1[, fastq_2]) |
| `metagenomic_assemblies` | `genome` (assembly) | `ASSEMBLYNAME`, `STUDY`, `RUN_REF` (run_accession), `ASSEMBLY_TYPE=metagenome`, `COVERAGE`, `PROGRAM` (assembler+assembler_version), `FASTA` |
| `mags` | `genome` (MAG) | `ASSEMBLYNAME`, `STUDY`, `RUN_REF`/`ASSEMBLY_REF` (accession), `ASSEMBLY_TYPE=metagenome-assembled genome`, `COVERAGE`, `PROGRAM`, `MOLECULETYPE=genomic DNA`, `TAX_ID`/`ORGANISM` (from NCBI_lineage), `FASTA`, MIMAG fields (completeness, contamination, binning_software, metagenome, environment triad) |
| `bins` | `genome` (bin) | same as `mags` but `ASSEMBLY_TYPE=binned metagenome`, MISAG fields |

```bash
mkdir -p "$RUN_DIR/webin-cli/manifests"
cat > "$RUN_DIR/webin-cli/manifests/${SAMPLE_ID}.manifest.tsv" <<EOF
STUDY	$SUBMISSION_STUDY
SAMPLE	$SAMPLE_ACCESSION
...   # remaining fields per the table above, one KEY<TAB>VALUE per line
EOF
```

If TPA (`upload_tpa=true`), add `TPA_SPECIFIC_SUBMISSION_TYPE` per docs-corpus TPA notes.

#### 2c. Invoke `ena-webin-cli`

`--test_upload` (from `params.json`) selects `--test` vs the production endpoint. **SP1 gates any production invocation** — never construct the production command without the user having confirmed SP1.

```bash
WEBIN_CONTEXT="reads"   # or: genome  (metagenomic_assemblies / mags / bins all use `genome`)
WEBIN_FLAGS=(--context "$WEBIN_CONTEXT" \
             --userName "$ENA_WEBIN" --password "$ENA_WEBIN_PASSWORD" \
             --centerName "$CENTRE_NAME" \
             --manifest "$RUN_DIR/webin-cli/manifests/${SAMPLE_ID}.manifest.tsv" \
             --inputDir "$INPUT_DIR" --outputDir "$RUN_DIR/webin-cli")
[ "$TEST_UPLOAD" = "true" ] && WEBIN_FLAGS+=(--test)

ena-webin-cli "${WEBIN_FLAGS[@]}" -submit 2>&1 | tee -a "$RUN_DIR/run.log"
# Parse the accession from ena-webin-cli's stdout / the receipt XML under $RUN_DIR/webin-cli/
```

#### 2d. `multiqc` (mags/bins only)

```bash
multiqc --force -o "$RUN_DIR/multiqc" "$RUN_DIR/qc"
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
# ENA submission run report

Run:        $RUN_DIR
Generated:  <ISO8601>
Pipeline:   ena-submit v1.0.0

## Overall verdict

**GO** ✅ *(or GO-WITH-WARNINGS ⚠️ / NO-GO ❌)*

<one-line summary>

## Evidence

| Check | Verdict | Value | Threshold |
|---|---|---|---|
| `ena-webin-cli` on PATH | ✅ | ena-webin-cli 8.x | required |
| genome_evaluation QC complete (mags/bins only) | ✅ | 5/5 samples: coverage, RNA, taxonomy, checkm2 done | all samples with missing metadata columns filled |
| Webin env vars set | ✅ | ENA_WEBIN + ENA_WEBIN_PASSWORD | non-empty |
| Manifest(s) built | ✅ | N/N samples | one manifest per sample, valid TSV |
| Run submission | ✅ | submitted to ENA test server | test_upload=true → OK; =false → real submission (SP1-gated) |
| Accessions received | ✅ | N/N samples | ena-webin-cli receipt contains an accession per sample |

## Recommendations

- After run completes, hand off to `qc/ena-submit-qc` to build the accession summary.
- If run failed, route to `debug/ena-submit-debug` with the failing stderr.

## Handoff

If verdict is `GO` or `GO-WITH-WARNINGS`, hand off to: `qc/ena-submit-qc`.

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
| `ERROR: Login failed` / `authentication failed` from `ena-webin-cli` | Wrong `ENA_WEBIN` / `ENA_WEBIN_PASSWORD` or account not registered for the target context | Verify credentials at https://www.ebi.ac.uk/ena/submit/webin/login, re-export the env vars, re-run preflight. |
| `manifest field ... is mandatory` from `ena-webin-cli` | Manifest is missing a required field for the `--context` | Re-check the manifest table in §2b against the samplesheet row; rebuild the manifest. |
| `checkm2: database not found` / `No such file: .dmnd` | `--database_path` not set or CheckM2 DB not downloaded | `checkm2 database --download` once, then pass `--database_path` on every subsequent run. |
| `CAT: could not find database/taxonomy files` | `$CAT_DB` path wrong or DB not prepared | `CAT prepare --fresh --download_dir <dir>` once (large download), or point at an existing prepared DB. |
| `coverm: no reads mapped` / near-zero coverage | Wrong `fastq_1`/`fastq_2` pairing, or FASTA/reads mismatch | Re-verify the samplesheet's fastq columns reference the reads that generated this assembly/MAG. |
| `verdict: BEHIND-BY-N` from `pixi run update-check` | Upstream `github.com/cheahhl814/ena-submit` is ahead of the deployed copy | Re-deploy per AGENTS.md §4a: `rsync -a --exclude='.git' @skills/ena-submit/ ~/.pi/agent/skills/ena-submit/` then `diff -rq` to verify. The script prints the canonical fix on `BEHIND-BY-N`. |
| `verdict: OFFLINE` / `NO-ORIGIN` from `pixi run update-check` | No network or no `origin` remote — informational, exit code 2 | Re-run when online, or `git remote add origin https://github.com/cheahhl814/ena-submit.git` if the remote is missing. |

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

- **If verdict is `GO` or `GO-WITH-WARNINGS`** → hand off to `qc/ena-submit-qc`.
- **If verdict is `NO-GO`** → stop. List the failing checks and ask the user to fix them.

The recommended message:

> ENA submission run complete. Overall verdict: `<verdict>`. Next: invoke `qc/ena-submit-qc` with the artifact defaults.
