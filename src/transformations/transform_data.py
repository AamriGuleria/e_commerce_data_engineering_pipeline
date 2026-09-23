from pathlib import Path
from logging import getLogger
from database.session_manager import db_manager
from sqlalchemy import insert, inspect, select
from models.analytics_schema import DimCustomer, DimProduct, DimSeller
from models.raw_schema import Customers, Products, Seller

logger = getLogger(__name__)
DATASET_PATH = (
        Path(__file__).resolve().parents[2]
        / "dataset"
        / "Brazilian E-Commerce Public Dataset by Olist.csv"
    )
DIMENSION_CONFIG = {
    Customers: (
        DimCustomer,
        {
            "customer_id": "customer_id",
            "customer_unique_id": "customer_unique_id",
            "customer_zip_code_prefix": "customer_zip_code_prefix",
            "customer_city": "customer_city",
            "customer_state": "customer_state",
        },
    ),
    Products: (
        DimProduct,
        {
            "product_id": "product_id",
            "product_category_name": "product_category_name",
            "product_name_length": "product_name_lenght",
            "product_description_length": "product_description_lenght",
            "product_photos_qty": "product_photos_qty",
            "product_weight_g": "product_weight_g",
            "product_length_cm": "product_length_cm",
            "product_height_cm": "product_height_cm",
            "product_width_cm": "product_width_cm",
        },
    ),
    Seller: (
        DimSeller,
        {
            "seller_id": "seller_id",
            "seller_city": "seller_city",
            "seller_state": "seller_state",
            "seller_zip_code_prefix": "seller_zip_code_prefix",
        },
    ),
}

def _upsert_dimension_batch(session, records, target_model, col_mappings):
    try:
        if not records:
            return
        data = [
            {
                target_col: getattr(record, source_col)
                for source_col, target_col in col_mappings.items()
            }
            for record in records
        ]
        table_name = target_model.__table__
        pk_cols = [col.name for col in inspect(table_name).primary_key.columns]
        stmt = insert(target_model).values(data)
        stmt = stmt.on_conflict_do_update(
            index_elements = pk_cols,
            set_={
                col: stmt.excluded[col]
                for col in data[0].keys()
                if col not in pk_cols
            }
        )
        session.execute(stmt)
        session.commit()
    except Exception as ex:
        logger.error(f"Failed to upsert dimension batch: {ex}")
        raise RuntimeError(f"Failed to upsert dimension batch: {ex}")

def load_dimension_tables(model_name):
    try:
        with db_manager.sync_session_scope() as session:
            if model_name not in DIMENSION_CONFIG:
                raise ValueError(f"Model {model_name} is not configured for dimension loading.")
            target_model, mappings = DIMENSION_CONFIG[model_name]
            records = session.execute(select(model_name).scalars().yield_per(1000))
            batches=0
            for record in records:
                logger.info(f"Loading record: {record}")
                _upsert_dimension_batch(session, record, target_model, mappings)
                batch+=1
    except Exception as ex:
        logger.error(f"Failed to load dimension table {ex}")
        raise RuntimeError(f"Failed to load dimension tables: {ex}")