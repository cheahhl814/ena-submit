# cat (CAT — Contig Annotation Tool) — docs-corpus index

## Sources

- `cli-reference.md` — primary, `--help` capture (populated when installed via `pixi install`)
- `github-readme.md` — secondary, https://github.com/MalteHerrmann/CAT
- `web-docs.md` — tertiary, CAT usage docs

## Quick flags

The skill invokes the nf-core `fasta_classify_catpack` subworkflow which wraps the CAT/BAT pack pipeline:

```
CAT contigs -c <contigs.fasta> -d <CAT_database/> -t <taxonomy/> -o <out_prefix>
CAT add_names -i <ORF2LCA.tsv> -o <out_prefix>.named.tsv -t <taxonomy/> --only_official
CAT summarise -c <contigs.fasta> -i <ORF2LCA.named.tsv> -o <out_prefix>.summary.txt
```

## Notes

- `CAT` (Contig Annotation Tool) classifies contigs and bins taxonomically by aggregating ORFs against a DIAMOND protein database, then voting per contig.
- The bioconda package name is `cat` (not `catpack` — the old name). The nf-core subworkflow `fasta_classify_catpack` invokes these commands.
- Database prep: `CAT prepare --fresh --download_dir <dir/>` (or use a pre-built database). The nf-core `catpack/download` and `catpack/prepare` modules handle this.
- Used in `mags`/`bins` mode to populate the `taxonomy` column of the genome metadata TSV.
