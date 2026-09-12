---
name: ena-submit
description: Agent wrapper for the nf-core/seqsubmit pipeline (v1.0.0) that submits sequence data to ENA. Orchestrates four submission modes (reads, metagenomic_assemblies, mags, bins) via Bash recipes. Does NOT re-implement the Nextflow pipeline — instead pre-validates inputs (samplesheet, Webin credentials, study accession), prepares the ENA Webin CLI context, and post-processes accession receipts. The Nextflow pipeline itself is invoked as the core executor; the agent owns the pre/post glue.
version: 1.0.0
updated: "2026-09-12"
triggers:
  - "submit to ENA"
  - "ENA submission"
  - "submit raw reads to ENA"
  - "submit MAGs to ENA"
  - "submit bins to ENA"
  - "submit metagenomic assembly to ENA"
  - "Webin CLI"
  - "ENA Webin"
  - "run nf-core/seqsubmit"
  - "seqsubmit agent"
---

# ENA Sequence Submission Agent (seqsubmit wrapper)

> **v1.0.0.** Agent wrapper for the nf-core/seqsubmit pipeline (v1.0.0) — orchestrates 4 ENA submission modes (reads, metagenomic_assemblies, mags, bins) via Bash recipes. Wraps the upstream Nextflow pipeline as an external executor; pre-validates inputs and post-processes accession receipts.

## Audience

This skill serves two purposes:

- **AI Agents**: Triggered by the phrases above. The agent must follow the strict evidence chain and run the Go/No-Go gates.
- **Human Users**: Provides a transparent audit trail.

## When to Use This Skill

Use this skill when you need to:

- Submit raw sequencing reads to the European Nucleotide Archive (ENA) via the `reads` mode of nf-core/seqsubmit.
- Submit metagenomic assemblies to ENA via the `metagenomic_assemblies` mode.
- Submit MAGs or bins to ENA via the `mags` / `bins` mode (with `genome_evaluation` QC: rRNA, tRNA, CheckM2, CAT, coverage).

**Do NOT use this skill** if:

- You do not have a Webin account at https://www.ebi.ac.uk/ena/submit/webin/login (the skill will refuse to proceed without ENA_WEBIN / ENA_WEBIN_PASSWORD set in Nextflow secrets).
- You want to re-implement the Nextflow pipeline — the skill wraps the existing nf-core/seqsubmit as an external executor; it does not author its own DSL2.

## 0. Orchestrator — detect stage, route to the right sub-skill

This meta-skill is a **router**, not a doer. It does not duplicate logic from the sub-skills. Its job is to ask: **"what stage is the user at, and which sub-skill should they invoke next?"**

### 0.1 Locate the run directory

By convention the agent writes handoff files (see §B) to a run directory. Default: the current working directory. Override with `RUN_DIR` env var.

### 0.2 Detect the user's stage

Try to detect automatically **before** asking:

```bash
# Stage detection ladder — first match wins
test -f "$RUN_DIR/seqsubmit-report.md" && STAGE="qc-done"
test -f "$RUN_DIR/qc-summary.md" && STAGE="qc"
test -f "$RUN_DIR/run-summary.md" && STAGE="run"
test -f "$RUN_DIR/preflight.md" && STAGE="preflight"
: "${STAGE:=preflight}"
```

If auto-detection is ambiguous, ask the user one short question (see **SP0** in §0.5).

### 0.5 Master ask-user stop points

This orchestrator has **one** user-facing stop point (SP0). All other stop points live in the sub-skills. The pattern is **Evidence + Recommend + Options**.

#### SP0 — Entry-stage ambiguity

| Trigger | Ask |
|---|---|
| Stage detection returns `preflight` AND no upstream artifact exists | "I don't see the upstream artifact. Did you run the upstream skill?" |

**Auto-pick when**: upstream artifact exists OR user just said "run ena-submit" with no other context → default to `preflight` stage.

#### Routing rule

Auto-pick the default when the evidence is unambiguous. Ask only when the agent genuinely cannot decide.

### 0.3 Route to the right sub-skill

| Stage | Action |
| --- | --- |
| `preflight` | Invoke `preflight/<phase>-preflight`. Validates inputs, writes `preflight.md` + `params.json`. |
| `run` | Invoke `build/<phase>-builder`. Runs the main workflow. |
| `qc` | Invoke `qc/<phase>-qc`. Builds the final report. |
| `qc-done` | Show the user `$RUN_DIR/<report>.md`. |

**Do not skip preflight.** The preflight sub-skill computes evidence and writes `params.json` that the run sub-skill consumes.

## Update Check

This skill ships with a self-update check that compares the deployed `SKILL.md` (and the rest of the skill) against the upstream `github.com/cheahhl814/ena-submit` repo via `git fetch` + SHA diff — no GitHub API call, no extra dependencies.

```bash
pixi run update-check
# Verdict legend (exit code in parens):
#   UP-TO-DATE       (0)  local HEAD matches origin/HEAD
#   LOCAL-AHEAD      (0)  unpushed local commits; no action needed
#   BEHIND-BY-N      (1)  upstream is N commits ahead → rsync from @skills/ena-submit/
#   OFFLINE          (2)  git fetch failed (no network / no credentials); informational
#   NO-ORIGIN        (2)  no `origin` remote configured; informational
```

When `BEHIND-BY-N`, the script prints the canonical fix (rsync from `@skills/ena-submit/` to `~/.pi/agent/skills/ena-submit/` per AGENTS.md §4a, then `diff -rq` to verify). When `OFFLINE`, the script still prints `local_sha` + deployed version so the user can compare by hand. The full implementation is in `bin/skill-update-check.py` (rendered from the meta-skill's `templates/bin/skill-update-check.py.j2`).

### 0.4 The run command

This skill ships **bash recipes** for each phase. The pixi tasks are the entry point for single-machine runs.

```bash
# Run the preflight
pixi run preflight

# Run the main workflow (after preflight passes)
pixi run run

# Run the QC (after the main workflow finishes)
pixi run qc
```

## A. Pipeline Architecture

The analysis is divided into **three sequential phases**: Preflight → Run → QC. The agent MUST complete each phase in order and pass the associated "Go/No-Go" gate.

### Phase 1: Preflight (The Audit)

**Goal**: Validate inputs, compute evidence, and write `params.json` + `preflight.md`.

- **Sub-skill**: `preflight/<phase>-preflight`
- **Must-Verify**: All tools present; inputs valid.
- **Exit Gate**: `$RUN_DIR/preflight.md` exists with overall verdict ≥ `GO-WITH-WARNINGS`.

### Phase 2: Run (The Workflow)

**Goal**: Execute the main workflow.

- **Sub-skill**: `build/<phase>-builder`
- **Must-Verify**: Preflight verdict ≥ `GO-WITH-WARNINGS`.
- **Exit Gate**: The expected artifact exists.

### Phase 3: QC (The Report)

**Goal**: Build the final report.

- **Sub-skill**: `qc/<phase>-qc`
- **Must-Verify**: Run output present.
- **Exit Gate**: `$RUN_DIR/<report>.md` exists with verdict.

## B. The Evidence Chain & Handoff Contract

| From → To | Artifact | Owner | Consumer |
| --- | --- | --- | --- |
| Upstream → Preflight | Input files | upstream | `preflight/<phase>-preflight` |
| Preflight → Run | `preflight.md` + `params.json` | `preflight/<phase>-preflight` | `build/<phase>-builder` |
| Run → QC | Run artifact | `build/<phase>-builder` | `qc/<phase>-qc` |
| QC → User | `<report>.md` | `qc/<phase>-qc` | User |

## C. Output contract — no artifact

This orchestrator skill produces **no file of its own**. All artifacts are produced by the sub-skills.

## D. Go/No-Go Gates

The agent must stop and warn the user if:

- **Preflight `NO-GO`**: `preflight.md` shows `NO-GO` verdict.
- **QC `NO-GO`**: `<report>.md` shows `NO-GO` verdict.

## E. Common follow-ups

| User says | What to do |
| --- | --- |
| "Show me my last report" | `cat $RUN_DIR/<report>.md` |
| "What did the run produce?" | Read `$RUN_DIR/<report>.md` |
| "Can I publish this?" | Point to `$RUN_DIR/preflight.md` + `$RUN_DIR/<report>.md` as audit-trail artifacts. |

## Verification

- [ ] Preflight was performed; `preflight.md` overall verdict ≥ `GO-WITH-WARNINGS`.
- [ ] Run completed; expected artifact exists.
- [ ] QC was performed; `<report>.md` exists with verdict.

## Handoff pointers

After this orchestrator routes the user to a phase, the agent should explicitly state which sub-skill was invoked and what file it produces.

## Provenance

Built with the [bioinfo-skill-creator](https://github.com/cheahhl814/bioinfo-skill-creator) meta-skill. Pattern adopted from [BettaMt-agents](https://github.com/cheahhl814/BettaMt-agents).
