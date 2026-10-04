# Counting inside large transcripts

Shell recipes for exact counts and distinct-session denominators over
transcript files pulled to disk. Read this before analysing transcripts, and
hand it to any analysis agent you fan out to.

```sh
grep -oh '"name":"[A-Za-z_]*"' raw/*.txt | sort | uniq -c | sort -rn
grep -c "<pattern>" raw/*.txt
grep -l "<pattern>" raw/*.txt | wc -l        # distinct sessions, the denominator
```

Prefer an exact literal over a regex with `.*`, which will match across a whole
line and inflate counts. Verify a suspicious zero with a second spelling before
reporting it as absence.

The first line is a tool-frequency table built from the recorded tool names,
which is the observation rather than the agent's prose. `grep -c` counts
matching lines per file; `grep -l ... | wc -l` counts the files, which is the
distinct-session denominator every claim should carry.
