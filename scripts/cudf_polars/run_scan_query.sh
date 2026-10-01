#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/cudf_polars/run_scan_query.sh cpu|gpu [query-idx] [size]

Examples:
  scripts/cudf_polars/run_scan_query.sh cpu 1 large
  scripts/cudf_polars/run_scan_query.sh gpu 1 large
  scripts/cudf_polars/run_scan_query.sh cpu all small

Environment overrides:
  DATA_ROOT    Pre-sorted parquet rowgroup root
  DATA_DATE    Query date in YYYYMMDD form; defaults to 20260402
  PARAM_DIR    Parameter directory
  RESULT_DIR   Output directory for results.psv and run.out
  FLUSH        Cache flush helper; defaults to flush/noflush.sh
EOF
}

MODE="${1:-}"
IDX="${2:-1}"
SIZE="${3:-large}"
IDX_ARGS=()
IDX_LABEL="${IDX}"

if [[ "${MODE}" != "cpu" && "${MODE}" != "gpu" ]]; then
  usage
  exit 1
fi

if [[ "${IDX}" == "all" ]]; then
  IDX_LABEL="all"
else
  IDX_ARGS=(-idx "${IDX}")
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

EXTRA_ARGS=()
GPU_LABEL=""
if [[ "${MODE}" == "gpu" ]]; then
  EXTRA_ARGS=(--gpu)
  GPU_LABEL=" --gpu"
fi

DATA_ROOT="${DATA_ROOT:-/datasets/rzamora/nyse_${SIZE}_sorted/parquet/rowgroup}"
DATA_DATE="${DATA_DATE:-20260402}"
DATA_DATE="${DATA_DATE//-/}"
PARAM_DIR="${PARAM_DIR:-${REPO_ROOT}/artifacts/parameters/${SIZE}}"
QUERY_FILE="${QUERY_FILE:-${REPO_ROOT}/artifacts/queries/inmemory/polars_lazy.psv}"
QUERY_META="${QUERY_META:-${REPO_ROOT}/artifacts/queries/inmemory/querymeta.psv}"
PRESORTED="${PRESORTED:-time}"
RESULT_DIR="${RESULT_DIR:-${REPO_ROOT}/results/cudf_polars/q${IDX_LABEL}-${SIZE}-${MODE}-scan}"
RESULT_FILE="${RESULT_FILE:-${RESULT_DIR}/results.psv}"
LOG_FILE="${LOG_FILE:-${RESULT_DIR}/run.out}"
export FLUSH="${FLUSH:-${REPO_ROOT}/flush/noflush.sh}"

mkdir -p "${RESULT_DIR}"

cat <<EOF
mode       : ${MODE} (lazy-scan${GPU_LABEL})
query idx  : ${IDX}
data root  : ${DATA_ROOT}
date       : ${DATA_DATE}
param dir  : ${PARAM_DIR}
result psv : ${RESULT_FILE}
log file   : ${LOG_FILE}
presorted  : ${PRESORTED}
EOF

python -u pysrc/queryrunner/main.py \
  -date "${DATA_DATE}" \
  -storage_backend memory \
  -querymeta "${QUERY_META}" \
  -paramdir "${PARAM_DIR}" \
  "${IDX_ARGS[@]}" \
  -db "${DATA_ROOT}" \
  -engine polars \
  -mode lazy-scan \
  "${EXTRA_ARGS[@]}" \
  -sortcols time \
  -presorted "${PRESORTED}" \
  -queryfile "${QUERY_FILE}" \
  -result "${RESULT_FILE}" \
  2>&1 | tee "${LOG_FILE}"
