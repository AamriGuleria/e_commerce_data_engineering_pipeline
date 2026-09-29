import logging
from datetime import datetime, timezone
from time import perf_counter
from database.session_manager import db_manager
from ingestion import load_raw_data
from models.audit_tables import PipelineRun, PipelineStatus
from validation import initiate_validation
from transformations import transform_data

logger = logging.getLogger(__name__)


def main():
    started_at = datetime.now(timezone.utc)
    start_clock = perf_counter()

    with db_manager.sync_session_scope() as session:
        pipeline_run = PipelineRun(
            pipeline_name="E-commerce ETL",
            source_file="dataset/Brazilian E-Commerce Public Dataset by Olist.csv",
            started_at=started_at,
            status=PipelineStatus.RUNNING,
        )
        session.add(pipeline_run)
        session.flush()
        run_id = pipeline_run.run_id

    try:
        load_raw_data.main()
        validation_passed = initiate_validation.main()
        if not validation_passed:
            raise RuntimeError(
                "Validation pass rate is below the 70% threshold; transformation stopped."
            )
        transform_data.main()
    except Exception as ex:
        finished_at = datetime.now(timezone.utc)
        duration_seconds = perf_counter() - start_clock
        try:
            with db_manager.sync_session_scope() as session:
                pipeline_run = session.get(PipelineRun, run_id)
                pipeline_run.status = PipelineStatus.FAILED
                pipeline_run.finished_at = finished_at
                pipeline_run.error_message = str(ex)
        except Exception:
            logger.exception("Could not record failed pipeline run %s", run_id)

        logger.exception(
            "Pipeline run %s failed after %.2f seconds", run_id, duration_seconds
        )
        raise

    finished_at = datetime.now(timezone.utc)
    duration_seconds = perf_counter() - start_clock
    with db_manager.sync_session_scope() as session:
        pipeline_run = session.get(PipelineRun, run_id)
        pipeline_run.status = PipelineStatus.SUCCESS
        pipeline_run.finished_at = finished_at

    logger.info(
        "Pipeline run %s completed successfully in %.2f seconds",
        run_id,
        duration_seconds,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()