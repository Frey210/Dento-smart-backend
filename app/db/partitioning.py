from __future__ import annotations

from sqlalchemy import text

from app.db.database import engine


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
