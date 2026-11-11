#!/usr/bin/env bash
# Alternativa com `bq` (Google Cloud SDK) para carregar os Parquet do GCS.
# Uso: GCP_PROJECT=meu-projeto ./scripts/load_to_bigquery.sh
set -euo pipefail

: "${GCP_PROJECT:?Defina GCP_PROJECT}"
DATASET="${BQ_DATASET:-rmi_raw}"
LOCATION="${BQ_LOCATION:-US}"
BUCKET="gs://case_vagas/rmi"

bq --location="${LOCATION}" mk --dataset --force "${GCP_PROJECT}:${DATASET}"

for tbl in aluno escola turma avaliacao frequencia; do
  echo ">> carregando ${tbl}"
  bq load --source_format=PARQUET --replace \
    "${GCP_PROJECT}:${DATASET}.${tbl}" \
    "${BUCKET}/${tbl}"
done

echo "Concluido."
