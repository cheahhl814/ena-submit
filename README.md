# ENA Sequence Submission Agent (native ena-webin-cli orchestrator)

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](#-installation)
[![Type](https://img.shields.io/badge/type-agent%20skill-blueviolet)](#-installation)
[![Built with](https://img.shields.io/badge/built%20with-bioinfo--skill--creator-orange)](https://github.com/cheahhl814/bioinfo-skill-creator)

Native tool-orchestration meta-skill that submits sequence data to ENA. Orchestrates four submission modes (reads, metagenomic_assemblies, mags, bins) via Bash recipes. For `mags`/`bins` mode it runs the genome_evaluation QC tools itself (barrnap, tRNAscan-SE, CheckM2, CAT, CoverM) to fill in missing samplesheet metadata, then builds the ena-webin-cli manifest(s) and invokes `ena-webin-cli` directly against the ENA test or production server. No Nextflow, no nf-core dependency — the stage order and manifest formats follow the nf-core/seqsubmit spec (vendored offline in `docs-corpus/`) purely as a reference.

**Repository**: https://github.com/cheahhl814/ena-submit

> [!NOTE]
> Current version: **v1.0.0** (updated 2026-09-12).

## Contents

- [Installation](#-installation)
- [Usage](#-usage)
- [Pipeline overview](#-pipeline-overview)
- [Tools](#-tools)
- [Update check](#-update-check)
- [Repository layout](#-repository-layout)
- [Hard guarantees](#-hard-guarantees)
- [Provenance](#-provenance)

## 🚀 Installation

This is an **agent skill**, not a user-facing library. The recommended install path is to let your AI agent import it.

**Option A — give your agent this prompt (recommended):**

```text
Install the ena-submit skill from
https://github.com/cheahhl814/ena-submit —
clone it into your agent's skills directory (the path your agent watches
for skills) and run `pixi install` from that directory. Then read the
skill's SKILL.md to understand its phases and the Input/Output contract
for each. Confirm when the environment is ready.
```

**Option B — manual install:**

```bash
git clone https://github.com/cheahhl814/ena-submit.git
cd ena-submit
pixi install
```

> [!TIP]
> `pixi install` resolves every pinned tool from `pixi.toml` (channels: conda-forge, bioconda) into an isolated `.pixi/` environment — no system-wide installs, no version conflicts with other skills.

## 💡 Usage

The skill is designed to be driven by an AI agent: the agent reads the master `SKILL.md`, detects the current phase from the filesystem state of your run directory, and routes to the right sub-skill.

### Natural-language prompts that trigger the skill

```text
submit to ENA
ENA submission
submit raw reads to ENA
submit MAGs to ENA
submit bins to ENA
```

### Manual phase execution

If you prefer to drive the phases yourself (or want to re-run a single phase):

```bash
# Set your run directory (all phase artifacts land here)
RUN_DIR=/path/to/run-dir

pixi run preflight   # Phase 1 — validate inputs, write preflight.md + params.json
pixi run run         # Phase 2 — execute the workflow (after preflight ≥ GO)
pixi run qc          # Phase 3 — build the final report (after run completes)
pixi run debug       # On failure — interpret stderr via the signature library
pixi run battle-test # Verify the skill's structural integrity
```

> [!IMPORTANT]
> Each phase has an explicit **Inputs/Outputs contract** at the top of its sub-skill `SKILL.md`. If the upstream artifact is missing (e.g. you run `run` before `preflight` passed), the sub-skill refuses to proceed and tells you which phase to run first. Phases are gated on purpose — don't skip them.

## 🔬 Pipeline overview

The analysis follows a phased evidence chain. Each phase consumes the artifacts of the previous phase and gates progression with a Go/No-Go check.

| # | Phase | Goal | Sub-skill | Artifact produced |
|:--|:------|:-----|:----------|:------------------|
| **1** | **Preflight** | Validate samplesheet, Webin credentials, and study metadata; audit that `ena-webin-cli` (and, for mags/bins, the QC tools) are on PATH. | `preflight/` | `$RUN_DIR/preflight.md` |
| **2** | **Build** | Run the genome_evaluation QC tools (mags/bins only), build the manifest(s), and invoke `ena-webin-cli` directly. | `build/` | `$RUN_DIR/run-summary.md` |
| **3** | **Qc** | Aggregate the ena-webin-cli receipts and genome_evaluation QC outputs and write the final submission report. | `qc/` | `$RUN_DIR/seqsubmit-report.md` |
| **4** | **Debug** | Interpret ena-webin-cli / genome_evaluation QC tool failures via the signature library and recommend a fix. | `debug/` | `$RUN_DIR/debug-report.md` |
| **5** | **Battle-test** | Verify the new skill is structurally sound before declaring it ready. | `battle-test/` | `$RUN_DIR/battle-test-report.md` |

> [!TIP]
> Read each sub-skill's `SKILL.md` for the full procedure, its ask-user stop points, and its signature library (stderr pattern → cause → fix).

## 🧰 Tools

All tools are resolved from conda-forge/bioconda via the pinned `pixi.toml`.

| Tool | Version | Role |
|:-----|:--------|:-----|
| `ena-webin-cli` | * | ENA submission CLI (umbrella for all 4 modes: reads, metagenomic_assemblies, mags, bins) |
| `barrnap` | 0.9 | rRNA detection (used in genome_evaluation subworkflow) |
| `cat` | * | Contig Annotation Tool (CAT) for taxonomy classification of MAGs/bins |
| `checkm2` | * | MAG quality assessment (completeness/contamination) |
| `coverm` | * | read coverage / contig coverage / genome coverage |
| `trnascan-se` | 2.0 | tRNA detection (used in genome_evaluation subworkflow) |
| `multiqc` | 1.x | aggregate QC report |

Tool usage is grounded in the offline `docs-corpus/` snapshots (version-matched `--help`/`man` captures, upstream repo docs, and web docs as fallback) — the agent reads these instead of guessing flags. `docs-corpus/nf-core-seqsubmit/` is kept as a **reference spec only** (stage ordering, manifest formats, samplesheet schemas) — the pipeline itself is never invoked.

## 🔄 Update check

Every skill built with [bioinfo-skill-creator](https://github.com/cheahhl814/bioinfo-skill-creator) ships a self-update check that compares the deployed git SHA against this upstream repo via `git fetch` — no GitHub API call, no extra dependencies.

```bash
pixi run update-check
```

| Verdict | Exit | Meaning |
|:--------|:-----|:--------|
| `UP-TO-DATE` | 0 | Local HEAD matches origin/HEAD |
| `LOCAL-AHEAD` | 0 | Unpushed local commits; no action needed |
| `BEHIND-BY-N` | 1 | Upstream is N commits ahead → re-pull/re-sync from this repo |
| `OFFLINE` | 2 | `git fetch` failed; informational only |
| `NO-ORIGIN` | 2 | No `origin` remote configured; informational only |

## 📁 Repository layout

```text
ena-submit/
├── SKILL.md                 # Master orchestrator (router — start here)
├── README.md                # This file
├── pixi.toml                # Pinned tool environment (pixi install)
├── docs-corpus/             # Offline snapshots of upstream tool docs
│   └── ena-webin-cli/
│   └── barrnap/
│   └── cat/
│   └── checkm2/
│   └── coverm/
│   └── trnascan-se/
│   └── multiqc/
│   └── nf-core-seqsubmit/   # reference spec only (stage order, manifest formats) — never invoked
├── preflight/            # Phase sub-skill
├── build/            # Phase sub-skill
├── qc/            # Phase sub-skill
├── debug/            # Phase sub-skill
├── battle-test/            # Phase sub-skill
├── bin/
│   └── skill-update-check.py  # Self-update check (pixi run update-check)
└── bin/
    └── scaffold-render.py     # Reproducibility — re-render the skill from params.json
```

## 🔒 Hard guarantees

- **Filesystem evidence chain** — every phase emits the artifact the next phase consumes; the boundary between phases is the filesystem, not agent memory.
- **Docs-grounded tool usage** — tool flags come from `docs-corpus/`, never from the agent's memory.
- **Explicit stop points** — ambiguous decisions are surfaced to you as *Evidence + Recommend + Options*, not auto-picked.
- **Reproducible environments** — every tool is pinned in `pixi.toml` and resolved via pixi.

## Provenance

Built with the [bioinfo-skill-creator](https://github.com/cheahhl814/bioinfo-skill-creator) meta-skill (v1.1.0), following the AiX-BIO skill convention (preflight → build → debug → battle-test evidence chain). Pattern adopted from:

- **BettaMt-agents** — https://github.com/cheahhl814/BettaMt-agents
- **bacterial-genome-analysis** — https://github.com/cheahhl814/bacterial-genome-analysis
- **amr-gene-screening** — https://github.com/cheahhl814/amr-gene-screening

## License

Released under the MIT License — see the license file in this repository for details.