# coverm — docs-corpus index

## Sources

- `cli-reference.md` — primary, `--help` capture (populated when installed via `pixi install`)
- `github-readme.md` — secondary, https://github.com/wwood/CoverM
- `web-docs.md` — tertiary, CoverM wiki (https://github.com/wwood/CoverM/wiki)

## Quick flags

The skill invokes CoverM via the nf-core `coverm/contig` and `coverm/genome` modules:

```
# Per-contig coverage
coverm contigs --coupled <R1.fastq.gz> <R2.fastq.gz> \
    --reference <contigs.fasta> \
    --threads <N> \
    --output-file <coverage.tsv>

# Per-genome (MAG/bin) coverage
coverm genome --coupled <R1.fastq.gz> <R2.fastq.gz> \
    --genome-fasta-files <bin1.fasta> <bin2.fasta> ... \
    --threads <N> \
    --output-file <genome_coverage.tsv>
```

## Notes

- `coverm` computes read coverage of contigs / genomes using minimap2/bowtie2 as the aligner. Used in `mags`/`bins` mode to populate the `genome_coverage` column of the genome metadata TSV.
- The pipeline passes `--mapper minimap2` (default) or `--mapper bwa-mem`/`--mapper star` for short reads.
- Output columns: `Genome`, `Covered Bases`, `Covered Fraction`, `Mean Coverage`, ... (varies by `--methods` flag — `mean`, `count`, `covered_fraction`, `rpkm`, `tpm`).
- The `metagenomic_assemblies` mode does NOT use coverm (it doesn't need read coverage of MAGs).
