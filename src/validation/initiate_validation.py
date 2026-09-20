from database.session_manager import db_manager
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import text
from models.audit_tables import PipelineStatus
from utils.audit_logger import log_validate_data
from .validate_data import Validate_Data
from .validation_rules import VALIDATION_RULES

MINIMUM_VALIDATION_RATE = 0.70


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
    results = validator.validate_all_tables(dataframes, VALIDATION_RULES)
    total_checked = 0
    total_failed = 0
    validated_at = datetime.now(timezone.utc)

    for table_name, table_result in results.items():
        checked_row_count = table_result["checked_row_count"]
        failed_row_count = table_result["failed_row_count"]
        pass_rate = table_result["pass_rate"]
        table_passed = pass_rate >= MINIMUM_VALIDATION_RATE
        total_checked += checked_row_count
        total_failed += failed_row_count

        log_validate_data(
            table_name=table_name,
            rule_name="table_validation",
            severity="ERROR" if not table_passed else "INFO",
            passed=table_passed,
            checked_row_count=checked_row_count,
            failed_row_count=failed_row_count,
            sample_invalid_rows=table_result["errors"],
            status=PipelineStatus.SUCCESS if table_passed else PipelineStatus.FAILED,
            started_at=validated_at,
            finished_at=validated_at,
        )

        print(
            f"\n{table_name}: "
            f"{'PASS' if table_passed else 'FAIL'} "
            f"({pass_rate:.1%} valid)"
        )
        print(table_result["errors"])

    overall_pass_rate = (
        (total_checked - total_failed) / total_checked
        if total_checked
        else 0.0
    )
    return overall_pass_rate >= MINIMUM_VALIDATION_RATE

if __name__ == "__main__":
    main()