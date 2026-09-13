from contextlib import asynccontextmanager, contextmanager
import logging
from typing import Optional
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.orm import Session, sessionmaker
from core.config import config

logger = logging.getLogger(__name__)

class SessionManager():
    def __init__(
        self,
        database_url: Optional[str] = None,
        async_database_url: Optional[str] = None,
        echo: bool = False,  # Log all SQL statements
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        # pool_use_lifo: bool = True,
    ):
        self.database_url = database_url
        self.async_database_url = async_database_url
        self.echo = echo
        
        # Pool configuration
        self.pool_config = {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": pool_pre_ping,
            # "pool_use_lifo": pool_use_lifo,
        }

        self.sync_engine: Optional[Engine] = None
        self.async_engine: Optional[AsyncEngine] = None
        self.sync_session_factory: Optional[sessionmaker] = None
        self.async_session_factory: Optional[async_sessionmaker] = None

    def _setup_sync_engine(self):
        if self.sync_engine is not None:
            return

        if not self.database_url:
            raise ValueError("database_url must be provided for sync operations")

        try:
            self.sync_engine = create_engine(
                self.database_url,
                echo=self.echo,
                connect_args={"application_name": "e_commerce_data_processing"},
                **self.pool_config
            )
            logger.info("Sync engine initialized successfully")
        except Exception as ex:
            logger.error(f"Error creating sync engine: {ex}")
            raise

    def _setup_async_engine(self):
        if self.async_engine is not None:
            return

        if not self.async_database_url:
            raise ValueError("Async database url must be provided")

        try:
            self.async_engine = create_async_engine(
                self.async_database_url,
                echo=self.echo,
                poolclass=AsyncAdaptedQueuePool,
                connect_args={"application_name": "e_commerce_data_processing"},
                **self.pool_config
            )
            logger.info("Async engine initialized successfully")
        except Exception as ex:
            logger.error("Error creating async session")
            raise


    def _setup_sync_session_factory(self):
        if self.sync_session_factory is not None:
            return

        self._setup_sync_engine()
        self.sync_session_factory = sessionmaker(
            self.sync_engine,
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        return self.sync_session_factory

    def _setup_async_session_factory(self):
        if self.async_session_factory is not None:
            return 
        self._setup_async_engine()
        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        return self.async_session_factory

    @contextmanager
    def sync_session_scope(self):
        session_factory = self._setup_sync_session_factory()
        session: Session = session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Sync session rolled back due to: {e}")
            raise
        finally:
            session.close()
            logger.debug("Sync session closed")

    @asynccontextmanager
    async def async_session_scope(self):
        session_factory = self._setup_async_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async session rolled back due to: {e}")
                raise
            finally:
                await session.close()
                logger.debug("Async session closed")


db_manager = SessionManager(
    database_url=config.database_url,
    async_database_url=config.async_database_url,
    echo=config.echo,
    pool_size=config.pool_size,
    max_overflow=config.max_overflow,
    pool_recycle=config.pool_recycle,
    pool_pre_ping=config.pool_pre_ping,
)

def get_db():
    with db_manager.sync_session_scope() as db:
        yield db

async def get_async_db():
    async with db_manager.async_session_scope() as db:
        yield db