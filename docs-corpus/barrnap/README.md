# barrnap — docs-corpus index

## Sources

- `cli-reference.md` — primary, `--help` capture (populated when installed via `pixi install`)
- `github-readme.md` — secondary, https://github.com/tseemann/barrnap
- `web-docs.md` — tertiary, usage docs

## Quick flags

Flags the ena-submit skill actually invokes:

```
barrnap --quiet <fasta> > <gff>
# Optional: --kingdom bac|arc|mito,euk  --lencutoff 0.8  --reject 0.5
```

## Notes

- `barrnap` predicts ribosomal RNA (5S, 5.8S, 16S, 18S, 23S, 28S) by searching against HMM profiles from Rfam.
- Used by the nf-core/seqsubmit `genome_evaluation` subworkflow in `mags`/`bins` mode to detect rRNA in submitted genomes.
- Default e-value cutoffs are good for most bacterial genomes; the nf-core module pins `--lencutoff 0.8` and `--reject 0.5` for stricter detection.
- Output: BED/GFF on stdout (or to a file with `>`). The nf-core module writes to a per-fasta `.gff`.
