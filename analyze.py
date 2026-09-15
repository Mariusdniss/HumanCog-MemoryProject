"""
Analysis script for the free-recall / serial-recall memory experiment.

Usage:
    python analyze.py memory_experiment_P1_*.csv memory_experiment_P2_*.csv

Pools trials across all CSV files passed in (i.e. across participants),
scores each trial, and produces:

Note: serial-recall Block A stimuli are drawn entirely from a phonologically
confusable letter pool (B, C, D, G, P, T, V -- all rhyme with "-ee"), so
transposition/intrusion errors there are, by construction, letters that
sound like the target. This is what lets you speak to the lecture notes'
"type of errors" effect (participants confuse sound-alike letters like
F/S more than look-alike letters like F/E) without extra classification
logic -- just report the error rate and note the confusable-pool design
choice in your methods section.

Block B's 'chunked' condition uses three-letter words instead of single
letters, at the same number of units (6) as the other Block B conditions.
Compare pos_correct (or exact_correct) between 'control' and 'chunked' in
the manipulations plot/summary: similar values would replicate the slides'
point that capacity is measured in chunks, not raw letters, since each
chunked trial carries 3x the letter-level information of a control trial.

  - free_recall_serial_position.png   (accuracy by serial position, per condition)
  - serial_recall_capacity.png        (accuracy by list length)
  - serial_recall_errors.png          (transposition vs intrusion vs omission rate)
  - serial_recall_manipulations.png   (accuracy by condition: control/chunked/suppression/tapping)
  - summary.csv                       (all computed numbers, for your report tables)

Requires: pandas, numpy, matplotlib
    pip install pandas numpy matplotlib
"""
import sys
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def wilson_ci(k, n, z=1.96):
    """Wilson score interval for a binomial proportion. Returns (p, lo, hi)."""
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    half = (z * np.sqrt(p*(1-p)/n + z**2/(4*n**2))) / denom
    return p, max(0, center - half), min(1, center + half)

def load(paths):
    frames = [pd.read_csv(p) for p in paths]
    return pd.concat(frames, ignore_index=True)

# ---------- Free recall ----------
def score_free_recall(df):
    """Return long-form df: condition, serial_position, correct (0/1)."""
    rows = []
    fr = df[df.experiment == 'free_recall']
    for _, row in fr.iterrows():
        target = str(row['list']).split()
        resp = set(str(row['response']).upper().split())
        for pos, item in enumerate(target, start=1):
            rows.append({
                'condition': row['condition'],
                'serial_position': pos,
                'correct': int(item.upper() in resp)
            })
    return pd.DataFrame(rows)

def plot_free_recall(long_df, out='free_recall_serial_position.png'):
    conditions = long_df['condition'].unique()
    plt.figure(figsize=(7,5))
    for cond in conditions:
        sub = long_df[long_df.condition == cond]
        agg = sub.groupby('serial_position')['correct'].agg(['sum','count'])
        ps, los, his = [], [], []
        for _, r in agg.iterrows():
            p, lo, hi = wilson_ci(r['sum'], r['count'])
            ps.append(p); los.append(p-lo); his.append(hi-p)
        plt.errorbar(agg.index, ps, yerr=[los,his], marker='o', capsize=3, label=cond)
    plt.xlabel('Serial position')
    plt.ylabel('Proportion recalled')
    plt.ylim(0,1.05)
    plt.title('Free recall: accuracy by serial position and condition')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print(f'Saved {out}')

# ---------- Serial recall: capacity (block A) ----------
def score_serial_capacity(df):
    rows = []
    sr = df[(df.experiment=='serial_recall') & (df.block=='A_capacity')]
    for _, row in sr.iterrows():
        target = str(row['list'])
        resp = str(row['response']).strip()
        exact = int(resp == target)
        rows.append({'list_length': row['list_length'], 'exact_correct': exact})
    return pd.DataFrame(rows)

def plot_serial_capacity(cap_df, out='serial_recall_capacity.png'):
    agg = cap_df.groupby('list_length')['exact_correct'].agg(['sum','count'])
    ps, los, his = [], [], []
    for _, r in agg.iterrows():
        p, lo, hi = wilson_ci(r['sum'], r['count'])
        ps.append(p); los.append(p-lo); his.append(hi-p)
    plt.figure(figsize=(6,4.5))
    plt.errorbar(agg.index, ps, yerr=[los,his], marker='o', capsize=3, color='#3a5a40')
    plt.axhline(0.5, color='grey', linestyle='--', linewidth=1)
    plt.xlabel('List length (digits)')
    plt.ylabel('Proportion of trials fully correct')
    plt.ylim(0,1.05)
    plt.title('Serial recall: capacity curve')
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print(f'Saved {out}')

# ---------- Serial recall: error types (from block A trials) ----------
def score_error_types(df):
    """Classify each mismatched position as transposition, intrusion, or omission."""
    counts = {'transposition':0, 'intrusion':0, 'omission':0, 'correct':0}
    sr = df[(df.experiment=='serial_recall') & (df.block=='A_capacity')]
    for _, row in sr.iterrows():
        target = str(row['list'])
        resp = str(row['response']).strip()
        for i, t_item in enumerate(target):
            if i >= len(resp):
                counts['omission'] += 1
            elif resp[i] == t_item:
                counts['correct'] += 1
            elif resp[i] in target:
                counts['transposition'] += 1
            else:
                counts['intrusion'] += 1
    return counts

def plot_error_types(counts, out='serial_recall_errors.png'):
    labels = ['transposition','intrusion','omission']
    vals = [counts[l] for l in labels]
    total_errors = sum(vals)
    props = [v/total_errors if total_errors else 0 for v in vals]
    plt.figure(figsize=(5.5,4.5))
    plt.bar(labels, props, color=['#3a5a40','#8a4f3a','#6b6860'])
    plt.ylabel('Proportion of errors')
    plt.title('Serial recall: error type breakdown')
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print(f'Saved {out}  (counts: {counts})')

# ---------- Serial recall: manipulations (block B) ----------
def score_manipulations(df):
    """Block B stores space-separated tokens (single letters, or -- for the
    'chunked' condition -- three-letter words). Score token-by-token so a
    'chunk' (whole word) counts as one unit, matching the slides' point that
    capacity is measured in chunks, not letters."""
    rows = []
    sr = df[(df.experiment=='serial_recall') & (df.block=='B_manipulation')]
    for _, row in sr.iterrows():
        target = str(row['list']).split()
        resp = str(row['response']).strip().split()
        exact = int(resp == target)
        pos_correct = sum(1 for a,b in zip(target, resp) if a==b) / len(target)
        rows.append({'condition': row['condition'], 'exact_correct': exact, 'pos_correct': pos_correct, 'n_units': len(target)})
    return pd.DataFrame(rows)

def plot_manipulations(man_df, out='serial_recall_manipulations.png'):
    order = ['control','chunked','suppression','tapping']
    order = [c for c in order if c in man_df.condition.unique()]
    agg = man_df.groupby('condition')['pos_correct'].agg(['mean','count'])
    agg = agg.reindex(order)
    sems = man_df.groupby('condition')['pos_correct'].sem().reindex(order)
    plt.figure(figsize=(6.5,4.5))
    plt.bar(order, agg['mean'], yerr=sems, capsize=4, color='#3a5a40')
    plt.ylabel('Mean proportion of positions correct')
    plt.ylim(0,1.05)
    plt.title('Serial recall: effect of manipulations (fixed length)')
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print(f'Saved {out}')

def main():
    paths = []
    for arg in sys.argv[1:]:
        paths.extend(glob.glob(arg))
    if not paths:
        print('Usage: python analyze.py <csv files or glob patterns>')
        sys.exit(1)
    df = load(paths)
    print(f'Loaded {len(df)} trials from {len(paths)} file(s).')

    fr_long = score_free_recall(df)
    if not fr_long.empty:
        plot_free_recall(fr_long)

    cap_df = score_serial_capacity(df)
    if not cap_df.empty:
        plot_serial_capacity(cap_df)

    err_counts = score_error_types(df)
    plot_error_types(err_counts)

    man_df = score_manipulations(df)
    if not man_df.empty:
        plot_manipulations(man_df)

    # Dump a flat summary table for report tables
    summary_rows = []
    for cond, sub in fr_long.groupby('condition'):
        for pos, s2 in sub.groupby('serial_position'):
            p, lo, hi = wilson_ci(s2.correct.sum(), len(s2))
            summary_rows.append({'measure':'free_recall','condition':cond,'x':pos,'p':p,'ci_lo':lo,'ci_hi':hi,'n':len(s2)})
    for length, sub in cap_df.groupby('list_length'):
        p, lo, hi = wilson_ci(sub.exact_correct.sum(), len(sub))
        summary_rows.append({'measure':'serial_capacity','condition':None,'x':length,'p':p,'ci_lo':lo,'ci_hi':hi,'n':len(sub)})
    for cond, sub in man_df.groupby('condition'):
        summary_rows.append({'measure':'serial_manipulation','condition':cond,'x':None,'p':sub.pos_correct.mean(),'ci_lo':None,'ci_hi':None,'n':len(sub)})
    pd.DataFrame(summary_rows).to_csv('summary.csv', index=False)
    print('Saved summary.csv')

if __name__ == '__main__':
    main()
