from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.database import engine


logger = logging.getLogger("dento.partitioning")


async def ensure_current_month_partition() -> None:
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                """
                SELECT 1
                FROM pg_partitioned_table pt
                JOIN pg_class c ON c.oid = pt.partrelid
                WHERE c.relname = 'sensor_data'
                """
            )
        )
        if result.first() is None:
            return

        month_info = await conn.execute(
            text(
                """
                SELECT
                    date_trunc('month', now())::date AS start_date,
                    (date_trunc('month', now()) + interval '1 month')::date AS end_date,
                    'sensor_data_' || to_char(date_trunc('month', now())::date, 'YYYY_MM') AS part_name
                """
            )
        )
        start_date, end_date, part_name = month_info.one()

        conflicting_rows = await conn.execute(
            text(
                """
                SELECT count(*)
                FROM ONLY sensor_data_default
                WHERE timestamp >= :start_date
                  AND timestamp < :end_date
                """
            ),
            {"start_date": start_date, "end_date": end_date},
        )
        conflict_count = conflicting_rows.scalar_one()

        existing_partition = await conn.execute(
            text(
                """
                SELECT 1
                FROM pg_class
                WHERE relname = :part_name
                """
            ),
            {"part_name": part_name},
        )

        if existing_partition.first() and not conflict_count:
            return

        try:
            if conflict_count:
                await conn.execute(
                    text(
                        """
                        CREATE TEMP TABLE sensor_data_partition_migrate
                        ON COMMIT DROP
                        AS
                        SELECT *
                        FROM ONLY sensor_data_default
                        WHERE timestamp >= :start_date
                          AND timestamp < :end_date
                        """
                    ),
                    {"start_date": start_date, "end_date": end_date},
                )

                await conn.execute(
                    text(
                        """
                        DELETE FROM ONLY sensor_data_default
                        WHERE timestamp >= :start_date
                          AND timestamp < :end_date
                        """
                    ),
                    {"start_date": start_date, "end_date": end_date},
                )

            await conn.execute(
                text(
                    """
                    DO $$
                    DECLARE
                        start_date date := date_trunc('month', now())::date;
                        end_date date := (date_trunc('month', now()) + interval '1 month')::date;
                        part_name text := 'sensor_data_' || to_char(start_date,'YYYY_MM');
                    BEGIN
                        EXECUTE format(
                            'CREATE TABLE IF NOT EXISTS %I PARTITION OF sensor_data FOR VALUES FROM (%L) TO (%L)',
                            part_name, start_date, end_date
                        );
                    END $$;
                    """
                )
            )

            if conflict_count:
                await conn.execute(
                    text(
                        """
                        INSERT INTO sensor_data
                        SELECT *
                        FROM sensor_data_partition_migrate
                        """
                    )
                )
                logger.info(
                    "default_partition_rows_migrated",
                    extra={
                        "partition_name": part_name,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "migrated_rows": conflict_count,
                    },
                )
        except IntegrityError:
            logger.exception(
                "partition_creation_failed",
                extra={
                    "partition_name": part_name,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "conflicting_rows": conflict_count,
                },
            )
