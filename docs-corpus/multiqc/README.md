# multiqc — docs-corpus index

## Sources

- `cli-reference.md` — primary, `--help` capture (populated when installed via `pixi install`)
- `github-readme.md` — secondary, https://github.com/MultiQC/MultiQC
- `web-docs.md` — tertiary, MultiQC docs (https://multiqc.info/)

## Quick flags

`qc/ena-submit-qc` invokes MultiQC directly (no Nextflow/nf-core module involved), following the same command shape as the nf-core `multiqc` module for reference:

```
multiqc --force <outdir/>
# --force: overwrite existing report
# -o <out>: write report to this directory
# -n <name>: report filename (default: multiqc_report.html)
```

## Notes

- `multiqc` aggregates QC outputs from 100+ bioinformatics tools into a single HTML report. The nf-core/seqsubmit pipeline emits a MultiQC report at `outdir/multiqc/multiqc_report.html`.
- The pipeline's `ch_multiqc_report` channel collects tool outputs and feeds them to MultiQC at the end of each workflow.
- Custom config: the pipeline accepts `--multiqc_config` (a custom MultiQC YAML) and `--multiqc_logo` (a custom logo PNG). Defaults are the nf-core/seqsubmit logo + a base config that recognises every tool in the pipeline.
