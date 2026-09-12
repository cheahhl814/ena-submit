# Skill creator preflight report

Run:        /home/cheahhl814/claude_workspace/bioinformatics/AIx-BIO/skills/seqsubmit-agent
Generated:  2026-09-12T16:03:00Z
Meta-skill: bioinfo-skill-creator v1.2.0
Upstream:   https://github.com/nf-core/seqsubmit (v1.0.0)

## Overall verdict

**GO** ✅

Skill `seqsubmit-agent` queued for build. 7 public tools found (ena-webin-cli, barrnap, cat, checkm2, coverm, trnascan-se, multiqc) + Nextflow as the external executor. Bash-only per user request — no local DSL2 runner; the skill wraps the upstream nf-core/seqsubmit pipeline.

## Evidence

| Check | Verdict | Value | Threshold |
|---|---|---|---|
| Skill name (kebab-case) | ✅ | `seqsubmit-agent` | valid regex |
| Skill name uniqueness | ✅ | no collision in `@skills/` | unique |
| Target directory writable | ✅ | `$RUN_DIR` | writable |
| Tool inventory | ✅ | 7 tools (after dropping 2 aliases) | ≥ 1 |
| Pixi env | ✅ | pixi 0.70.1 on PATH | installed |
| Tool availability (`pixi search`) | ✅ | 7/7 found in conda-forge/bioconda | all tools resolve |
| Nextflow (external executor) | ✅ | required by upstream pipeline (≥25.04.0) | not packaged in pixi.toml — invoked directly |
| Git status | ⚠️ | NOT initialized | will init in build phase |
| Disk space | ✅ | 128 GB free at $RUN_DIR | ≥ 5 GB |
| GitHub repo | ✅ | cheahhl814/seqsubmit-agent does not exist yet | will be created on first push |

## SP8 (tool not found) — auto-resolved

Two tool names from the initial inventory came back `not_found` via `pixi search -c conda-forge -c bioconda`. Auto-resolved without asking (the failure mode is unambiguous for both):

| Tool | Status | Resolution |
|---|---|---|
| `webin-cli` | not_found | Dropped — legacy alias of `ena-webin-cli` (the current package). The upstream nf-core/seqsubmit invokes `webin-cli` internally; from the agent's pixi env the package is `ena-webin-cli`. |
| `catpack` | not_found | Renamed to `cat` — bioconda package is `cat` (Contig Annotation Tool). The upstream pipeline's `fasta_classify_catpack` subworkflow depends on the same `cat` package. |

Both resolutions are recorded in `params.json` under `dropped_tools` so the build phase can surface them in the skill's README provenance section.

## SP7 (nextflow-runner) — auto-picked: NO

Per the user's explicit request: *"create a meta-skill (without nextflow runner)"*. The skill wraps the upstream nf-core/seqsubmit pipeline as an external executor, not a local DSL2 runner. The Bash recipes handle pre-flight (samplesheet validation, Webin secret check) and post-processing (accession receipt parsing); the actual pipeline execution is a single `nextflow run nf-core/seqsubmit -profile <...>` call.

## Recommendations

- **Skill name**: `seqsubmit-agent` (user-provided; valid)
- **Skill shape**: `meta-skill-multi-subskill` (5 sub-skills; wraps a multi-mode external pipeline)
- **Sub-skills**: preflight, run, qc, debug, battle-test (5-sub-skill template)
- **Nextflow runner**: **no** (SP7 user override)
- **Target tiers**: `large` only (SP9) — Claude/GPT-5 class only
- **pixi task names**: `preflight`, `run`, `qc`, `report`, `update-check`
- **External executor**: invoke `nextflow run nf-core/seqsubmit` from the `run` sub-skill, not as a DSL2 wrapper

## Tools

| Tool | Role | `pixi search` status | Notes |
|---|---|---|---|
| ena-webin-cli | ENA submission CLI (all 4 modes) | ✅ found | umbrella for the 4 submission workflows |
| barrnap | rRNA detection | ✅ found | used in `genome_evaluation` subworkflow |
| cat | Contig Annotation Tool (taxonomy) | ✅ found | bioconda name; pipeline calls subworkflow `fasta_classify_catpack` |
| checkm2 | MAG QC (completeness/contamination) | ✅ found | `--checkm2_db` param triggers download |
| coverm | coverage (read/contig/genome) | ✅ found | used in `mags`/`bins` modes |
| trnascan-se | tRNA detection | ✅ found | used in `genome_evaluation` subworkflow |
| multiqc | aggregate QC report | ✅ found | emitted by all 4 modes |
| nextflow | pipeline executor | external | not in pixi.toml; required ≥25.04.0 by upstream |

## Handoff

Verdict is `GO`. Hand off to `build/skill-builder` with `params.json` defaults:

- `skill_name` = `seqsubmit-agent`
- `tool_inventory` = 7 tools (see table above) + `nextflow` as external
- `with_nextflow_runner` = `false`
- `sub_skills` = `["preflight", "run", "qc", "debug", "battle-test"]`
- `upstream_pipeline` = `nf-core/seqsubmit@1.0.0` (the skill wraps, not reimplements)

The build sub-skill will:
1. Generate `docs-corpus/` for the 7 tools + a `nf-core-seqsubmit/` snapshot.
2. Render `SKILL.md` from `ORCHESTRATOR_SKILL.md.j2`.
3. Render `README.md` from `README.md.j2` (no unfilled template slots).
4. Render `pixi.toml` from `pixi.toml.j2` (with the 7 conda-resolvable tools; `nextflow` added as a system-prerequisite line, not a pixi dep).
5. Render 5 sub-skill `SKILL.md` files from `SUB_SKILL_SKILL.md.j2`.
6. Render `bin/skill-update-check.py` from `templates/bin/skill-update-check.py.j2`.
7. Skip `runners/nextflow-runner/` (user opted out at SP7).

## Reproducibility

- params.json: `$RUN_DIR/params.json`
- evidence:   `$RUN_DIR/preflight_evidence.txt`
- this report: `$RUN_DIR/preflight.md` (regenerable via `preflight/skill-creator-preflight`)
