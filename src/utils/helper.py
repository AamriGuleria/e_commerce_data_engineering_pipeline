from models import Customers, Orders, Payments, Products, Seller, Order_Items

TABLE_TO_MODEL_MAPPING = {
    "customers": Customers,
    "products": Products,
    "sellers": Seller,
    "orders": Orders,
    "payments": Payments,
    "order_items":Order_Items
}