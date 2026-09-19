from database.session_manager import db_manager
import pandas as pd
from sqlalchemy import text
from .validate_data import Validate_Data
from .validation_rules import VALIDATION_RULES

def main():
    with db_manager.sync_session_scope() as session:
        dataframes = {
            table_name: pd.read_sql(
                text(f"SELECT * FROM {table_name}"),
                session.connection(),
            )
            for table_name in VALIDATION_RULES
        }

    validator = Validate_Data()
    result = validator.validate_all_tables(dataframes,VALIDATION_RULES)
    for table_name, result in result.items():
        print(f"\n{table_name}: {'PASS' if result['valid'] else 'FAIL'}")
        print(result["errors"])

if __name__ == "__main__":
    main()