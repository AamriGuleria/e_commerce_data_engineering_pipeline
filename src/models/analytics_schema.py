from .Base import Base
from sqlalchemy import Boolean, Column, Date, ForeignKey, Numeric, String, Float, Integer, UniqueConstraint

class DimCustomer(Base):
    __tablename__="dim_customer"
    customer_id = Column(String, primary_key=True)
    customer_unique_id = Column(String)
    customer_zip_code_prefix = Column(String)
    customer_city = Column(String)
    customer_state = Column(String)

class DimProduct(Base):
    __tablename__="dim_product"
    product_id = Column(String, primary_key=True)
    product_category_name = Column(String)
    product_name_length = Column(Float)
    product_description_length = Column(Float)
    product_photos_qty = Column(Integer)
    product_weight_g = Column(Float)
    product_length_cm = Column(Float)
    product_height_cm = Column(Float)
    product_width_cm = Column(Float)

class DimSeller(Base):
    __tablename__="dim_seller"
    seller_id = Column(String, primary_key=True)
    seller_city = Column(String)
    seller_state = Column(String)
    seller_zip_code_prefix = Column(String)

class DimDate(Base):
    __tablename__ = "dim_date"
    date_id = Column(Integer, primary_key=True)  
    full_date = Column(Date, unique=True, nullable=False)
    day_of_month = Column(Integer, nullable=False)
    day_name = Column(String, nullable=False)
    month_number = Column(Integer, nullable=False)
    month_name = Column(String, nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

class FactOrderItems(Base):
    __tablename__ = "fact_order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "order_item_id",
                         name="uq_fact_order_items_order_item"),
    )
    fact_order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, nullable=False, index=True)
    order_item_id = Column(Integer, nullable=False)
    
    customer_id = Column(String, ForeignKey("dim_customer.customer_id"), nullable=False,index=True)
    product_id = Column(String, ForeignKey("dim_product.product_id"), nullable=False,index=True)
    seller_id = Column(String, ForeignKey("dim_seller.seller_id"), nullable=False,index=True)
    purchase_date_id = Column(Integer, ForeignKey("dim_date.date_id"), nullable=False,index=True)

    order_status = Column(String)
    price = Column(Numeric(12, 2), nullable=False)
    freight_value = Column(Numeric(12, 2), nullable=False)
    item_total = Column(Numeric(12, 2), nullable=False)
    delivery_days = Column(Integer)
    delivered_late = Column(Boolean)