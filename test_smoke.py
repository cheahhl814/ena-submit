#!/usr/bin/env python3
"""ena-submit structural smoke tests.

Run:  python3 test_smoke.py

23 tests, mirroring the bioinfo-skill-creator v1.1+ convention.
Exit 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# ponytail: stdlib only. Single file. Verifies structural integrity of the skill.


SKILL_ROOT = Path(__file__).resolve().parent
SUB_SKILL_DIRS = ["preflight", "build", "qc", "debug", "battle-test"]
SUB_SKILL_NAMES = [
    "ena-submit-preflight",
    "ena-submit-runner",
    "ena-submit-qc",
    "ena-submit-debug",
    "ena-submit-battle-test",
]
EXPECTED_VERSION = "1.0.0"
EXPECTED_UPDATED = "2026-09-12"
EXPECTED_TOOLS = [
    "ena-webin-cli", "barrnap", "cat", "checkm2",
    "coverm", "trnascan-se", "multiqc",
]


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"OK    {msg}")


def test_count() -> int:
    return sum(1 for _ in range(1, 100))


# Test 1-3: file presence
def test_skills_exist() -> bool:
    required = ["SKILL.md", "README.md", "pixi.toml", ".gitignore", "params.json", "preflight.md"]
    for r in required:
        if not (SKILL_ROOT / r).is_file():
            fail(f"missing top-level file: {r}")
            return False
    ok("all top-level files present (SKILL.md, README.md, pixi.toml, .gitignore, params.json, preflight.md)")
    return True


def test_sub_skill_dirs() -> bool:
    for d, n in zip(SUB_SKILL_DIRS, SUB_SKILL_NAMES):
        path = SKILL_ROOT / d / n / "SKILL.md"
        if not path.is_file():
            fail(f"missing sub-skill: {path.relative_to(SKILL_ROOT)}")
            return False
    ok(f"all {len(SUB_SKILL_DIRS)} sub-skill SKILL.md files present")
    return True


def test_bin_update_check() -> bool:
    p = SKILL_ROOT / "bin" / "skill-update-check.py"
    if not p.is_file():
        fail("bin/skill-update-check.py missing")
        return False
    if not os.access(p, os.X_OK):
        fail("bin/skill-update-check.py not executable (+x)")
        return False
    ok("bin/skill-update-check.py present and executable")
    return True


# Test 4-6: frontmatter coherence
def test_master_frontmatter() -> bool:
    text = (SKILL_ROOT / "SKILL.md").read_text()
    for field in ("name", "description", "version", "updated", "triggers"):
        if not re.search(rf"^{field}:", text, re.MULTILINE):
            fail(f"SKILL.md missing frontmatter field: {field}")
            return False
    m = re.search(r"^version:\s*['\"]?([^'\"\n]+)['\"]?", text, re.MULTILINE)
    if not m or m.group(1).strip() != EXPECTED_VERSION:
        fail(f"SKILL.md version != {EXPECTED_VERSION}")
        return False
    ok(f"SKILL.md frontmatter coherent, version={EXPECTED_VERSION}")
    return True


def test_sub_skill_frontmatter() -> bool:
    for d, n in zip(SUB_SKILL_DIRS, SUB_SKILL_NAMES):
        text = (SKILL_ROOT / d / n / "SKILL.md").read_text()
        for field in ("name", "description", "version", "updated", "triggers"):
            if not re.search(rf"^{field}:", text, re.MULTILINE):
                fail(f"{d}/{n}/SKILL.md missing frontmatter field: {field}")
                return False
        m = re.search(r"^version:\s*['\"]?([^'\"\n]+)['\"]?", text, re.MULTILINE)
        if not m or m.group(1).strip() != EXPECTED_VERSION:
            fail(f"{d}/{n}/SKILL.md version != {EXPECTED_VERSION}")
            return False
    ok(f"all {len(SUB_SKILL_DIRS)} sub-skill frontmatter coherent (version={EXPECTED_VERSION})")
    return True


def test_sub_skill_names() -> bool:
    """Verify the sub-skill name in frontmatter matches the directory name."""
    for d, n in zip(SUB_SKILL_DIRS, SUB_SKILL_NAMES):
        text = (SKILL_ROOT / d / n / "SKILL.md").read_text()
        m = re.search(r"^name:\s*['\"]?([^'\"\n]+)['\"]?", text, re.MULTILINE)
        if not m or m.group(1).strip() != n:
            fail(f"{d}/{n}/SKILL.md name field != {n}")
            return False
    ok("all sub-skill `name` fields match their directory names")
    return True


# Test 7-9: signature-library completeness
def test_signature_library_present() -> bool:
    """Every sub-skill SKILL.md must have a 'Troubleshooting — Signature library' section with at least 3 entries."""
    for d, n in zip(SUB_SKILL_DIRS, SUB_SKILL_NAMES):
        text = (SKILL_ROOT / d / n / "SKILL.md").read_text()
        if "## Troubleshooting" not in text and "## Troubleshooting — Signature library" not in text:
            fail(f"{d}/{n}/SKILL.md missing Troubleshooting section")
            return False
        # Count the number of table rows in the signature library table (rough proxy: lines starting with '| `')
        sig_rows = len(re.findall(r"^\|\s+`", text, re.MULTILINE))
        if sig_rows < 3:
            fail(f"{d}/{n}/SKILL.md signature library has only {sig_rows} entries (need ≥ 3)")
            return False
    ok(f"signature libraries present in all {len(SUB_SKILL_DIRS)} sub-skills (≥ 3 entries each)")
    return True


def test_ask_user_stop_points() -> bool:
    """Every sub-skill SKILL.md must have a stop points section (SP1+)."""
    for d, n in zip(SUB_SKILL_DIRS, SUB_SKILL_NAMES):
        text = (SKILL_ROOT / d / n / "SKILL.md").read_text()
        sp_count = len(re.findall(r"^### SP\d+\s+—", text, re.MULTILINE))
        if sp_count < 1:
            fail(f"{d}/{n}/SKILL.md has 0 stop points (need ≥ 1)")
            return False
    ok(f"ask-user stop points present in all {len(SUB_SKILL_DIRS)} sub-skills")
    return True


def test_io_contracts() -> bool:
    """Each sub-skill SKILL.md must have an Inputs/Outputs contract section."""
    for d, n in zip(SUB_SKILL_DIRS, SUB_SKILL_NAMES):
        text = (SKILL_ROOT / d / n / "SKILL.md").read_text()
        if "## 0. Inputs / Outputs contract" not in text:
            fail(f"{d}/{n}/SKILL.md missing Inputs/Outputs contract")
            return False
    ok("Inputs/Outputs contracts present in all sub-skills")
    return True


# Test 10-12: docs-corpus freshness
def test_docs_corpus_dirs() -> bool:
    """Every tool in pixi.toml must have a docs-corpus/<tool>/ directory with a README.md."""
    for tool in EXPECTED_TOOLS:
        d = SKILL_ROOT / "docs-corpus" / tool
        if not d.is_dir():
            fail(f"missing docs-corpus dir: {tool}/")
            return False
        if not (d / "README.md").is_file():
            fail(f"missing docs-corpus index: {tool}/README.md")
            return False
    # nf-core-seqsubmit snapshot is optional but recommended
    if not (SKILL_ROOT / "docs-corpus" / "nf-core-seqsubmit" / "README.md").is_file():
        fail("missing docs-corpus/nf-core-seqsubmit/README.md (upstream snapshot index)")
        return False
    ok(f"docs-corpus covers all {len(EXPECTED_TOOLS)} tools + nf-core-seqsubmit snapshot")
    return True


def test_docs_corpus_no_machine_paths() -> bool:
    """docs-corpus entries must not contain machine-specific paths."""
    bad_paths = re.compile(r"/home/[^/\s]+|/Users/[^/\s]+|/mnt/|/scratch/")
    for p in (SKILL_ROOT / "docs-corpus").rglob("*.md"):
        text = p.read_text()
        hits = bad_paths.findall(text)
        if hits:
            fail(f"{p.relative_to(SKILL_ROOT)} contains machine-specific path: {hits[0]}")
            return False
    ok("docs-corpus entries have no machine-specific paths")
    return True


def test_docs_corpus_fingerprints() -> bool:
    fp = SKILL_ROOT / "docs-corpus" / ".fingerprints"
    if not fp.is_file():
        fail("docs-corpus/.fingerprints missing")
        return False
    if len(fp.read_text().splitlines()) < 5:
        fail("docs-corpus/.fingerprints has < 5 entries (expected at least 9)")
        return False
    ok("docs-corpus/.fingerprints manifest present and populated")
    return True


# Test 13-15: pixi.toml + bin/ + .gitignore
def test_pixi_toml_channels() -> bool:
    text = (SKILL_ROOT / "pixi.toml").read_text()
    if 'channels = ["conda-forge", "bioconda"]' not in text:
        fail('pixi.toml channels must be ["conda-forge", "bioconda"]')
        return False
    ok("pixi.toml channels correct (conda-forge, bioconda)")
    return True


def test_pixi_toml_tools() -> bool:
    text = (SKILL_ROOT / "pixi.toml").read_text()
    for tool in EXPECTED_TOOLS:
        if f"{tool} =" not in text:
            fail(f"pixi.toml missing tool: {tool}")
            return False
    ok(f"pixi.toml pins all {len(EXPECTED_TOOLS)} tools")
    return True


def test_pixi_toml_tasks() -> bool:
    text = (SKILL_ROOT / "pixi.toml").read_text()
    for task in ("preflight", "run", "qc", "debug", "battle-test", "update-check"):
        if f"{task} =" not in text:
            fail(f"pixi.toml missing task: {task}")
            return False
    ok("pixi.toml declares all 6 expected tasks (preflight, run, qc, debug, battle-test, update-check)")
    return True


def test_gitignore() -> bool:
    text = (SKILL_ROOT / ".gitignore").read_text()
    for entry in ("work/", "docs-corpus/.fingerprints", ".pixi/", "pixi.lock"):
        if entry not in text:
            fail(f".gitignore missing: {entry}")
            return False
    ok(".gitignore covers work/, docs-corpus/.fingerprints, .pixi/, pixi.lock")
    return True


# Test 16-18: README hygiene
def test_readme_no_machine_paths() -> bool:
    """The README must not contain machine-specific paths or AGENTS.md § refs."""
    text = (SKILL_ROOT / "README.md").read_text()
    bad = re.compile(r"/home/[^/\s]+|/Users/[^/\s]+|~\.pi|/mnt/|/scratch/|AGENTS\.md §")
    hits = bad.findall(text)
    if hits:
        fail(f"README.md contains machine-specific path: {hits[0]}")
        return False
    ok("README.md has no machine-specific paths")
    return True


def test_readme_no_unfilled_slots() -> bool:
    """The README must not contain unfilled [bracketed] slots or Jinja placeholders."""
    text = (SKILL_ROOT / "README.md").read_text()
    bad = re.compile(r"\[.*slot|\[Describe|\[One-paragraph|\[Write 3|\[role in the pipeline|\[artifact\]|\[phase goal\]|\{\{|\{%")
    hits = bad.findall(text)
    if hits:
        fail(f"README.md has unfilled slot: {hits[0]}")
        return False
    ok("README.md has no unfilled template slots")
    return True


def test_readme_required_sections() -> bool:
    """The README must contain the standard section set."""
    text = (SKILL_ROOT / "README.md").read_text()
    for section in ("## Contents", "## 🚀 Installation", "## 💡 Usage", "## 🔬 Pipeline overview", "## 🧰 Tools", "## 🔄 Update check", "## 📁 Repository layout", "## 🔒 Hard guarantees", "## Provenance", "## License"):
        if section not in text:
            fail(f"README.md missing section: {section}")
            return False
    ok("README.md has all 10 standard sections")
    return True


# Test 19-21: bin/skill-update-check.py + params.json + preflight.md
def test_update_check_parses() -> bool:
    import py_compile
    try:
        py_compile.compile(str(SKILL_ROOT / "bin" / "skill-update-check.py"), doraise=True)
    except py_compile.PyCompileError as e:
        fail(f"bin/skill-update-check.py does not parse: {e}")
        return False
    ok("bin/skill-update-check.py parses as Python")
    return True


def test_params_json_valid() -> bool:
    import json
    try:
        p = json.loads((SKILL_ROOT / "params.json").read_text())
    except Exception as e:
        fail(f"params.json does not parse: {e}")
        return False
    for field in ("skill_name", "skill_version", "tool_inventory", "verdict"):
        if field not in p:
            fail(f"params.json missing field: {field}")
            return False
    if p.get("verdict") not in ("GO", "GO-WITH-WARNINGS", "NO-GO"):
        fail(f"params.json verdict invalid: {p.get('verdict')}")
        return False
    ok(f"params.json valid, verdict={p.get('verdict')}")
    return True


def test_preflight_md_exists_with_verdict() -> bool:
    text = (SKILL_ROOT / "preflight.md").read_text()
    if "**GO**" not in text and "GO-WITH-WARNINGS" not in text:
        fail("preflight.md missing overall verdict (GO or GO-WITH-WARNINGS)")
        return False
    ok("preflight.md present with overall verdict GO/GO-WITH-WARNINGS")
    return True


# Test 22: handoff evidence chain
def test_evidence_chain() -> bool:
    """preflight.md + params.json + SKILL.md + 5 sub-skill SKILL.md files + bin/ + docs-corpus/ all present."""
    chain = [
        "preflight.md",
        "params.json",
        "SKILL.md",
        "bin/skill-update-check.py",
    ]
    for d, n in zip(SUB_SKILL_DIRS, SUB_SKILL_NAMES):
        chain.append(f"{d}/{n}/SKILL.md")
    for tool in EXPECTED_TOOLS:
        chain.append(f"docs-corpus/{tool}/README.md")
    missing = [c for c in chain if not (SKILL_ROOT / c).exists()]
    if missing:
        fail(f"evidence chain missing: {missing}")
        return False
    ok(f"evidence chain complete ({len(chain)} artifacts)")
    return True


ALL_TESTS = [
    test_skills_exist,
    test_sub_skill_dirs,
    test_bin_update_check,
    test_master_frontmatter,
    test_sub_skill_frontmatter,
    test_sub_skill_names,
    test_signature_library_present,
    test_ask_user_stop_points,
    test_io_contracts,
    test_docs_corpus_dirs,
    test_docs_corpus_no_machine_paths,
    test_docs_corpus_fingerprints,
    test_pixi_toml_channels,
    test_pixi_toml_tools,
    test_pixi_toml_tasks,
    test_gitignore,
    test_readme_no_machine_paths,
    test_readme_no_unfilled_slots,
    test_readme_required_sections,
    test_update_check_parses,
    test_params_json_valid,
    test_preflight_md_exists_with_verdict,
    test_evidence_chain,
]


def main() -> int:
    print(f"Running {len(ALL_TESTS)} structural smoke tests against {SKILL_ROOT}\n")
    failures = 0
    for t in ALL_TESTS:
        if not t():
            failures += 1
    print(f"\n{'-' * 60}")
    if failures == 0:
        print(f"PASS  {len(ALL_TESTS)}/{len(ALL_TESTS)} tests passed")
        return 0
    print(f"FAIL  {failures}/{len(ALL_TESTS)} tests failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
