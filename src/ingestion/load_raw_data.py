import pandas as pd
import logging
from pathlib import Path
from models.audit_tables import PipelineStatus
from utils.audit_logger import log_raw_data_load
from utils.helper import TABLE_TO_MODEL_MAPPING
from database import session_manager
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

TABLE_DEDUPLICATION_KEYS = {
    "customers": ["customer_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "payments": ["order_id", "payment_sequential"],
}


def inspect_csv(df):
    print("Shape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())


def load_into_postgres(
    data,
    table_name,
    batch_size=1000,
):
    started_at = datetime.now(timezone.utc)
    df = None
    source_row_count = 0
    inserted_row_count = 0
    try:
        df = data if isinstance(data, pd.DataFrame) else pd.read_csv(data)
        source_row_count = len(df)
        model = TABLE_TO_MODEL_MAPPING[table_name]
        model_cols = set(model.__table__.columns.keys())
        df = df[[col for col in df.columns if col in model_cols]]

        deduplication_keys = TABLE_DEDUPLICATION_KEYS[table_name]
        missing_keys = [key for key in deduplication_keys if key not in df]
        if missing_keys:
            raise ValueError(
                f"Missing deduplication columns for {table_name}: {missing_keys}"
            )
        df = df.drop_duplicates(subset=deduplication_keys)
        with session_manager.db_manager.sync_session_scope() as session:
            for start in range(0, len(df), batch_size):
                batch = df.iloc[start:start + batch_size]
                records = (
                    batch.astype(object)
                    .where(pd.notna(batch), None)
                    .to_dict(orient="records")
                )
                session.bulk_insert_mappings(model, records)
                inserted_row_count += len(records)
                logger.info(
                    "Loaded %s rows into %s (%s/%s)",
                    len(records),
                    table_name,
                    min(start + batch_size, len(df)),
                    len(df),
                )
            finished_at = datetime.now(timezone.utc)
            log_raw_data_load(
                table_name=table_name,
                source_row_count=source_row_count,
                rows_after_deduplication=len(df),
                inserted_row_count=inserted_row_count,
                status=PipelineStatus.SUCCESS,
                started_at=started_at,
                finished_at=finished_at,
                session=session,
            )
    except Exception as ex:
        logger.error(f"Error loading csv data into postgres: \n {ex}")
        finished_at = datetime.now(timezone.utc)
        log_raw_data_load(
            table_name=table_name,
            source_row_count=source_row_count,
            rows_after_deduplication=len(df) if df is not None else 0,
            inserted_row_count=inserted_row_count,
            failed_row_count=(len(df) - inserted_row_count) if df is not None else 0,
            status=PipelineStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
            error_message=str(ex),
        )
        raise
def main():
    dataset_path = (
        Path(__file__).resolve().parents[2]
        / "dataset"
        / "Brazilian E-Commerce Public Dataset by Olist.csv"
    )
    raw_tables = ["customers", "products", "sellers", "orders", "payments","order_items"]
    source_data = pd.read_csv(dataset_path)
    inspect_csv(source_data)
    for raw_table in raw_tables:
        try:
            load_into_postgres(source_data, raw_table)
        except Exception as e:
            logger.error(f"Failed to load data into table {raw_table}: {e}")


if __name__ == "__main__":
    main()


# python -m src.ingestion.load_raw_data