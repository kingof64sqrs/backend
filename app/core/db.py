from __future__ import annotations

from collections.abc import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from sqlalchemy.schema import CreateColumn, CreateIndex

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine: AsyncEngine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    # Dev-friendly: create tables automatically.
    # For production, switch to Alembic migrations.
    from app.modules.places.model import Place  # noqa: F401
    from app.modules.posts.model import Post  # noqa: F401
    from app.modules.users.model import User  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)

        if settings.auto_schema_sync:
            await _auto_sync_schema(conn)


async def _auto_sync_schema(conn) -> None:
    """Add missing schema pieces in-place without dropping/changing existing data."""

    for table in Base.metadata.sorted_tables:
        existing_cols_result = await conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :table_name
                """
            ),
            {"table_name": table.name},
        )
        existing_cols = {row[0] for row in existing_cols_result.fetchall()}

        for column in table.columns:
            if column.name in existing_cols:
                continue

            # Safe additive policy: only auto-add nullable/defaulted columns.
            can_add_safely = column.nullable or column.server_default is not None or column.default is not None
            if not can_add_safely:
                logger.warning(
                    "Schema sync skipped non-null column without default: %s.%s",
                    table.name,
                    column.name,
                )
                continue

            column_sql = str(CreateColumn(column).compile(dialect=conn.dialect)).strip()
            await conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {column_sql}'))
            logger.info("Schema sync added column: %s.%s", table.name, column.name)

        existing_indexes_result = await conn.execute(
            text(
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public' AND tablename = :table_name
                """
            ),
            {"table_name": table.name},
        )
        existing_indexes = {row[0] for row in existing_indexes_result.fetchall()}

        for index in table.indexes:
            if not index.name or index.name in existing_indexes:
                continue

            create_index_sql = str(CreateIndex(index).compile(dialect=conn.dialect)).strip()
            if create_index_sql.startswith("CREATE UNIQUE INDEX "):
                create_index_sql = create_index_sql.replace(
                    "CREATE UNIQUE INDEX ", "CREATE UNIQUE INDEX IF NOT EXISTS ", 1
                )
            elif create_index_sql.startswith("CREATE INDEX "):
                create_index_sql = create_index_sql.replace(
                    "CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ", 1
                )

            await conn.execute(text(create_index_sql))
            logger.info("Schema sync added index: %s", index.name)
