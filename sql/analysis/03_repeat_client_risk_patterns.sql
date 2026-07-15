-- Count prior applications per client (SK_ID_CURR) from previous_application,
-- join to application, bucket count into 0, 1-2, 3-5, 6+, find default rate per bucket

WITH cnt_applications AS(
	SELECT SK_ID_CURR, COUNT(*) AS total_applications
	FROM previous_application
	GROUP BY SK_ID_CURR
)
SELECT
	CASE 
		WHEN COALESCE(c.total_applications, 0) = 0 THEN 'zero'
        WHEN c.total_applications <= 2 THEN '1_to_2'
        WHEN c.total_applications <= 5 THEN '3_to_5'
        ELSE 'above_6'
	END AS applications_bucket,	
	ROUND((100 * SUM(a.TARGET)) / COUNT(*),2) AS default_pct
FROM application AS a
LEFT JOIN cnt_applications AS c
ON a.SK_ID_CURR = c.SK_ID_CURR
GROUP BY applications_bucket
ORDER BY default_pct;



-- For clients with at least one previous application, find their most recent
-- previous NAME_CONTRACT_STATUS (Approved/Refused/Cancelled/Unused offer),
-- then default rate per status — does a past refusal predict current default

WITH ranked AS (
    SELECT
        SK_ID_CURR,
        NAME_CONTRACT_STATUS,
        ROW_NUMBER() OVER (
            PARTITION BY SK_ID_CURR 
            ORDER BY DAYS_DECISION DESC
        ) AS rn
    FROM previous_application
),
last_status AS (
    SELECT SK_ID_CURR, NAME_CONTRACT_STATUS
    FROM ranked
    WHERE rn = 1
)
SELECT
    l.NAME_CONTRACT_STATUS,
    COUNT(*) AS n_clients,
    ROUND(100.0 * SUM(a.TARGET) / COUNT(*), 2) AS default_pct
FROM application a
JOIN last_status l ON a.SK_ID_CURR = l.SK_ID_CURR
GROUP BY l.NAME_CONTRACT_STATUS
ORDER BY default_pct DESC;


-- For clients whose most recent previous application was Refused,
-- find default rate by CODE_REJECT_REASON, restricted to reasons with 200+ occurrences

WITH recent_refused AS (
	SELECT SK_ID_CURR, NAME_CONTRACT_STATUS, CODE_REJECT_REASON,
		ROW_NUMBER() OVER (PARTITION BY SK_ID_CURR ORDER BY DAYS_DECISION DESC) AS row_num
	FROM previous_application
),
final AS (
	SELECT r.*, a.TARGET
	FROM recent_refused AS r
	LEFT JOIN application AS a
	ON r.SK_ID_CURR = a.SK_ID_CURR
	WHERE r.row_num = 1 AND r.NAME_CONTRACT_STATUS = 'Refused'
)
SELECT 
	CODE_REJECT_REASON,
	COUNT(*) AS n,
	ROUND((SUM(TARGET) * 100.0) / COUNT(*),2) AS default_pct
FROM final
GROUP BY CODE_REJECT_REASON
HAVING COUNT(*) >= 200
ORDER BY default_pct DESC;	









