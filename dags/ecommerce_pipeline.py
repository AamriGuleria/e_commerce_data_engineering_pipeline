from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task
from airflow.exceptions import AirflowException


@dag(
    dag_id="ecommerce_pipeline",
    start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    tags=["ecommerce", "etl"],
)
def ecommerce_pipeline():
    @task(retries=2, retry_delay=timedelta(minutes=1))
    def ingest_raw_data():
        from ingestion import load_raw_data

        load_raw_data.main()

    @task(retries=0)
    def validate_raw_data():
        from validation import initiate_validation

        if not initiate_validation.main():
            raise AirflowException(
                "Validation did not meet the required pass rate."
            )

    @task(retries=2, retry_delay=timedelta(minutes=1))
    def transform_analytics_data():
        from transformations import transform_data

        transform_data.main()

    ingestion = ingest_raw_data()
    validation = validate_raw_data()
    transformation = transform_analytics_data()

    ingestion >> validation >> transformation


ecommerce_pipeline()