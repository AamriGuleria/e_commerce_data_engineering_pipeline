from logging import getLogger
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from database.session_manager import db_manager
from models.raw_schema import Customers, Products, Seller
from models.analytics_schema import DimCustomer, DimDate, DimSeller, DimProduct, FactOrderItems
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


def _upsert_dimension_batch(session, dimension_model, rows):
    """Insert a dimension batch or update its non-key attributes on reruns."""
    if not rows:
        return

    statement = insert(dimension_model).values(rows)
    primary_key_columns = [column.name for column in dimension_model.__table__.primary_key.columns]
    if not primary_key_columns:
        raise ValueError(f"{dimension_model.__name__} does not define a primary key.")

    columns_to_update = {
        column.name: getattr(statement.excluded, column.name)
        for column in dimension_model.__table__.columns
        if column.name not in primary_key_columns
    }

    if columns_to_update:
        session.execute(
            statement.on_conflict_do_update(
                index_elements=primary_key_columns,
                set_=columns_to_update,
            )
        )
    else:
        session.execute(
            statement.on_conflict_do_nothing(
                index_elements=primary_key_columns,
            )
        )


def build_date_dimension_rows(timestamps):
    """Create dim_date rows with a generated surrogate key."""
    unique_dates = (
        pd.Series(pd.to_datetime(timestamps))
        .dt.normalize()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    rows = []
    for date_id, purchase_date in enumerate(unique_dates, start=1):
        date_value = purchase_date.date()
        rows.append(
            {
                "date_id": date_id,
                "full_date": date_value,
                "day_of_month": date_value.day,
                "day_name": date_value.strftime("%A"),
                "month_number": date_value.month,
                "month_name": date_value.strftime("%B"),
                "quarter": (date_value.month - 1) // 3 + 1,
                "year": date_value.year,
            }
        )
    return rows


def build_fact_order_rows(df, date_lookup):
    """Build fact-order rows using dim_date surrogate keys and normalized metrics."""
    rows = []
    for record in df.to_dict("records"):
        purchase_timestamp = pd.to_datetime(record["order_purchase_timestamp"])
        purchase_date_key = purchase_timestamp.date().isoformat()
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

        rows.append(
            {
                "order_id": record["order_id"],
                "order_item_id": record["order_item_id"],
                "customer_id": record["customer_id"],
                "product_id": record["product_id"],
                "seller_id": record["seller_id"],
                "purchase_date_id": int(purchase_date_id),
                "order_status": record.get("order_status"),
                "price": float(record["price"]),
                "freight_value": float(record["freight_value"]),
                "item_total": float(record["price"]) + float(record["freight_value"]),
                "delivery_days": delivery_days,
                "delivered_late": delivered_late,
            }
        )
    return rows


def load_dimensions(raw_model, batch_size=1_000):
    try:
        dimension_model, column_mapping = DIMENSION_CONFIG[raw_model]
    except KeyError as ex:
        supported_models = ", ".join(model.__name__ for model in DIMENSION_CONFIG)
        raise ValueError(
            f"{raw_model.__name__} is not a dimension source. "
            f"Supported models: {supported_models}."
        ) from ex

    loaded_row_count = 0
    with db_manager.sync_session_scope() as session:
        source_rows = (
            session.execute(select(raw_model))
            .scalars()
            .yield_per(batch_size)
        )
        batch = []

        for source_row in source_rows:
            batch.append(
                {
                    target_column: getattr(source_row, source_column)
                    for target_column, source_column in column_mapping.items()
                }
            )
            if len(batch) == batch_size:
                _upsert_dimension_batch(session, dimension_model, batch)
                loaded_row_count += len(batch)
                batch = []

        if batch:
            _upsert_dimension_batch(session, dimension_model, batch)
            loaded_row_count += len(batch)

    logger.info("Loaded %s rows into %s.", loaded_row_count, dimension_model.__tablename__)
    return loaded_row_count


def build_date_dimension():
    try:
        with db_manager.sync_session_scope() as session:
            existing_dates = session.execute(select(DimDate.date_id)).first()
            if existing_dates:
                logger.info("dim_date table already has data. Skipping date dimension build.")
                return

            df = pd.read_csv(DATASET_PATH, parse_dates=["order_purchase_timestamp"])
            date_rows = build_date_dimension_rows(df["order_purchase_timestamp"])

            _upsert_dimension_batch(session, DimDate, date_rows)
            logger.info("Inserted %s rows into dim_date.", len(date_rows))
    except Exception as ex:
        logger.error(f"Error Loading date dimension table {ex}")
        raise


def load_fact_order_items():
    try:
        with db_manager.sync_session_scope() as session:
            existing_records = session.execute(select(FactOrderItems.fact_order_item_id)).first()
            if existing_records:
                logger.info("FactOrderItems already has data. Skipping fact_order_items load.")
                return

            df = pd.read_csv(DATASET_PATH)
            if df.empty:
                logger.info("No order item data found in the source CSV.")
                return

            if not session.execute(select(DimDate.date_id)).first():
                date_rows = build_date_dimension_rows(df["order_purchase_timestamp"])
                _upsert_dimension_batch(session, DimDate, date_rows)

            date_lookup = {
                row.full_date.isoformat(): row.date_id
                for row in session.execute(select(DimDate.full_date, DimDate.date_id)).all()
            }
            records = build_fact_order_rows(df, date_lookup)
            _upsert_dimension_batch(session, FactOrderItems, records)
            logger.info("Inserted %s rows into fact_order_items.", len(records))
    except Exception as ex:
        logger.error(f"Error Loading fact_order_items table {ex}")
        raise
