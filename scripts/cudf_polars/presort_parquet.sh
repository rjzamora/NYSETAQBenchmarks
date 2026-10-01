#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

SIZE="${SIZE:-large}"
HIVE_DATE="${HIVE_DATE:-2026-04-02}"
INPUT_ROOT="${INPUT_ROOT:-/datasets/btepera/kx_nyse/${SIZE}/parquet/rowgroup}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/datasets/rzamora/nyse_${SIZE}_sorted/parquet/rowgroup}"
SORTCOLS="${SORTCOLS:-time}"
ROW_GROUP_SIZE="${ROW_GROUP_SIZE:-1000000}"

cat <<EOF
input root     : ${INPUT_ROOT}
output root    : ${OUTPUT_ROOT}
hive date      : ${HIVE_DATE}
sort columns   : ${SORTCOLS}
row group size : ${ROW_GROUP_SIZE}
EOF

python -u scripts/cudf_polars/presort_parquet.py \
  --input-root "${INPUT_ROOT}" \
  --output-root "${OUTPUT_ROOT}" \
  --date "${HIVE_DATE}" \
  --sortcols "${SORTCOLS}" \
  --row-group-size "${ROW_GROUP_SIZE}"
