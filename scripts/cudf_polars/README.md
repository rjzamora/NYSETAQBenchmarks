# cudf-polars lazy-scan benchmark

These scripts run the Polars lazy queries directly against pre-sorted Parquet
data. They compare the CPU and GPU engines without including an initial
materialization or sort in the query time.

## Prepare the data

```bash
SIZE=large \
INPUT_ROOT=/datasets/btepera/kx_nyse/large/parquet/rowgroup \
OUTPUT_ROOT=/datasets/rzamora/nyse_large_sorted/parquet/rowgroup \
HIVE_DATE=2026-04-02 \
scripts/cudf_polars/presort_parquet.sh
```

This writes a rowgroup Parquet dataset with `trade` and `quote` sorted by
`time`. It also copies `master` and `exnames.parquet`.

## Run a query

```bash
scripts/cudf_polars/run_scan_query.sh cpu 1 large
scripts/cudf_polars/run_scan_query.sh gpu 1 large
```

The first argument selects the CPU or GPU engine. The second is the query index,
and the third is the dataset size. Use `all` instead of a query index to run the
full query set.

The runner uses the benchmark's lazy-scan mode and marks `time` as pre-sorted so
the query does not need to sort the input again.

## Configuration

The scripts accept these environment overrides:

- `DATA_ROOT`: Pre-sorted Parquet rowgroup root.
- `DATA_DATE`: Query date in `YYYYMMDD` form. Defaults to `20260402`.
- `PARAM_DIR`: Benchmark parameter directory.
- `QUERY_FILE`: Query definition file.
- `QUERY_META`: Query metadata file.
- `PRESORTED`: Columns already sorted in the input. Defaults to `time`.
- `RESULT_DIR`: Output directory.

Results and logs are written under `results/cudf_polars/`, which is ignored by
git.
