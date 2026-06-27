import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow")

from source.metadata_driven_transfos import MetadataDrivenTransfos


with DAG(
    "metadata_driven_transformations",
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="Execute metadata-driven data transformations",
    schedule=None,
    catchup=False,
    start_date=datetime(2026, 6, 27),
) as dag:
    run_transformations_task = PythonOperator(
        task_id="run_metadata_driven_transformations",
        python_callable=MetadataDrivenTransfos().entrypoint,
        op_kwargs={"metadata_filename": "metadata.json"},
    )
