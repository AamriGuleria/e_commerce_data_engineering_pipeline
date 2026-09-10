from sqlalchemy import ARRAY, JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from models.Base import Base


# customers , products , orders , payments


# order_id,order_item_id,customer_id,customer_unique_id,
# customer_zip_code_prefix,customer_city,customer_state,product_id,
# product_category_name,product_name_lenght,product_description_lenght,
# product_photos_qty,product_weight_g,product_length_cm,product_height_cm,
# product_width_cm,seller_id,seller_city,seller_state,seller_zip_code_prefix,
# payment_type,payment_sequential,payment_installments,price,freight_value,payment_value,
# shipping_limit_date,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,
# order_delivered_customer_date,order_estimated_delivery_date,day_of_purchase,month_of_purchase,
# year_of_purchase,month/year_of_purchase,order_status,order_unique_id

class Orders(Base):
    __tablename__ = "orders"
    order_id = Column(String, primary_key=True)
    order_item_id = Column(Integer)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    product_id = Column(String, ForeignKey("products.product_id"))
    seller_id = Column(String, ForeignKey("sellers.seller_id"))
    price = Column(Float)
    freight_value = Column(Float)
    order_status = Column(String)
class Customers(Base):
    __tablename__ = "customers"
    customer_id = Column(String, primary_key=True)
    customer_unique_id = Column(String, unique=True)
    customer_zip_code_prefix = Column(String)
    customer_city = Column(String)
    customer_state = Column(String)
class Products(Base):
    __tablename__ = "products"
    product_id = Column(String, primary_key=True)
    product_category_name = Column(String)
    product_name_lenght = Column(Float)
    product_description_lenght = Column(Float)
    product_photos_qty = Column(Integer)
    product_weight_g = Column(Float)
    product_length_cm = Column(Float)
    product_height_cm = Column(Float)
    product_width_cm = Column(Float)
class Seller(Base):
    __tablename__ = "sellers"
    seller_id = Column(String, primary_key=True)
    seller_city = Column(String)
    seller_state = Column(String)
    seller_zip_code_prefix = Column(String)

class Payments(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.order_id"))
    payment_type = Column(String)
    payment_sequential = Column(Integer)
    payment_installments = Column(Integer)
    payment_value = Column(Float)