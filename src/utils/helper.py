from models import Customers, Orders, Payments, Products, Seller

TABLE_TO_MODEL_MAPPING = {
    "customers": Customers,
    "products": Products,
    "sellers": Seller,
    "orders": Orders,
    "payments": Payments,
}