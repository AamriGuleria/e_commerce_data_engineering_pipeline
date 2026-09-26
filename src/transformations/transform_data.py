from pathlib import Path
from logging import getLogger
from typing import Optional
from database.session_manager import db_manager
from sqlalchemy import inspect, select
from sqlalchemy.dialects.postgresql import insert
from models.analytics_schema import DimCustomer, DimProduct, DimSeller, FactOrderItems, DimDate
from models.raw_schema import Customers, Products, Seller
import pandas as pd

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

def _upsert_dimension_batch(session, records, target_model, col_mappings: Optional[dict]):
    try:
        if not records:
            return
        table_name = target_model.__table__
        pk_cols = [col.name for col in inspect(table_name).primary_key.columns]
        if col_mappings:
            data = [
                {
                    target_col: getattr(record, source_col)
                    for source_col, target_col in col_mappings.items()
                }
                for record in records
            ]
        else:
            data = records
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

def load_dimension_tables(model_name, batch_size=1000):
    try:
        with db_manager.sync_session_scope() as session:
            if model_name not in DIMENSION_CONFIG:
                raise ValueError(f"Model {model_name} is not configured for dimension loading.")
            target_model, mappings = DIMENSION_CONFIG[model_name]
            records = session.scalars(select(model_name)).yield_per(batch_size)
            batch = []
            batches=0
            for record in records:
                batch.append(record)
                if len(batch) == batch_size:
                    _upsert_dimension_batch(session, batch, target_model, mappings)
                    batches += 1
                    batch = []
            if batch:
                _upsert_dimension_batch(session, batch, target_model, mappings)
                batches += 1
        logger.info(f"Successfully loaded dimension table for model: {model_name.__name__} in {batches} batches.")
    except Exception as ex:
        logger.error(f"Failed to load dimension table {ex}")
        raise RuntimeError(f"Failed to load dimension tables: {ex}")

def build_dim_date():
    try:
        with db_manager.sync_session_scope() as session:
            df = pd.read_csv(DATASET_PATH)
            target_model = DimDate
            data = []
            for _, record in df.iterrows():
                purchase_timestamp = pd.to_datetime(record["order_purchase_timestamp"])
                purchase_date_key = purchase_timestamp.date()
                day_of_month = purchase_date_key.day()
                day_name = purchase_date_key.day_name()
                month_number = purchase_date_key.month()
                month_name = purchase_date_key.month_name()
                year = purchase_date_key.year()
                quarter = (purchase_date_key.month - 1) // 3 + 1
                data.append(
                    {
                        "full_date": purchase_date_key,
                        "day_of_month": day_of_month,
                        "day_name": day_name,
                        "month_number": month_number,
                        "month_name": month_name,
                        "quarter": quarter,
                        "year": year,
                    }
                )   
            if data:
                stmt = insert(target_model).values(data)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["full_date"]
                )
                session.execute(stmt)
    except Exception as ex:
        logger.error(f"Failed to load dimension table {ex}")
        raise RuntimeError(f"Failed to load dimension tables: {ex}")
def fact_order_table():
    try:
        with db_manager.sync_session_scope() as session:
            logger.info("Loading fact_order table...")
            df = pd.read_csv(DATASET_PATH)
            target_model = FactOrderItems
            data = []
            date_lookup = dict(
                session.query(DimDate.full_date, DimDate.date_id).all()
            )
            for _, record in df.iterrows():
                purchase_timestamp = pd.to_datetime(record["order_purchase_timestamp"])
                purchase_date_key = purchase_timestamp.date()
                purchase_date_id = date_lookup.get(purchase_date_key)
                if purchase_date_id is None:
                    raise ValueError(f"Missing dim_date row for {purchase_date_key}.")

                delivered_customer_date = record.get("order_delivered_customer_date")
                estimated_delivery_date = record.get("order_estimated_delivery_date")
                delivered_customer_dt = (
                    pd.to_datetime(delivered_customer_date) if pd.notna(delivered_customer_date) else pd.NaT
                )
                estimated_delivery_dt = (
                    pd.to_datetime(estimated_delivery_date) if pd.notna(estimated_delivery_date) else pd.NaT
                )

                delivery_days = None
                if pd.notna(delivered_customer_dt):
                    delivery_days = (delivered_customer_dt - purchase_timestamp).days

                delivered_late = None
                if pd.notna(delivered_customer_dt) and pd.notna(estimated_delivery_dt):
                    delivered_late = delivered_customer_dt > estimated_delivery_dt
                data.append(
                    {
                        "order_id": record["order_id"],
                        "order_item_id": record["order_item_id"],
                        "customer_id": record["customer_id"],
                        "product_id": record["product_id"],
                        "seller_id": record["seller_id"],
                        "purchase_date_id": purchase_date_id,
                        "order_status": record.get("order_status"),
                        "price": float(record["price"]),
                        "freight_value": float(record["freight_value"]),
                        "item_total": float(record["price"]) + float(record["freight_value"]),
                        "delivery_days": delivery_days,
                        "delivered_late": delivered_late,
                    }
                )
            if data:
                stmt = insert(target_model).values(data)
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_fact_order_items_order_item",
                    set_={
                        column: getattr(stmt.excluded, column)
                        for column in data[0]
                        if column not in {"order_id", "order_item_id"}
                    },
                )
                session.execute(stmt)
            logger.info("Successfully loaded fact_order table.")
    except Exception as ex:
        logger.error(f"Failed to load fact_order table: {ex}")
        raise RuntimeError(f"Failed to load fact_order table: {ex}")


if __name__ == "__main__":
    for model in DIMENSION_CONFIG:
        load_dimension_tables(model)
    build_dim_date()
    fact_order_table()


def main():
    for model in DIMENSION_CONFIG.keys():
        logger.info(f"Loading dimension table for model: {model.__name__}")
        load_dimension_tables(model)
    build_dim_date()
    fact_order_table()