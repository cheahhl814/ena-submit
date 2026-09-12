# trnascan-se — docs-corpus index

## Sources

- `cli-reference.md` — primary, `--help` capture (populated when installed via `pixi install`)
- `github-readme.md` — secondary, https://github.com/UCSC-LoweLab/tRNAscan-SE
- `web-docs.md` — tertiary, tRNAscan-SE docs (http://lowelab.ucsc.edu/tRNAscan-SE/)

## Quick flags

`build/ena-submit-runner` invokes tRNAscan-SE directly (no Nextflow/nf-core module involved), following the same command shape as the nf-core `trnascanse` module for reference:

```
tRNAscan-SE -B -Q <fasta> -o <out.gff> -m <out.stats>
# -B: bacterial
# -Q: quiet
# -m: emit statistics file
```

## Notes

- `tRNAscan-SE` detects tRNA genes in genomic DNA using a covariance model + heuristic filtering.
- Used by the nf-core/seqsubmit `genome_evaluation` subworkflow in `mags`/`bins` mode. The pipeline takes `--trna_limit` (max number of tRNAs per genome, default 400).
- Source mode `-B` is for bacterial genomes (the most common case in MAG submission). For eukaryotes use `-E` or omit for the default.
- The nf-core module writes the GFF + statistics to the per-fasta `*_trnascanse/` directory.
