# Battle-Test Report: ena-submit

Skill:        ena-submit
Run:          /home/cheahhl814/claude_workspace/bioinformatics/AIx-BIO/skills/ena-submit
Generated:    2026-09-12T16:15:00Z
Meta-skill:   bioinfo-skill-creator v1.2.0
Upstream:     https://github.com/nf-core/seqsubmit (v1.0.0)

## Overall verdict

**PASS** ✅

All 23 structural smoke tests pass. The skill is ready to commit and push to `github.com/cheahhl814/ena-submit`.

## Test results

```
Running 23 structural smoke tests against /home/cheahhl814/claude_workspace/bioinformatics/AIx-BIO/skills/ena-submit

OK    all top-level files present (SKILL.md, README.md, pixi.toml, .gitignore, params.json, preflight.md)
OK    all 5 sub-skill SKILL.md files present
OK    bin/skill-update-check.py present and executable
OK    SKILL.md frontmatter coherent, version=1.0.0
OK    all 5 sub-skill frontmatter coherent (version=1.0.0)
OK    all sub-skill `name` fields match their directory names
OK    signature libraries present in all 5 sub-skills (≥ 3 entries each)
OK    ask-user stop points present in all 5 sub-skills
OK    Inputs/Outputs contracts present in all sub-skills
OK    docs-corpus covers all 7 tools + nf-core-seqsubmit snapshot
OK    docs-corpus entries have no machine-specific paths
OK    docs-corpus/.fingerprints manifest present and populated
OK    pixi.toml channels correct (conda-forge, bioconda)
OK    pixi.toml pins all 7 tools
OK    pixi.toml declares all 6 expected tasks (preflight, run, qc, debug, battle-test, update-check)
OK    .gitignore covers work/, docs-corpus/.fingerprints, .pixi/, pixi.lock
OK    README.md has no machine-specific paths
OK    README.md has no unfilled template slots
OK    README.md has all 10 standard sections
OK    bin/skill-update-check.py parses as Python
OK    params.json valid, verdict=GO
OK    preflight.md present with overall verdict GO/GO-WITH-WARNINGS
OK    evidence chain complete (16 artifacts)

PASS  23/23 tests passed
```

## Per-check table

| # | Check | Verdict | Notes |
|---|---|---|---|
| 1 | Top-level files present | ✅ | SKILL.md, README.md, pixi.toml, .gitignore, params.json, preflight.md |
| 2 | Sub-skill dirs + SKILL.md files | ✅ | 5/5 present: preflight/, build/, qc/, debug/, battle-test/ |
| 3 | bin/skill-update-check.py present + executable | ✅ | 6,948 bytes, +x set, renders from `templates/bin/skill-update-check.py.j2` |
| 4 | Master SKILL.md frontmatter | ✅ | name, description, version=1.0.0, updated, triggers all present |
| 5 | Sub-skill frontmatter coherence | ✅ | All 5 sub-skills match master version=1.0.0 |
| 6 | Sub-skill name field ↔ dir name | ✅ | All 5 sub-skill `name` fields match their directory names |
| 7 | Signature-library completeness | ✅ | All 5 sub-skills have ≥ 3 entries in the Troubleshooting table |
| 8 | Ask-user stop points | ✅ | All 5 sub-skills have ≥ 1 SP (master has 5 + master SP0) |
| 9 | Inputs/Outputs contracts | ✅ | All 5 sub-skills have `## 0. Inputs / Outputs contract` |
| 10 | Docs-corpus dirs | ✅ | 7/7 tools + nf-core-seqsubmit snapshot |
| 11 | Docs-corpus hygiene (no machine paths) | ✅ | 0 hits for /home/, /Users/, /mnt/, /scratch/ |
| 12 | Docs-corpus fingerprints | ✅ | 14 entries in `docs-corpus/.fingerprints` |
| 13 | pixi.toml channels | ✅ | `["conda-forge", "bioconda"]` |
| 14 | pixi.toml tools | ✅ | 7/7 tools pinned (ena-webin-cli, barrnap, cat, checkm2, coverm, trnascan-se, multiqc) |
| 15 | pixi.toml tasks | ✅ | 6/6 tasks (preflight, run, qc, debug, battle-test, update-check) |
| 16 | .gitignore | ✅ | Covers work/, docs-corpus/.fingerprints, .pixi/, pixi.lock |
| 17 | README.md hygiene — no machine paths | ✅ | 0 hits |
| 18 | README.md hygiene — no unfilled slots | ✅ | 0 hits for `[slot]`, `[Describe]`, `{{`, `{%` |
| 19 | README.md required sections | ✅ | All 10 standard sections present (Contents, Installation, Usage, Pipeline overview, Tools, Update check, Repository layout, Hard guarantees, Provenance, License) |
| 20 | bin/skill-update-check.py parses | ✅ | `py_compile` exit 0 |
| 21 | params.json valid | ✅ | verdict=GO, all required fields present |
| 22 | preflight.md verdict | ✅ | Overall verdict GO |
| 23 | Evidence chain complete | ✅ | 16/16 expected artifacts present |

## Specific notes

- **No nextflow-runner** (per user SP7 explicit opt-out at `params.json: with_nextflow_runner = false`): the skill wraps the upstream `nf-core/seqsubmit` pipeline as an external executor, not a local DSL2 runner.
- **No lite tree** (per `params.json: target_tiers = ["large"]`): the skill is large-model only; no `<name>-lite/` sibling.
- **`nextflow` is a system prerequisite**, not a pixi dep (the conda channels don't ship it). The pixi.toml lists it as a comment under `[dependencies]` and the README mentions `curl -s https://get.nextflow.io | bash` as the install path.
- **docs-corpus quality**: every tool has at least a curated `README.md` index (the per-skill's primary documentation surface). For tools that are *also* invoked internally by the upstream pipeline (e.g. `cat` via `fasta_classify_catpack`, `barrnap` via `genome_evaluation`), the agent does not call them directly — the corpus exists to ground any future direct invocation. The `nf-core-seqsubmit/` entry has the full snapshot (README, usage, output, nextflow_schema.json) for the per-mode parameters.

## Handoff

Verdict is `PASS`. The skill is ready to ship.

Recommended next steps:

```bash
cd /home/cheahhl814/claude_workspace/bioinformatics/AIx-BIO/skills/ena-submit

# 1. git init + first commit
git init --initial-branch=master
git config user.email "<your.email>"
git config user.name "<your.name>"
git add -A
git commit -m "v1.0.0: initial scaffold of ena-submit (no nextflow runner)"

# 2. create the GitHub repo and push
gh repo create cheahhl814/ena-submit --public --source=. --remote=origin --push
# (or: git remote add origin https://github.com/cheahhl814/ena-submit.git && git push -u origin master)

# 3. deploy to pi skills directory
rsync -av --delete . ~/.pi/agent/skills/ena-submit/
diff -rq . ~/.pi/agent/skills/ena-submit/   # expect zero content differences

# 4. (optional) verify the update check
cd ~/.pi/agent/skills/ena-submit
pixi run update-check
```

## Reproducibility

- preflight.md: `$RUN_DIR/preflight.md`
- skill-built.md: `$RUN_DIR/skill-built.md`
- this report: `$RUN_DIR/battle-test-report.md`
- test_smoke.py: `$RUN_DIR/test_smoke.py` (re-runnable: `python3 test_smoke.py`)
