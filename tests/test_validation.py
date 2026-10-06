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

def test_unique_keys():
    df = pd.DataFrame([
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 1, 
        "payment_installments": 1, 
        "payment_value": 100.0
        },
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 1, 
        "payment_installments": 1, 
        "payment_value": 100.0
        },
    ])
    result = Validate_Data().validate_table(df,"payments",VALIDATION_RULES)
    assert result["valid"] is False
    assert result["errors"]["duplicate_count"] is not 0
    assert result["failed_row_count"] == 2

def test_composite_key_behaviour():
    df = pd.DataFrame([
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 1, 
        "payment_installments": 1, 
        "payment_value": 100.0
        },
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 2, 
        "payment_installments": 1, 
        "payment_value": 100.0
        },
    ])
    result = Validate_Data().validate_table(df,"payments",VALIDATION_RULES)
    assert result["valid"] is True
    assert result["failed_row_count"] == 0

def test_minimum_values():
    df = pd.DataFrame([
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 1, 
        "payment_installments": 1, 
        "payment_value": -100.0 # negative value which is not allowed
        },
    ])
    result = Validate_Data().validate_table(df,"payments",VALIDATION_RULES)
    assert result["valid"] is False
    assert result["errors"]["minimum_violations"] is not 0
    assert result["failed_row_count"] == 1

def test_non_negative_values():
    df = pd.DataFrame([
        {
        "order_id": 1,
        "payment_type":"credit_card",
        "payment_sequential": 1, 
        "payment_installments": 1, 
        "payment_value": -100.0 # negative value which is not allowed
        },
    ])
    result = Validate_Data().validate_table(df,"payments",VALIDATION_RULES)
    assert result["valid"] is False
    assert result["errors"]["non_negative_counts"] is not 0
    assert result["failed_row_count"] == 1

