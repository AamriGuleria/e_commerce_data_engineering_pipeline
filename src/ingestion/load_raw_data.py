import pandas as pd
import logging
from utils.helper import TABLE_TO_MODEL_MAPPING
from database import session_manager
logger = logging.getLogger(__name__)
def inspect_csv(
    file_path,
    # table_name,
    # schema
):
    df = pd.read_csv(file_path)
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
    file_path,
    table_name
):
    try:
        df = pd.read_csv(file_path)
        model = TABLE_TO_MODEL_MAPPING[table_name]
        model_cols = set(model.__table__.columns.keys())
        df = df[[col for col in df.columns if col in model_cols]]
        records = (
            df.astype(object)
            .where(pd.notna(df), None)
            .to_dict(orient="records")
        )
        with session_manager.db_manager.sync_session_scope() as session:
            session.bulk_insert_mappings(model, records)
    except Exception as ex:
        logger.error(f"Error loading csv data into postgres: \n {ex}")
        raise

if __name__ == "__main__":
    inspect_csv(r"dataset\Brazilian E-Commerce Public Dataset by Olist.csv")


# python -m src.ingestion.load_raw_data