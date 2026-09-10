from sqlalchemy import ARRAY, JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
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
    __tablename__="orders"
    id = Column(Integer,primary_key=True)
    order_id = Column(Integer,unique=True)
    order_item_id = Column(Integer)
    customer_id = Column(Integer,ForeignKey("customers.id"))
    product_id = Column(Integer,ForeignKey("products.id"))
    seller_id = Column(Integer,ForeignKey("sellers.id"))
    payment_id = Column(Integer,ForeignKey("payments.id"))
    price = Column(Float)
    freight_value = Column(Float)
    shipping_limit_date = Column(DateTime)
    order_purchase_timestamp = Column(DateTime)
    order_approved_at = Column(DateTime)
    order_delivered_carrier_date = Column(DateTime)
    order_delivered_customer_date = Column(DateTime)
    order_estimated_delivery_date = Column(DateTime)
    day_of_purchase = Column(Integer)
    month_of_purchase = Column(Integer)
    year_of_purchase = Column(Integer)
    month_year_of_purchase = Column(String(100))
    order_status = Column(String(100))

class Customers(Base):
    __tablename__="customers"
    id = Column(Integer,primary_key=True)
    customer_unique_id = Column(Integer,unique=True)
    customer_zip_code_prefix = Column(String(100))
    customer_city = Column(String(100))
    customer_state = Column(String(100))

class Products(Base):
    __tablename__="products"
    id = Column(Integer,primary_key=True)
    product_category_name = Column(String(100))
    product_name_lenght = Column(Integer)
    product_description_lenght = Column(Integer)
    product_photos_qty = Column(Integer)
    product_weight_g = Column(Float)
    product_length_cm = Column(Float)
    product_height_cm = Column(Float)
    product_width_cm = Column(Float)

class Seller(Base):
    __tablename__="sellers"
    id = Column(Integer,primary_key=True)
    seller_city = Column(String(100))
    seller_state = Column(String(100))
    seller_zip_code_prefix = Column(String(100))


class Payments(Base):
    __tablename__="payments"
    id = Column(Integer,primary_key=True)
    payment_type = Column(String(100))
    payment_sequential = Column(Integer)
    payment_installments = Column(Integer)
    payment_value = Column(Float)