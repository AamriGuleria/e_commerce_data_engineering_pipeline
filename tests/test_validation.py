import pandas as pd

from validation.validate_data import Validate_Data
from validation.validation_rules import VALIDATION_RULES

# Tests for payments model
def test_check_required_column():
    df = pd.DataFrame([
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 1, 
        "payment_installments": 1, 
        # "payment_value": 100.0 # missing payment value which is mandatory column
        },
    ])
    result = Validate_Data().validate_table(df,"payments",VALIDATION_RULES)
    assert result["valid"] is False
    assert result["errors"]["missing_columns"] == ["payment_value"]
    assert result["failed_row_count"] == 1

def test_check_not_null():
    df = pd.DataFrame([
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 1, 
        "payment_installments": 1, 
        "payment_value": None # null value which is not allowed
        },
    ])
    result = Validate_Data().validate_table(df,"payments",VALIDATION_RULES)
    assert result["valid"] is False
    assert result["errors"]["null_counts"] is not 0
    assert result["failed_row_count"] == 1