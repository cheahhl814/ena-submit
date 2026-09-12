# nextflow — docs-corpus index

## Sources

- `cli-reference.md` — primary, `nextflow -h` capture (populated when installed)
- `github-readme.md` — secondary, https://github.com/nextflow-io/nextflow
- `web-docs.md` — tertiary, Nextflow docs (https://www.nextflow.io/docs/latest/)

## Quick flags

The skill invokes the upstream nf-core/seqsubmit pipeline via `nextflow run`:

```
nextflow run nf-core/seqsubmit \
    -profile <docker|singularity|podman|conda|test> \
    --mode <reads|metagenomic_assemblies|mags|bins> \
    --input <samplesheet.csv> \
    --centre_name <your_centre> \
    --submission_study <study_or_file> \
    --outdir <outdir>
```

## Notes

- `nextflow` is the orchestrator DSL for the pipeline. The ena-submit skill does NOT author a local DSL2 runner — it wraps the upstream nf-core/seqsubmit pipeline as an external executor.
- Required version: `>=25.04.0` per the upstream `nextflow.config`. nf-core/seqsubmit 1.0.0 was developed against Nextflow 25.10.4.
- Install: `curl -s https://get.nextflow.io | bash && mv nextflow /usr/local/bin/` (NOT a conda package in the standard channels — install outside the pixi env; the `pixi.toml` lists it as a system prerequisite).
- Secrets: `nextflow secrets set ENA_WEBIN "Webin-XXX"` and `nextflow secrets set ENA_WEBIN_PASSWORD "..."`. The agent's preflight sub-skill verifies these are set before invoking the run.
