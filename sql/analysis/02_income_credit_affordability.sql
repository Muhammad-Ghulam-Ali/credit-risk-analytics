-- Compare average AMT_INCOME_TOTAL, AMT_CREDIT, AMT_ANNUITY between
-- defaulters (TARGET=1) and non-defaulters (TARGET=0)
SELECT  AVG(AMT_INCOME_TOTAL) AS avg_income,
    AVG(AMT_CREDIT) AS avg_credit, 
    AVG(AMT_ANNUITY) AS avg_annuity,
	CASE
		WHEN TARGET = 1 THEN 'Default'
		WHEN TARGET = 0 THEN 'Non Default'
		END AS default_status
FROM application
GROUP BY default_status
ORDER BY AVG(AMT_INCOME_TOTAL) DESC;

-- Bucket annuity-to-income ratio (AMT_ANNUITY/AMT_INCOME_TOTAL) into ranges:
-- <0.1, 0.1-0.2, 0.2-0.3, 0.3-0.4, 0.4+
-- then default rate per bucket (this measures debt burden as % of income)
SELECT ROUND(AVG(AMT_ANNUITY / AMT_INCOME_TOTAL), 2) AS annuity_ratio,
    CASE
        WHEN AMT_ANNUITY / AMT_INCOME_TOTAL < 0.1 THEN 'below_0.1'
        WHEN AMT_ANNUITY / AMT_INCOME_TOTAL < 0.2 THEN '0.1_to_0.2'
        WHEN AMT_ANNUITY / AMT_INCOME_TOTAL < 0.3 THEN '0.2_to_0.3'
        WHEN AMT_ANNUITY / AMT_INCOME_TOTAL < 0.4 THEN '0.3_to_0.4'
        ELSE 'above_0.4'
    END AS buckets,
    ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM application
WHERE AMT_INCOME_TOTAL > 0 AND AMT_ANNUITY IS NOT NULL
GROUP BY buckets
ORDER BY annuity_ratio;   

-- Compare AMT_CREDIT vs AMT_GOODS_PRICE: calculate how much extra credit was
-- financed beyond the goods price (AMT_CREDIT - AMT_GOODS_PRICE), bucket into
-- negative/zero, small overage, large overage, then default rate per bucket
SELECT 
    CASE
        WHEN AMT_CREDIT - AMT_GOODS_PRICE <= 0 THEN 'no_overage'
        WHEN (AMT_CREDIT - AMT_GOODS_PRICE) / AMT_GOODS_PRICE < 0.1 THEN 'small_overage_under_10pct'
        ELSE 'large_overage_10pct_plus'
    END AS bucket,
    ROUND(AVG(AMT_CREDIT),2) AS avg_credit,
    ROUND(AVG(AMT_GOODS_PRICE),2) AS avg_goods_price,
    ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM application
WHERE AMT_GOODS_PRICE > 0
GROUP BY bucket
ORDER BY default_pct;

-- Combine NAME_INCOME_TYPE and NAME_EDUCATION_TYPE into a single segment,
-- find default rate per combination, restricted to combos with 500+ applicants,
-- ordered by default rate descending
SELECT 
	CONCAT(NAME_INCOME_TYPE, ' - ', NAME_EDUCATION_TYPE) AS segment,
	COUNT(*) AS total_applicants,
	ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM application
GROUP BY segment
HAVING total_applicants > 500
ORDER BY default_pct DESC;