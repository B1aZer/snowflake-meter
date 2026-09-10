-- Billed seconds vs executed seconds per warehouse, last 6 days. XS rate: scale by warehouse size.
SELECT m.warehouse_name,
       SUM(m.credits_used_compute) * 3600            AS billed_seconds_xs_rate,
       SUM(q.execution_time) / 1000                  AS executed_seconds,
       billed_seconds_xs_rate / NULLIF(executed_seconds, 0) AS billed_per_executed
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(DATEADD('day', -6, CURRENT_TIMESTAMP()))) m
LEFT JOIN TABLE(INFORMATION_SCHEMA.QUERY_HISTORY_BY_WAREHOUSE(
       WAREHOUSE_NAME => m.warehouse_name,
       END_TIME_RANGE_START => DATEADD('day', -6, CURRENT_TIMESTAMP()), RESULT_LIMIT => 10000)) q
GROUP BY 1 ORDER BY 4 DESC;
