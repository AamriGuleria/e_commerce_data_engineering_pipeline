from database.session_manager import SessionManager

from .validation_helper import (
    check_duplicates,
    check_minimum_value,
    check_non_negative,
    check_not_null,  
)
from sqlalchemy.ext.asyncio import AsyncSession
from database.session_manager import db_manager

class Validate_Data:
    def __init__(self, db: AsyncSession):
        self.db = db

    def validate_table(self, df , table_name , rules):
        table_rules = rules[table_name]
        result = {
            "table": table_name,
            "valid": True,
            "errors": {},
        }
        required_columns = table_rules.get("required_columns", [])
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            result["valid"] = False
            result["errors"]["missing_columns"] = missing_columns
            return result

        null_counts = check_not_null(
            df,
            table_rules.get("not_null", []),
        )
        duplicate_count = check_duplicates(
            df,
            table_rules.get("unique_key", []),
        )
        negative_counts = check_non_negative(
            df,
            table_rules.get("non_negative", []),
        )

        minimum_counts = check_minimum_value(
            df,
            table_rules.get("minimum_value", {}),
        )
        result["errors"]["null_counts"] = null_counts
        result["errors"]["duplicate_count"] = duplicate_count
        result["errors"]["negative_counts"] = negative_counts
        result["errors"]["minimum_violations"] = minimum_counts

        result["valid"]=(
            not any(null_counts.values())
            and duplicate_count == 0
            and not any(negative_counts.values())
            and not any(minimum_counts.values())
        )
        return result

    def validate_all_tables(self, dataframes, validation_rules):
        results = {}

        for table_name , df in dataframes.items():
            results[table_name] = self.validate_table(
                df,
                table_name,
                validation_rules
            )
        return results



