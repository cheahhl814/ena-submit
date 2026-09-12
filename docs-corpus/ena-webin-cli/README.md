# ena-webin-cli — docs-corpus index

## Sources

- `cli-reference.md` — primary, `--help` capture (authoritative for the pinned version; populated when the tool is installed via `pixi install`)
- `github-readme.md` — secondary, GitHub repo README (https://github.com/enasequence/ena_webin_cli)
- `web-docs.md` — tertiary, ENA docs portal (https://ena-docs.readthedocs.io/en/latest/submit/sra/programmatic.html)

## Quick flags

Flags the ena-submit skill actually invokes (see the `build/ena-submit-runner` sub-skill for context):

```
--context <reads|sequence|tsa|sequence_submit|tsa_embl|ena_run|ena_study|ena_sample|ena_experiment|ena_submission|ena_assembly|ena_genome|ena_mags>
--userName <Webin-XXX>
--password <...>
--centerName <centre>
--manifest <manifest.tsv>
--inputDir <dir/>
--outputDir <out/>
--test
--validate
```

## Notes

- `ena-webin-cli` is the umbrella CLI for ALL four submission modes (reads / metagenomic_assemblies / mags / bins). The context flag selects which submission type.
- Authentication: `--userName` (`Webin-XXX` format) and `--password`, read from the `ENA_WEBIN` / `ENA_WEBIN_PASSWORD` environment variables so credentials never appear on the command line.
- `build/ena-submit-runner` invokes `ena-webin-cli` directly (no Nextflow/nf-core involved) — it is the actual submission executor, not something wrapped by an upstream pipeline.
- For the test server, pass `--test` (SP1-gated default in `build/ena-submit-runner`; a production submission requires explicit user confirmation).
