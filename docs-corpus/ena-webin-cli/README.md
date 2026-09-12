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
- Authentication: `--userName` (`Webin-XXX` format) and `--password`. The skill wraps this in Nextflow secrets (`ENA_WEBIN`, `ENA_WEBIN_PASSWORD`) so they never appear on the command line.
- The nf-core/seqsubmit pipeline invokes `webin-cli` internally per mode; the agent never calls `ena-webin-cli` directly. It only validates the binary is on PATH and that the Webin secrets resolve.
- For the test server, prepend `--test` (or run the pipeline with `--test_upload true`).
