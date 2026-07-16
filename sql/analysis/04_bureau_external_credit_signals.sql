-- Count bureau credits per client (SK_ID_CURR) from bureau table, join to application,
-- bucket count into 0, 1-3, 4-7, 8+, find default rate per bucket

WITH full AS (
	WITH cre_cnt AS (
		SELECT SK_ID_CURR, COUNT(*) AS credit_count
		FROM bureau
		GROUP BY SK_ID_CURR
	)
	SELECT a.*, c.credit_count,
		CASE 
		    WHEN COALESCE(c.credit_count,0) = 0 THEN '0'
		    WHEN COALESCE(c.credit_count,0) BETWEEN 1 AND 3 THEN '1-3'
		    WHEN COALESCE(c.credit_count,0) BETWEEN 4 AND 7 THEN '4-7'
    		ELSE '8+'
		END AS buckets	
	FROM application AS a
	LEFT JOIN cre_cnt AS c
	ON a.SK_ID_CURR = c.SK_ID_CURR
)
SELECT buckets,
	ROUND((SUM(TARGET) * 100.0) / COUNT(*),2) AS default_pct
FROM full
GROUP BY buckets;

-- For each client, check if they have ANY bureau credit with CREDIT_ACTIVE = 'Active'
-- vs clients where all bureau credits are 'Closed', find default rate for each group

WITH client_status AS (
    SELECT SK_ID_CURR,
        CASE 
            WHEN SUM(CASE WHEN CREDIT_ACTIVE = 'Active' THEN 1 ELSE 0 END) > 0 THEN 'has_active'
            ELSE 'all_closed'
        END AS status
    FROM bureau
    GROUP BY SK_ID_CURR
)
SELECT c.status,
    COUNT(*) AS n_clients,
    ROUND(SUM(a.TARGET) * 100.0 / COUNT(*), 2) AS default_pct
FROM client_status c
JOIN application a ON c.SK_ID_CURR = a.SK_ID_CURR
GROUP BY c.status;

-- Default rate for clients with any bureau credit where CREDIT_DAY_OVERDUE > 0
-- vs clients with no overdue bureau credit

WITH client_overdue AS (
    SELECT SK_ID_CURR,
        CASE WHEN MAX(CREDIT_DAY_OVERDUE) > 0 THEN 'has_overdue' ELSE 'no_overdue' END AS status
    FROM bureau
    GROUP BY SK_ID_CURR
)
SELECT c.status,
    ROUND(SUM(a.TARGET) * 100.0 / COUNT(*), 2) AS default_pct
FROM client_overdue c
JOIN application a ON c.SK_ID_CURR = a.SK_ID_CURR
GROUP BY c.status;