-- Dynamic-table refreshes that found nothing new; each one still resumed its warehouse.
SELECT name, COUNT(*) AS refreshes, SUM(IFF(refresh_action = 'NO_DATA', 1, 0)) AS empty_refreshes
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
GROUP BY 1 ORDER BY 3 DESC;
