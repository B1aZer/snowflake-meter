-- Billed seconds vs executed seconds per warehouse, last 6 days (INFORMATION_SCHEMA keeps 7).
-- Billed seconds assume X-Small (1 credit/hour); scale by warehouse size for larger ones.
-- On a busy account swap QUERY_HISTORY for SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY (no 10k-row cap, ~45 min lag).
WITH billed AS (
  SELECT warehouse_name, SUM(credits_used_compute) * 3600 AS billed_seconds
  FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('day', -6, CURRENT_TIMESTAMP())))
  GROUP BY 1),
executed AS (
  SELECT warehouse_name, SUM(execution_time) / 1000 AS executed_seconds
  FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
         END_TIME_RANGE_START => DATEADD('day', -6, CURRENT_TIMESTAMP()), RESULT_LIMIT => 10000))
  WHERE warehouse_name IS NOT NULL
  GROUP BY 1)
SELECT b.warehouse_name, b.billed_seconds, e.executed_seconds,
       b.billed_seconds / NULLIF(e.executed_seconds, 0) AS billed_per_executed
FROM billed b LEFT JOIN executed e USING (warehouse_name)
ORDER BY 4 DESC NULLS LAST;
