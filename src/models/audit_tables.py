from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .Base import Base


class PipelineStatus(str, PyEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    run_id = Column(Integer, primary_key=True)
    pipeline_name = Column(String(100), nullable=False)
    source_file = Column(String(500), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        SqlEnum(PipelineStatus, name="pipeline_status"),
        nullable=False,
        default=PipelineStatus.RUNNING,
        server_default=text("'RUNNING'"),
    )
    error_message = Column(Text, nullable=True)
    raw_load_audits = relationship("RawLoadAudit", back_populates="run")
    validation_audits = relationship("ValidationAudit", back_populates="run")


class RawLoadAudit(Base):
    __tablename__ = "raw_load_audit"
    __table_args__ = (
        UniqueConstraint("run_id", "table_name", name="uq_raw_load_audit_run_table"),
    )

    audit_id = Column(Integer, primary_key=True)
    run_id = Column(
        Integer,
        ForeignKey("pipeline_runs.run_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    table_name = Column(String(100), nullable=False)
    source_row_count = Column(Integer, nullable=False, default=0)
    rows_after_deduplication = Column(Integer, nullable=False, default=0)
    inserted_row_count = Column(Integer, nullable=False, default=0)
    skipped_row_count = Column(Integer, nullable=False, default=0)
    failed_row_count = Column(Integer, nullable=False, default=0)
    status = Column(
        SqlEnum(PipelineStatus, name="pipeline_status"),
        nullable=False,
        default=PipelineStatus.RUNNING,
        server_default=text("'RUNNING'"),
    )
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    run = relationship("PipelineRun", back_populates="raw_load_audits")


class ValidationAudit(Base):
    __tablename__ = "validation_audit"
    __table_args__ = (
        UniqueConstraint(
            "run_id", "table_name", "rule_name", name="uq_validation_audit_run_table_rule"
        ),
    )
    audit_id = Column(Integer, primary_key=True)
    run_id = Column(
        Integer,
        ForeignKey("pipeline_runs.run_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    table_name = Column(String(100), nullable=False)
    rule_name = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False, default="ERROR")
    passed = Column(Boolean, nullable=False)
    checked_row_count = Column(Integer, nullable=False, default=0)
    failed_row_count = Column(Integer, nullable=False, default=0)
    sample_invalid_rows = Column(JSONB, nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    run = relationship("PipelineRun", back_populates="validation_audits")
    
