# nf-core/seqsubmit — docs-corpus index

## Sources

- `github-readme.md` — local snapshot of the upstream README at v1.0.0
- `usage.md` — local snapshot of `docs/usage.md` (per-mode sample sheets, parameters)
- `output.md` — local snapshot of `docs/output.md` (per-mode output structure)
- `nextflow_schema.json` — local snapshot of the parameter schema (every --param the pipeline accepts)

## Modes (4 total)

| Mode | Workflow | Color (from upstream docs) | Typical use |
|---|---|---|---|
| `reads` | `READSUBMIT` | pink | Raw sequencing reads → ENA read submission |
| `metagenomic_assemblies` | `ASSEMBLYSUBMIT` | green | Pre-assembled contigs → ENA assembly submission |
| `mags` | `GENOMESUBMIT` | blue | Metagenome-assembled genomes (with QC: rRNA, tRNA, CheckM2, CAT, coverage) |
| `bins` | `GENOMESUBMIT` | blue | Bins from a co-assembly (same workflow as MAGs) |

## Quick flags (excerpt from nextflow_schema.json)

The full parameter list is in `nextflow_schema.json`. Key ones:

```
--mode              enum: reads|metagenomic_assemblies|mags|bins
--input             file (samplesheet.csv)
--outdir            string
--centre_name       string
--submission_study  string (study accession or path to study metadata file)
--study_metadata    file (alternative to --submission_study)
--upload_tpa        boolean (Third Party Annotation upload)
--test_upload       boolean (submit to ENA test server)
--webincli_mode     string (passes through to webin-cli --context)
--is_private        boolean (default true)
--release_date      string (ISO 8601)
--checkm2_db        string (path; required for mags/bins)
--checkm2_db_download_id string (Zenodo ID; alternative to --checkm2_db)
--cat_db            string (path; required for mags/bins)
--trna_limit        integer (default 400)
--rrna_limit        integer (default 400)
--multiqc_config    file
--multiqc_logo      file
--email             string (pipeline completion email)
--email_on_fail     string
```

## Notes

- The agent's `preflight` sub-skill validates the samplesheet column set against the chosen `--mode` (per `params.json: submission_modes` in this skill).
- The `build/seqsubmit-agent-runner` sub-skill invokes `nextflow run nf-core/seqsubmit -profile <X> --mode <X> --input <X> --outdir <X> --centre_name <X> --submission_study <X>`. It does NOT author a local DSL2 runner.
- The `qc/seqsubmit-agent-qc` sub-skill reads the per-mode output directory and aggregates accession receipts into `seqsubmit-report.md`.
