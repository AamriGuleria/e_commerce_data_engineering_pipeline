from datetime import datetime, timezone
from logging import getLogger
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.session_manager import db_manager
from models.audit_tables import PipelineRun, PipelineStatus, RawLoadAudit, ValidationAudit

logger = getLogger(__name__)


def _write_raw_data_load_audit(
    session: Session,
    table_name: str,
    source_row_count: int,
    rows_after_deduplication: int,
    inserted_row_count: int,
    skipped_row_count: int,
    failed_row_count: int,
    status: PipelineStatus,
    started_at: datetime,
    finished_at: Optional[datetime],
    error_message: Optional[str],
    source_file: str,
    pipeline_name: str,
) -> int:
    pipeline_entry = PipelineRun(
        pipeline_name=pipeline_name,
        status=status,
        source_file=source_file,
        started_at=started_at,
        finished_at=finished_at,
        error_message=error_message,
    )
    session.add(pipeline_entry)
    session.flush()

    raw_audit_entry = RawLoadAudit(
        run_id=pipeline_entry.run_id,
        table_name=table_name,
        source_row_count=source_row_count,
        rows_after_deduplication=rows_after_deduplication,
        inserted_row_count=inserted_row_count,
        skipped_row_count=skipped_row_count,
        failed_row_count=failed_row_count,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        error_message=error_message,
    )
    session.add(raw_audit_entry)
    session.flush()
    return pipeline_entry.run_id


def log_raw_data_load(
    table_name: str,
    source_row_count: int,
    rows_after_deduplication: int,
    inserted_row_count: int,
    skipped_row_count: int = 0,
    failed_row_count: int = 0,
    status: PipelineStatus = PipelineStatus.RUNNING,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    error_message: Optional[str] = None,
    source_file: str = "load_raw_data",
    pipeline_name: str = "Raw Data Load",
    session: Optional[Session] = None,
) -> int:
    started_at = started_at or datetime.now(timezone.utc)
    logger.info("Recording raw data load audit for %s.", table_name)

    try:
        if session is not None:
            return _write_raw_data_load_audit(
                session=session,
                table_name=table_name,
                source_row_count=source_row_count,
                rows_after_deduplication=rows_after_deduplication,
                inserted_row_count=inserted_row_count,
                skipped_row_count=skipped_row_count,
                failed_row_count=failed_row_count,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                error_message=error_message,
                source_file=source_file,
                pipeline_name=pipeline_name,
            )

        with db_manager.sync_session_scope() as session:
            run_id = _write_raw_data_load_audit(
                session=session,
                table_name=table_name,
                source_row_count=source_row_count,
                rows_after_deduplication=rows_after_deduplication,
                inserted_row_count=inserted_row_count,
                skipped_row_count=skipped_row_count,
                failed_row_count=failed_row_count,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                error_message=error_message,
                source_file=source_file,
                pipeline_name=pipeline_name,
            )

        logger.info("Raw data load audit recorded for %s (run_id=%s).", table_name, run_id)
        return run_id
    except Exception as e:
        logger.exception("Failed to record raw data load audit for %s: %s", table_name, e)
        raise



def log_validate_data(
    table_name: str,
    rule_name: str,
    severity: str,
    passed: bool,
    checked_row_count: int,
    failed_row_count: int,
    sample_invalid_rows: Optional[Any] = None,
    status: PipelineStatus = PipelineStatus.RUNNING,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
    error_message: Optional[str] = None,
    source_file: str = "initiate_validation",
    pipeline_name: str = "Validate Data",
) -> int:
    started_at = started_at or datetime.now(timezone.utc)
    logger.info("Recording validation audit for %s using rule %s.", table_name, rule_name)

    try:
        with db_manager.sync_session_scope() as session:
            pipeline_entry = PipelineRun(
                pipeline_name=pipeline_name,
                status=status,
                source_file=source_file,
                started_at=started_at,
                finished_at=finished_at,
                error_message=error_message,
            )
            session.add(pipeline_entry)
            session.flush()

            validation_audit_entry = ValidationAudit(
                run_id=pipeline_entry.run_id,
                table_name=table_name,
                rule_name=rule_name,
                severity=severity,
                passed=passed,
                checked_row_count=checked_row_count,
                failed_row_count=failed_row_count,
                sample_invalid_rows=sample_invalid_rows,
                validated_at=finished_at,
            )
            session.add(validation_audit_entry)
            session.flush()
            run_id = pipeline_entry.run_id

        logger.info("Validation audit recorded for %s (run_id=%s).", table_name, run_id)
        return run_id
    except Exception as e:
        logger.exception("Failed to record validation audit for %s: %s", table_name, e)
        raise