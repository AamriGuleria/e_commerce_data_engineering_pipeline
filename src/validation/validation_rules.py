VALIDATION_RULES = {
    "products":{
        "required_columns":["product_id"],
        "unique_key":["product_id"],
        "not_null":["product_id"],
        "non_negative":[
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
            "product_photos_qty",
        ]
    },
    "payments":{
        "required_columns":["order_id", "payment_sequential"],
        "unique_key": ["order_id", "payment_sequential"],
        "not_null": ["order_id", "payment_sequential"],
        "non_negative": ["payment_value"],
        "minimum_value": {
            "payment_sequential": 1,
            "payment_installments": 1,
        },
    },
    "order_items":{
        "required_columns":["order_id", "order_item_id"],
        "unique_key": ["order_id", "order_item_id"],
        "not_null": ["order_id", "order_item_id","price"],
        "non_negative": ["freight_value","price"],
    },
    "orders":{
        "required_columns":["order_id"],
        "unique_key": ["order_id"],
        "not_null": ["order_id"],
    },
    "customers":{
        "required_columns":["customer_id"],
        "unique_key": ["customer_id","customer_unique_id"],
        "not_null": ["customer_id"],
    },
    "seller":{
        "required_columns":["seller_id"],
        "unique_key": ["seller_id"],
        "not_null": ["seller_id"],
    }
}