from logging import getLogger

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from database.session_manager import db_manager
from models.raw_schema import Customers, Products, Seller
from models.analytics_schema import DimCustomer, DimSeller, DimProduct

logger = getLogger(__name__)

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
    statement = insert(dimension_model).values(rows)
    primary_key_columns = [column.name for column in dimension_model.__table__.primary_key]
    columns_to_update = {
        column.name: getattr(statement.excluded, column.name)
        for column in dimension_model.__table__.columns
        if column.name not in primary_key_columns
    }
    session.execute(
        statement.on_conflict_do_update(
            index_elements=primary_key_columns,
            set_=columns_to_update,
        )
    )


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
    pass

def load_fact_order_items():
    pass
