"""
Ingestao dos Parquet do desafio RMI (GCS) para um dataset `raw` no BigQuery.

Os arquivos estao em um bucket GCS PUBLICO, sem extensao .parquet:
    gs://case_vagas/rmi/{aluno,escola,turma,avaliacao,frequencia}

O BigQuery carrega Parquet diretamente de gs:// (nao precisa baixar localmente).

Uso:
    export GCP_PROJECT=meu-projeto-sandbox
    python scripts/load_to_bigquery.py
    # ou:
    python scripts/load_to_bigquery.py --project meu-projeto --dataset rmi_raw --location US

Requisitos:
    pip install google-cloud-bigquery
    gcloud auth application-default login   (ou GOOGLE_APPLICATION_CREDENTIALS)
"""

from __future__ import annotations

import argparse
import os
import sys

from google.cloud import bigquery

BUCKET_URI = "gs://case_vagas/rmi"

# Nome do objeto no GCS -> nome da tabela no dataset raw
TABELAS = {
    "aluno": "aluno",
    "escola": "escola",
    "turma": "turma",
    "avaliacao": "avaliacao",
    "frequencia": "frequencia",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Carrega Parquet do GCS para o BigQuery (dataset raw).")
    p.add_argument("--project", default=os.environ.get("GCP_PROJECT"),
                   help="Project ID do GCP (ou env GCP_PROJECT).")
    p.add_argument("--dataset", default="rmi_raw", help="Dataset de destino (default: rmi_raw).")
    p.add_argument("--location", default="US", help="Location do dataset (default: US).")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.project:
        print("ERRO: informe --project ou defina a env var GCP_PROJECT.", file=sys.stderr)
        return 1

    client = bigquery.Client(project=args.project, location=args.location)

    dataset_id = f"{args.project}.{args.dataset}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = args.location
    client.create_dataset(dataset, exists_ok=True)
    print(f"[ok] dataset pronto: {dataset_id} ({args.location})")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    for objeto, tabela in TABELAS.items():
        uri = f"{BUCKET_URI}/{objeto}"
        destino = f"{dataset_id}.{tabela}"
        print(f"[..] carregando {uri} -> {destino}")
        load_job = client.load_table_from_uri(uri, destino, job_config=job_config)
        load_job.result()  # espera concluir
        tbl = client.get_table(destino)
        print(f"[ok] {tabela}: {tbl.num_rows:,} linhas, {len(tbl.schema)} colunas")

    print("\nConcluido. Ajuste `database`/`schema` da source em "
          "models/staging/educacao/_educacao__sources.yml se necessario.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
