# checkm2 — docs-corpus index

## Sources

- `cli-reference.md` — primary, `--help` capture (populated when installed via `pixi install`)
- `github-readme.md` — secondary, https://github.com/chklovski/CheckM2
- `web-docs.md` — tertiary, CheckM2 paper + docs

## Quick flags

`build/ena-submit-runner` invokes CheckM2 directly (no Nextflow/nf-core module involved), following the same command shape as the nf-core `checkm2/predict` module for reference:

```
checkm2 predict --threads <N> --input <bins_dir/*.fa> --output-directory <out_dir/>
```

Database setup (one-time, then reused):

```
checkm2 database --download
# or download a specific version:
checkm2 database --download --output <db_dir/>
```

## Notes

- CheckM2 is the deep-learning successor to CheckM1. It estimates completeness and contamination for MAGs/bins WITHOUT needing marker genes specific to a lineage — it's universal.
- The nf-core/seqsubmit pipeline takes `--checkm2_db` (path to the CheckM2 database directory) and `--checkm2_db_download_id` (Zenodo ID for download).
- Output: a `quality_report.tsv` with columns `Name`, `Completeness`, `Contamination`, `Genome_Size`, ... The nf-core module extracts these into the `completeness` and `contamination` columns of the genome metadata TSV.
- The `pixi.toml` in this skill pins a setuptools constraint if CheckM1 is also in the env (CheckM1's pkg_resources dependency is broken on setuptools >= 81).
