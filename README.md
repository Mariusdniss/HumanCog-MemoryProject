# Human Memory Mini Project — DTU 02464/02458

Free recall and serial recall experiments replicating the effects described
in Sections 1.5–1.6 of the course lecture notes (primacy/recency, capacity,
error types, chunking, articulatory suppression, finger tapping).

## Contents

- `experiment.html` — self-contained experiment runner (no install, no
  server). Open it in a browser to run either task and export a CSV of
  trial-level data.
- `analyze.py` — scores exported CSVs, pools trials across participants,
  and produces the plots and summary table used in the report.
- `report/report.tex` — LaTeX report skeleton (≤5 pages), matching the
  assignment's required sections.
- `requirements.txt` — Python dependencies for `analyze.py`.

## Running the experiment

1. Open `experiment.html` in any browser (double-click it, or `open
   experiment.html`). No installation needed.
2. Enter a participant ID and run **Free Recall** and **Serial Recall**
   (each takes 15–20 minutes). Each group member should run both, ideally
   after a short pilot run to check the instructions and timing feel right.
3. Click **Export CSV** when done. Repeat for every participant, giving
   each one a distinct participant ID.

## Design summary

**Free recall** (20 trials): 20-item letter lists (sampled from A–Z),
across four conditions — baseline (1 item/sec), fast (2 items/sec),
distractor (20s backward counting before recall), and delay (20s quiet
wait before recall). Scored by proportion recalled per serial position.

**Serial recall — Block A** (20 trials, capacity + error types): list
lengths 3–7, drawn from a phonologically confusable letter pool (B, C, D,
G, P, T, V — all rhyme with "-ee"). This maximizes sound-alike errors so
the error-type effect (confusing letters that sound alike, not letters
that look alike) actually shows up in the data.

**Serial recall — Block B** (24 trials, manipulations): 6-unit sequences
across four conditions — control (6 letters), chunked (6 three-letter
words, e.g. CAT DOG JOB — testing whether capacity is measured in chunks
rather than raw letters), articulatory suppression (say "the-the-the"
throughout), and finger tapping (as a dual-task control that should *not*
impair performance).

## Analyzing results

```bash
pip install -r requirements.txt
python analyze.py memory_experiment_*.csv
```

This pools every CSV passed in, scores each trial, and writes:

- `free_recall_serial_position.png` — accuracy by serial position, per condition
- `serial_recall_capacity.png` — accuracy by list length
- `serial_recall_errors.png` — transposition / intrusion / omission breakdown
- `serial_recall_manipulations.png` — accuracy by condition (control / chunked / suppression / tapping)
- `summary.csv` — all computed numbers, for pasting into report tables

## Report

`report/report.tex` compiles with `pdflatex` (or any standard LaTeX
toolchain). It's a skeleton with the required sections filled in with
placeholders — drop your own figures, numbers, and discussion in once
you've collected and analyzed real data.

```bash
cd report
pdflatex report.tex
pdflatex report.tex   # run twice for references/page numbers
```
