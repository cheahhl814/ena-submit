#!/usr/bin/env python3
"""Build sub-skill renderer for seqsubmit-agent.

Renders the bioinfo-skill-creator templates against params.json.
No nextflow-runner (user opted out). No lite tree (target_tiers = [large] only).
"""
import json
import os
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

META = Path("/home/cheahhl814/.agents/skills/bioinfo-skill-creator")
RUN_DIR = Path("/home/cheahhl814/claude_workspace/bioinformatics/AIx-BIO/skills/seqsubmit-agent")
TEMPLATES = META / "templates"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=False,
    lstrip_blocks=False,
)

params = json.loads((RUN_DIR / "params.json").read_text())

# Add flat-string defaults the templates expect
params.setdefault("skill_short_description",
    "Agent wrapper for the nf-core/seqsubmit pipeline (v1.0.0) — orchestrates 4 ENA submission modes (reads, metagenomic_assemblies, mags, bins) via Bash recipes. Wraps the upstream Nextflow pipeline as an external executor; pre-validates inputs and post-processes accession receipts.")
params.setdefault("use_case_1", "Submit raw sequencing reads to the European Nucleotide Archive (ENA) via the `reads` mode of nf-core/seqsubmit.")
params.setdefault("use_case_2", "Submit metagenomic assemblies to ENA via the `metagenomic_assemblies` mode.")
params.setdefault("use_case_3", "Submit MAGs or bins to ENA via the `mags` / `bins` mode (with `genome_evaluation` QC: rRNA, tRNA, CheckM2, CAT, coverage).")
params.setdefault("anti_use_case_1", "You do not have a Webin account at https://www.ebi.ac.uk/ena/submit/webin/login (the skill will refuse to proceed without ENA_WEBIN / ENA_WEBIN_PASSWORD set in Nextflow secrets).")
params.setdefault("anti_use_case_2", "You want to re-implement the Nextflow pipeline — the skill wraps the existing nf-core/seqsubmit as an external executor; it does not author its own DSL2.")

# Stage detection ladder
params["stage_detection_ladder"] = [
    {"name": "qc-done", "artifact": "seqsubmit-report.md"},
    {"name": "qc", "artifact": "qc-summary.md"},
    {"name": "run", "artifact": "run-summary.md"},
    {"name": "preflight", "artifact": "preflight.md"},
]

# Sub-skill subdirectory list (for repo layout)
# No with_nextflow_runner -> skip the runner
# target_tiers == [large] -> no lite tree

# Per-sub-skill definitions (drives the 5 SUB_SKILL_SKILL.md.j2 renders)
SUB_SKILLS = [
    {
        "dirname": "preflight",
        "subskill_dirname": "seqsubmit-agent-preflight",
        "sub_skill_name": "seqsubmit-agent-preflight",
        "sub_skill_title": "ENA Submission Preflight",
        "sub_skill_short_description": "Validate samplesheet, Webin credentials, and study metadata before invoking nf-core/seqsubmit.",
        "sub_skill_description": "Phase 1 of seqsubmit-agent. Validates the submission samplesheet (column set per `--mode`), confirms `ENA_WEBIN` and `ENA_WEBIN_PASSWORD` Nextflow secrets are set, resolves the study accession or study-registration file, and writes `preflight.md` + `params.json` with verdict GO / GO-WITH-WARNINGS / NO-GO. Mirrors the preflight evidence pattern from nf-core/seqsubmit docs.",
        "sub_skill_triggers": ["preflight ENA submission", "validate Webin credentials", "check seqsubmit samplesheet", "resolve study accession"],
        "sub_skill_phase_role": "input validation (preflight)",
        "sub_skill_use_case_1": "Validate the samplesheet column set against the chosen `--mode` (reads/metagenomic_assemblies/mags/bins) before invoking the upstream pipeline.",
        "sub_skill_use_case_2": "Confirm ENA Webin credentials and study accession are resolvable so the upstream `webin-cli` calls do not fail mid-submission.",
        "sub_skill_anti_use_case_1": "You have not yet chosen a submission mode — pick one of `reads | metagenomic_assemblies | mags | bins` first.",
        "sub_skill_user_inputs": [
            {"name": "`--mode` (reads | metagenomic_assemblies | mags | bins)", "required": "yes", "default": "ask"},
            {"name": "`--input` samplesheet.csv", "required": "yes", "default": "ask"},
            {"name": "`--centre_name`", "required": "yes", "default": "ask"},
            {"name": "`--submission_study` accession OR `--study_metadata` file", "required": "yes (one of)", "default": "ask"},
            {"name": "ENA Webin credentials", "required": "yes", "default": "`nextflow secrets set`"},
        ],
        "sub_skill_inputs": [
            {"path": "samplesheet.csv", "source": "user", "required": "yes"},
            {"path": "study_accession_or_metadata.{txt,tsv}", "source": "user", "required": "yes (one of)"},
        ],
        "sub_skill_outputs": [
            {"path": "preflight.md", "format": "Markdown", "notes": "human audit trail"},
            {"path": "params.json", "format": "JSON", "notes": "machine contract for the run sub-skill"},
            {"path": "preflight_evidence.txt", "format": "text", "notes": "raw evidence"},
        ],
        "sub_skill_artifact_machine": "params.json",
        "sub_skill_artifact_human": "preflight.md",
        "sub_skill_evidence_file": "preflight_evidence.txt",
        "sub_skill_verdict_artifact": "preflight.md",
        "sub_skill_verdict_pass": "GO",
        "sub_skill_verdict_pass_warn": "GO-WITH-WARNINGS",
        "sub_skill_verdict_fail": "NO-GO",
        "sub_skill_sp_count": "5",
        "sub_skill_sp1_title": "Mode / samplesheet mismatch",
        "sub_skill_sp1_trigger": "the samplesheet columns do not match the expected columns for `--mode` (reads/metagenomic_assemblies/mags/bins)",
        "sub_skill_sp1_evidence": "csv header diff vs the mode-specific required columns in `params.json: submission_modes`",
        "sub_skill_sp1_ask": "The samplesheet columns don't match the expected schema for `--mode <X>`. Pick: (A) I'll re-emit the samplesheet now, (B) auto-derive the mode from the header (best-match), (C) abort",
        "sub_skill_sp1_autopick": "the header exactly matches the expected schema for the chosen `--mode`. Default: proceed.",
        "sub_skill_first_evidence_step": "Mode detection — read `--mode` (or derive from samplesheet header)",
        "sub_skill_first_evidence_command": "MODE=$1; awk -F, 'NR==1{for(i=1;i<=NF;i++) h[i]=$i; print h[1]}' \"$SAMPLESHEET\"",
        "sub_skill_machine_field_1": "mode",
        "sub_skill_machine_value_1": "mags",
        "sub_skill_machine_field_2": "verdict",
        "sub_skill_machine_value_2": "GO",
        "sub_skill_evidence_checks": [
            {"name": "Mode resolved", "verdict": "✅", "value": "mags", "threshold": "one of reads|metagenomic_assemblies|mags|bins"},
            {"name": "Samplesheet columns", "verdict": "✅", "value": "all required present", "threshold": "matches mode schema"},
            {"name": "Webin secret ENA_WEBIN", "verdict": "✅", "value": "set (len 14)", "threshold": "starts with Webin-"},
            {"name": "Webin secret ENA_WEBIN_PASSWORD", "verdict": "✅", "value": "set (redacted)", "threshold": "non-empty"},
            {"name": "Study accession OR metadata file", "verdict": "✅", "value": "PRJEB12345", "threshold": "accession OR existing file"},
            {"name": "Output directory writable", "verdict": "✅", "value": "/path/to/outdir", "threshold": "writable"},
        ],
        "sub_skill_recommendation_1": "Proceed to `build/seqsubmit-agent-runner` with the validated samplesheet and resolved mode.",
        "sub_skill_recommendation_2": "If GO-WITH-WARNINGS: surface the warning column to the user before proceeding.",
        "sub_skill_next_skill": "build/seqsubmit-agent-runner",
        "sub_skill_upstream_evidence": "user-provided samplesheet + study accession + Webin credentials in Nextflow secrets.",
    },
    {
        "dirname": "build",
        "subskill_dirname": "seqsubmit-agent-runner",
        "sub_skill_name": "seqsubmit-agent-runner",
        "sub_skill_title": "Run nf-core/seqsubmit",
        "sub_skill_short_description": "Invoke the upstream nf-core/seqsubmit pipeline with the preflight-validated inputs.",
        "sub_skill_description": "Phase 2 of seqsubmit-agent. Constructs the `nextflow run nf-core/seqsubmit` command from `params.json` (mode, profile, input, centre_name, submission_study, outdir), starts the run, and watches the work directory. Writes `run-summary.md` + the Nextflow trace/timeline/report into `$RUN_DIR/trace/`, `$RUN_DIR/timeline/`, `$RUN_DIR/report/`. Does NOT author a local DSL2 runner — the upstream pipeline is the executor.",
        "sub_skill_triggers": ["run seqsubmit", "submit to ENA", "run nf-core/seqsubmit", "execute seqsubmit pipeline", "start ENA submission"],
        "sub_skill_phase_role": "execution (run)",
        "sub_skill_use_case_1": "Submit a batch of samples to ENA via the upstream nf-core/seqsubmit pipeline at version 1.0.0.",
        "sub_skill_use_case_2": "Run on the ENA test server (`--test_upload true`) to dry-run the submission before a real push.",
        "sub_skill_anti_use_case_1": "You want to author your own Nextflow pipeline — this skill wraps the existing upstream, not a new one.",
        "sub_skill_user_inputs": [
            {"name": "Container profile (docker|singularity|podman|conda|test)", "required": "yes", "default": "docker"},
            {"name": "`--outdir`", "required": "yes", "default": "ask"},
            {"name": "`--upload_tpa true|false`", "required": "no", "default": "false"},
            {"name": "`--test_upload true|false`", "required": "no", "default": "true (recommended)"},
        ],
        "sub_skill_inputs": [
            {"path": "preflight.md", "source": "preflight", "required": "yes (verdict ≥ GO-WITH-WARNINGS)"},
            {"path": "params.json", "source": "preflight", "required": "yes"},
        ],
        "sub_skill_outputs": [
            {"path": "run-summary.md", "format": "Markdown", "notes": "run log + accession table (if any)"},
            {"path": "trace/", "format": "Nextflow trace TSV", "notes": "nf-core standard"},
            {"path": "timeline/", "format": "Nextflow timeline HTML", "notes": "nf-core standard"},
            {"path": "report/", "format": "Nextflow report HTML", "notes": "nf-core standard"},
        ],
        "sub_skill_artifact_machine": "run-summary.md",
        "sub_skill_artifact_human": "run-summary.md",
        "sub_skill_evidence_file": "run.log",
        "sub_skill_verdict_artifact": "run-summary.md",
        "sub_skill_verdict_pass": "GO",
        "sub_skill_verdict_pass_warn": "GO-WITH-WARNINGS",
        "sub_skill_verdict_fail": "NO-GO",
        "sub_skill_sp_count": "4",
        "sub_skill_sp1_title": "Container profile not available",
        "sub_skill_sp1_trigger": "`docker --version` (or `singularity --version`, `podman --version`, `conda --version`) returns nothing for the chosen profile",
        "sub_skill_sp1_evidence": "missing container runtime vs `--profile <X>` choice",
        "sub_skill_sp1_ask": "Container runtime for profile `<X>` is not on PATH. Pick: (A) install the runtime now, (B) switch to `--profile conda` (slower but no daemon), (C) abort",
        "sub_skill_sp1_autopick": "the chosen runtime is on PATH. Default: proceed.",
        "sub_skill_first_evidence_step": "Verify container runtime",
        "sub_skill_first_evidence_command": "command -v docker || command -v singularity || command -v podman || command -v conda",
        "sub_skill_machine_field_1": "status",
        "sub_skill_machine_value_1": "submitted",
        "sub_skill_machine_field_2": "accessions",
        "sub_skill_machine_value_2": "[{sample, accession, receipt}]",
        "sub_skill_evidence_checks": [
            {"name": "Container runtime", "verdict": "✅", "value": "docker 27.x", "threshold": "one of docker/singularity/podman/conda"},
            {"name": "Nextflow version", "verdict": "✅", "value": "25.10.4", "threshold": "≥ 25.04.0 (nf-core/seqsubmit 1.0.0)"},
            {"name": "Pipeline pulled", "verdict": "✅", "value": "nf-core/seqsubmit 1.0.0", "threshold": "exact tag"},
            {"name": "Webin secrets set", "verdict": "✅", "value": "ENA_WEBIN + ENA_WEBIN_PASSWORD", "threshold": "non-empty"},
            {"name": "Run submission", "verdict": "✅", "value": "submitted to ENA test server", "threshold": "test_upload=true → OK; =false → real submission"},
        ],
        "sub_skill_recommendation_1": "After run completes, hand off to `qc/seqsubmit-agent-qc` to build the accession summary.",
        "sub_skill_recommendation_2": "If run failed, route to `debug/seqsubmit-agent-debug` with the failing stderr.",
        "sub_skill_next_skill": "qc/seqsubmit-agent-qc",
        "sub_skill_upstream_evidence": "preflight.md (GO/GO-WITH-WARNINGS) + params.json (mode, profile, outdir).",
    },
    {
        "dirname": "qc",
        "subskill_dirname": "seqsubmit-agent-qc",
        "sub_skill_name": "seqsubmit-agent-qc",
        "sub_skill_title": "ENA Submission QC + Accession Summary",
        "sub_skill_short_description": "Aggregate the per-mode accession receipts and write the final submission report.",
        "sub_skill_description": "Phase 3 of seqsubmit-agent. Parses the per-mode output directory (reads/ or metagenomic_assemblies/ or mags/, bins/) and `multiqc/`, collects accession numbers, MAGs/bins manifest, coverage files, and the MultiQC report. Writes `seqsubmit-report.md` (the per-submission audit report) and `qc-summary.md` (the machine-readable summary).",
        "sub_skill_triggers": ["build ENA submission report", "summarise accession numbers", "qc seqsubmit output", "collect MAG accessions"],
        "sub_skill_phase_role": "output (qc)",
        "sub_skill_use_case_1": "Collect accession numbers per sample after a successful ENA submission.",
        "sub_skill_use_case_2": "Aggregate the per-mode outputs (manifest TSVs, MultiQC report, MAGs/bins metadata) into a single audit-trail report.",
        "sub_skill_anti_use_case_1": "The pipeline run failed — route to `debug/seqsubmit-agent-debug` first.",
        "sub_skill_user_inputs": [
            {"name": "Submission mode (mags/bins/metagenomic_assemblies/reads)", "required": "yes", "default": "from params.json"},
        ],
        "sub_skill_inputs": [
            {"path": "run-summary.md", "source": "build/seqsubmit-agent-runner", "required": "yes"},
            {"path": "outdir/<mode>/", "source": "build", "required": "yes (mode-specific)"},
            {"path": "outdir/multiqc/", "source": "build", "required": "no (but aggregated when present)"},
        ],
        "sub_skill_outputs": [
            {"path": "seqsubmit-report.md", "format": "Markdown", "notes": "per-submission audit report (the deliverable)"},
            {"path": "qc-summary.md", "format": "Markdown", "notes": "machine-readable summary table"},
        ],
        "sub_skill_artifact_machine": "qc-summary.md",
        "sub_skill_artifact_human": "seqsubmit-report.md",
        "sub_skill_evidence_file": "qc-evidence.txt",
        "sub_skill_verdict_artifact": "seqsubmit-report.md",
        "sub_skill_verdict_pass": "GO",
        "sub_skill_verdict_pass_warn": "GO-WITH-WARNINGS",
        "sub_skill_verdict_fail": "NO-GO",
        "sub_skill_sp_count": "3",
        "sub_skill_sp1_title": "Outdir missing per-mode output",
        "sub_skill_sp1_trigger": "`outdir/<mode>/` is missing the expected submission-receipt files (e.g. `*_webin_cli.log`, `manifest.tsv`, `genome_metadata.tsv`)",
        "sub_skill_sp1_evidence": "file-glob against the mode-specific expected outputs",
        "sub_skill_sp1_ask": "The per-mode output dir is missing expected submission files. Pick: (A) the run did not actually submit (re-run with `--test_upload false`), (B) the run hit an error mid-flight (route to debug), (C) accept the partial output and report what's there",
        "sub_skill_sp1_autopick": "all expected files are present. Default: proceed.",
        "sub_skill_first_evidence_step": "Mode-specific output inventory",
        "sub_skill_first_evidence_command": "ls -la $OUTDIR/$MODE/",
        "sub_skill_machine_field_1": "samples_submitted",
        "sub_skill_machine_value_1": "10",
        "sub_skill_machine_field_2": "verdict",
        "sub_skill_machine_value_2": "GO",
        "sub_skill_evidence_checks": [
            {"name": "Per-mode output dir present", "verdict": "✅", "value": "outdir/mags/", "threshold": "exists"},
            {"name": "Accession receipts", "verdict": "✅", "value": "10/10 samples have accessions", "threshold": "≥ 90% of samples have non-empty accessions"},
            {"name": "MAGs/bins manifest (mags/bins mode)", "verdict": "✅", "value": "genome_metadata.tsv", "threshold": "exists when mode is mags/bins"},
            {"name": "MultiQC report", "verdict": "✅", "value": "multiqc_report.html", "threshold": "exists"},
            {"name": "Pipeline info complete", "verdict": "✅", "value": "trace + timeline + report", "threshold": "all 3 present"},
        ],
        "sub_skill_recommendation_1": "Submit is complete. `seqsubmit-report.md` is the audit-trail deliverable.",
        "sub_skill_recommendation_2": "If verdict is NO-GO (failed samples), surface the per-sample failure to the user; they can re-run with `--test_upload false` to actually submit.",
        "sub_skill_next_skill": "(end of pipeline — deliverable is seqsubmit-report.md)",
        "sub_skill_upstream_evidence": "run-summary.md + the per-mode outdir/ tree produced by nf-core/seqsubmit.",
    },
    {
        "dirname": "debug",
        "subskill_dirname": "seqsubmit-agent-debug",
        "sub_skill_name": "seqsubmit-agent-debug",
        "sub_skill_title": "Debug: ENA Submission Failures",
        "sub_skill_short_description": "Interpret nf-core/seqsubmit failures via the signature library and recommend a fix.",
        "sub_skill_description": "Phase 4 (optional) of seqsubmit-agent. Reads the failing stderr / Nextflow log / ENA Webin CLI receipt and matches it against the signature library (e.g. 'Webin authentication failed', 'checkm2_db not found', 'samplesheet missing column <X>', 'study accession already has private status'). Writes `debug-report.md` with diagnosis + fix.",
        "sub_skill_triggers": ["debug ENA submission failure", "interpret seqsubmit error", "Webin CLI error", "nf-core/seqsubmit failed"],
        "sub_skill_phase_role": "failure-interpretation (debug)",
        "sub_skill_use_case_1": "Diagnose a failing `nextflow run nf-core/seqsubmit` invocation by matching the stderr against the signature library.",
        "sub_skill_use_case_2": "Surface a concrete, runnable fix (e.g. reset Webin secrets, re-download the CheckM2 database, fix a samplesheet column).",
        "sub_skill_anti_use_case_1": "The run succeeded — you do not need a debug pass.",
        "sub_skill_user_inputs": [
            {"name": "Failing command + stderr", "required": "yes", "default": "ask"},
            {"name": "Mode (mags/bins/metagenomic_assemblies/reads)", "required": "yes", "default": "from params.json"},
        ],
        "sub_skill_inputs": [
            {"path": "run.log", "source": "build/seqsubmit-agent-runner", "required": "yes"},
            {"path": "preflight.md", "source": "preflight", "required": "yes"},
        ],
        "sub_skill_outputs": [
            {"path": "debug-report.md", "format": "Markdown", "notes": "diagnosis + fix"},
        ],
        "sub_skill_artifact_machine": "debug-report.md",
        "sub_skill_artifact_human": "debug-report.md",
        "sub_skill_evidence_file": "debug-evidence.txt",
        "sub_skill_verdict_artifact": "debug-report.md",
        "sub_skill_verdict_pass": "RECOVERABLE",
        "sub_skill_verdict_pass_warn": "RECOVERABLE",
        "sub_skill_verdict_fail": "BLOCKED",
        "sub_skill_sp_count": "5",
        "sub_skill_sp1_title": "Failure signature not in library",
        "sub_skill_sp1_trigger": "the stderr / log does not match any of the 5+ entries in the signature library",
        "sub_skill_sp1_evidence": "grep against the signature library table below returns 0 matches",
        "sub_skill_sp1_ask": "The failure does not match a known signature. Pick: (A) run a short investigation loop (re-read docs-corpus, re-run with `-with-dump-hashes` etc.), (B) escalate to the user with the raw stderr, (C) abort",
        "sub_skill_sp1_autopick": "a known signature matches. Default: emit the diagnosis from the library entry.",
        "sub_skill_first_evidence_step": "Match stderr against the signature library",
        "sub_skill_first_evidence_command": "grep -F -f sigs.txt $RUN_DIR/run.log",
        "sub_skill_machine_field_1": "signature",
        "sub_skill_machine_value_1": "WEBIN_AUTH_FAILED",
        "sub_skill_machine_field_2": "verdict",
        "sub_skill_machine_value_2": "RECOVERABLE",
        "sub_skill_evidence_checks": [
            {"name": "Signature match", "verdict": "✅", "value": "WEBIN_AUTH_FAILED", "threshold": "one of the entries in the library"},
            {"name": "Recoverable vs blocked", "verdict": "✅", "value": "RECOVERABLE", "threshold": "non-blocked → re-run preflight or run"},
            {"name": "Suggested fix", "verdict": "✅", "value": "re-set Nextflow secrets", "threshold": "concrete command"},
        ],
        "sub_skill_recommendation_1": "Apply the fix, then loop back to the relevant sub-skill (usually preflight or run).",
        "sub_skill_recommendation_2": "If BLOCKED, escalate to the user — the failure is environmental (e.g. ENA service outage, study-private conflict).",
        "sub_skill_next_skill": "(loops back to the sub-skill whose artifact the failure invalidated)",
        "sub_skill_upstream_evidence": "failing stderr + the preflight.md + run-summary.md that the failure invalidated.",
    },
    {
        "dirname": "battle-test",
        "subskill_dirname": "seqsubmit-agent-battle-test",
        "sub_skill_name": "seqsubmit-agent-battle-test",
        "sub_skill_title": "Battle-Test: Skill Structural Integrity",
        "sub_skill_short_description": "Verify the new skill is structurally sound before declaring it ready.",
        "sub_skill_description": "Phase 5 of seqsubmit-agent. Runs 8+ structural smoke tests: frontmatter coherence across all 5 sub-skill SKILL.md files, signature-library completeness (≥ 3 entries each in preflight/qc/debug), docs-corpus freshness (every tool in pixi.toml has docs-corpus/<tool>/README.md), pixi.toml parses, bin/skill-update-check.py parses, README hygiene (no machine-specific paths, no unfilled slots), git init status. Writes `battle-test-report.md` with PASS/PASS-WITH-WARNINGS/FAIL.",
        "sub_skill_triggers": ["battle-test the skill", "verify skill integrity", "structural smoke test", "skill quality gate"],
        "sub_skill_phase_role": "structural verification (battle-test)",
        "sub_skill_use_case_1": "Verify the new skill is structurally sound (frontmatter coherence, signature-library completeness, docs-corpus freshness, pixi.toml parse, README hygiene).",
        "sub_skill_use_case_2": "Get a PASS / PASS-WITH-WARNINGS / FAIL verdict before shipping the skill to GitHub.",
        "sub_skill_anti_use_case_1": "You have not yet scaffolded the skill — run `build/skill-builder` first.",
        "sub_skill_user_inputs": [
            {"name": "`--execution` flag (optional — runs real tools if available)", "required": "no", "default": "off"},
        ],
        "sub_skill_inputs": [
            {"path": "SKILL.md", "source": "this skill", "required": "yes"},
            {"path": "README.md", "source": "this skill", "required": "yes"},
            {"path": "pixi.toml", "source": "this skill", "required": "yes"},
            {"path": "preflight/, build/, qc/, debug/ sub-skill SKILL.md files", "source": "this skill", "required": "yes"},
            {"path": "docs-corpus/", "source": "this skill", "required": "yes"},
        ],
        "sub_skill_outputs": [
            {"path": "battle-test-report.md", "format": "Markdown", "notes": "PASS / PASS-WITH-WARNINGS / FAIL"},
        ],
        "sub_skill_artifact_machine": "battle-test-report.md",
        "sub_skill_artifact_human": "battle-test-report.md",
        "sub_skill_evidence_file": "battle-test-evidence.txt",
        "sub_skill_verdict_artifact": "battle-test-report.md",
        "sub_skill_verdict_pass": "PASS",
        "sub_skill_verdict_pass_warn": "PASS-WITH-WARNINGS",
        "sub_skill_verdict_fail": "FAIL",
        "sub_skill_sp_count": "3",
        "sub_skill_sp1_title": "Frontmatter version mismatch across sub-skills",
        "sub_skill_sp1_trigger": "the version field in any sub-skill's `SKILL.md` does not match the orchestrator's `version`",
        "sub_skill_sp1_evidence": "grep -E '^version:' across all SKILL.md files in this skill",
        "sub_skill_sp1_ask": "Sub-skill `<X>` declares version `<V1>` but the orchestrator declares `<V2>`. Pick: (A) bump `<X>` to `<V2>`, (B) downgrade the orchestrator to `<V1>`, (C) accept the mismatch (PASS-WITH-WARNINGS)",
        "sub_skill_sp1_autopick": "all versions match. Default: proceed.",
        "sub_skill_first_evidence_step": "Frontmatter version coherence",
        "sub_skill_first_evidence_command": "grep -E '^version:' $(find . -name 'SKILL.md')",
        "sub_skill_machine_field_1": "checks_passed",
        "sub_skill_machine_value_1": "8",
        "sub_skill_machine_field_2": "verdict",
        "sub_skill_machine_value_2": "PASS",
        "sub_skill_evidence_checks": [
            {"name": "Frontmatter coherence (5 SKILL.md files)", "verdict": "✅", "value": "8/8", "threshold": "all pass"},
            {"name": "Signature-library completeness", "verdict": "✅", "value": "≥ 3 entries per sub-skill", "threshold": "≥ 3"},
            {"name": "Docs-corpus freshness", "verdict": "✅", "value": "7/7 tools covered", "threshold": "all tools in pixi.toml covered"},
            {"name": "pixi.toml parses", "verdict": "✅", "value": "pixi lock --dry-run", "threshold": "exit 0"},
            {"name": "bin/skill-update-check.py parses", "verdict": "✅", "value": "py_compile", "threshold": "exit 0"},
            {"name": "README hygiene (no machine paths, no unfilled slots)", "verdict": "✅", "value": "0 hits", "threshold": "0 hits"},
            {"name": "git init status", "verdict": "✅", "value": "clean", "threshold": "initialised + clean"},
            {"name": ".gitignore covers work/ + docs-corpus/.fingerprints", "verdict": "✅", "value": "present", "threshold": "both entries present"},
        ],
        "sub_skill_recommendation_1": "If PASS, the skill is ready to ship. `git add -A && git commit -m 'v1.0.0: initial scaffold' && git push -u origin master` and `rsync -av --delete` to `~/.pi/agent/skills/seqsubmit-agent/`.",
        "sub_skill_recommendation_2": "If PASS-WITH-WARNINGS, surface the warnings and decide whether to ship or fix first.",
        "sub_skill_next_skill": "(end of pipeline — ship the skill)",
        "sub_skill_upstream_evidence": "the new skill itself (SKILL.md, README.md, pixi.toml, all sub-skill SKILL.md files, docs-corpus/, bin/skill-update-check.py).",
    },
]

# Stage detection ladder for orchestrator (used inside SKILL.md render)
# Build a structured sub_skills list for the README's phase overview table.
params["sub_skills"] = [
    {"name": s["dirname"], "purpose": s["sub_skill_short_description"], "artifact": s["sub_skill_artifact_human"]}
    for s in SUB_SKILLS
]

# pixi channels default
params.setdefault("pixi_channels", ["conda-forge", "bioconda"])
params.setdefault("license", "MIT")

# 1. Render the orchestrator SKILL.md
master = env.get_template("ORCHESTRATOR_SKILL.md.j2")
(RUN_DIR / "SKILL.md").write_text(master.render(**params))

# 2. Render the 5 sub-skill SKILL.md files
sub_tmpl = env.get_template("SUB_SKILL_SKILL.md.j2")
for s in SUB_SKILLS:
    sdir = RUN_DIR / s["dirname"] / s["subskill_dirname"]
    sdir.mkdir(parents=True, exist_ok=True)
    s_params = dict(params, **s)
    (sdir / "SKILL.md").write_text(sub_tmpl.render(**s_params))

# 3. Render the README.md
readme = env.get_template("README.md.j2")
(RUN_DIR / "README.md").write_text(readme.render(**params))

# 4. Render the pixi.toml
pixi = env.get_template("pixi.toml.j2")
# Drop external tools (system prerequisites, not conda-resolvable)
# nextflow is installed via `curl -s https://get.nextflow.io | bash`, not conda.
pixi_tools = [t for t in params["tool_inventory"] if t.get("status") == "found"]
params_for_pixi = dict(params, tool_inventory=pixi_tools)
# We need to use bioconda channel because at least one tool is bioconda-only
# Override the channel logic — the template's check is too narrow.
# Manually fix: ena-webin-cli, cat, checkm2, coverm, trnascan-se, multiqc are all in bioconda.
# So we need [conda-forge, bioconda] unconditionally.
pixi_text = pixi.render(**params_for_pixi)
# Patch channels: always include bioconda since all our tools are bioconda
pixi_text = pixi_text.replace(
    'channels = ["conda-forge"]',
    'channels = ["conda-forge", "bioconda"]',
)
# Add a system-requirements comment after [dependencies] for non-conda tools
external_tools = [t for t in params["tool_inventory"] if t.get("status") != "found"]
if external_tools:
    external_block = "\n# === System prerequisites (not installed via pixi; install outside the env) ===\n"
    for t in external_tools:
        external_block += f"# {t['name']} (version {t['version']}, role: {t['role']}) — install via system package manager or upstream installer.\n"
    pixi_text = pixi_text.replace(
        "[tasks]",
        external_block + "\n[tasks]",
    )
(RUN_DIR / "pixi.toml").write_text(pixi_text)

# 5. Render bin/skill-update-check.py
(RUN_DIR / "bin").mkdir(exist_ok=True)
update_script = env.get_template("bin/skill-update-check.py.j2")
# The script template uses `{{ skill_target }}` too — supply it
params["skill_target"] = params["skill_name"]
update_path = RUN_DIR / "bin" / "skill-update-check.py"
update_path.write_text(update_script.render(**params))
update_path.chmod(0o755)

# 6. .gitignore
(RUN_DIR / ".gitignore").write_text("""# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.eggs/

# pixi
.pixi/
pixi.lock

# work / run artefacts
work/
outdir/
trace/
timeline/
report/
run.log
nextflow.log*

# docs-corpus fingerprints
docs-corpus/.fingerprints

# macOS
.DS_Store
""")

print("Build complete:")
for p in sorted(RUN_DIR.rglob("*")):
    if p.is_file():
        rel = p.relative_to(RUN_DIR)
        print(f"  {rel}  ({p.stat().st_size} bytes)")
