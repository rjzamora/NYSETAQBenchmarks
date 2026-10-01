# cudf-polars scan experiments

These helpers compare Polars CPU lazy scan and cudf-polars GPU scan on the same
pre-sorted Parquet input. The goal is to keep the setup simple enough that Q1 can
be debugged without also benchmarking the one-time load/sort step.

## Why Q1 Is Slow On The GPU

Once the input is pre-sorted and both engines use lazy Parquet scans, Q1 is no
longer dominated by sorting or ordering metadata. The useful checks so far are:

- CPU lazy scan on the large pre-sorted data is sub-second for Q1.
- GPU lazy scan is much slower when Q1 returns all quote columns.
- `set_sorted` versus no `set_sorted` does not materially change the GPU time.
- Rewriting `time` from `Duration(ns)` to `Int64` does not materially change the
  full Q1 GPU time.
- Count-only and narrow projections are much faster on the GPU.
- cudf-polars does not currently support Polars `Categorical` or `Enum` dtypes,
  so the GPU scan path reads those columns as strings.

The current working theory is that Q1 exposes a string/categorical gap: CPU
Polars can use categorical columns directly, while cudf-polars has to decode and
materialize string columns.

## Pre-sort a dataset

```bash
SIZE=large \
INPUT_ROOT=/datasets/btepera/kx_nyse/large/parquet/rowgroup \
OUTPUT_ROOT=/datasets/rzamora/nyse_large_sorted/parquet/rowgroup \
HIVE_DATE=2026-04-02 \
scripts/cudf_polars/presort_parquet.sh
```

This writes a rowgroup Parquet dataset with `trade` and `quote` sorted by
`time`. It also copies `master` and `exnames.parquet`.

## Run Q1

```bash
scripts/cudf_polars/run_scan_query.sh cpu 1 large
scripts/cudf_polars/run_scan_query.sh gpu 1 large
```

The runner still builds the benchmark's usual sort on `-sortcols time`; the
helper passes `-presorted time` first so Polars can remove that sort when the
input dataset is already sorted.

Results and logs are written under `results/cudf_polars/`, which is ignored by
git.

Use `DATA_ROOT=/path/to/parquet/rowgroup` to point at a different pre-sorted
dataset. The script defaults to `DATA_DATE=20260402`; override it if needed.
