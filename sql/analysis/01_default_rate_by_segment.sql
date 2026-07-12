-- Find default rate (%) by CODE_GENDER, NAME_EDUCATION_TYPE, and NAME_INCOME_TYPE
SELECT CODE_GENDER,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS total_defaults,
    ROUND((SUM(TARGET) * 100) / COUNT(*), 2) AS default_per_gender
FROM application
GROUP BY CODE_GENDER;    

SELECT NAME_EDUCATION_TYPE,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS total_defaults,
    ROUND((SUM(TARGET) * 100) / COUNT(*) ,2) AS default_per_edu
FROM application
GROUP BY NAME_EDUCATION_TYPE;

SELECT NAME_INCOME_TYPE,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS total_defaults,
    ROUND((SUM(TARGET) * 100) / COUNT(*),2) AS default_per_income
FROM application
GROUP BY NAME_INCOME_TYPE;

-- Find default rate (%) by NAME_FAMILY_STATUS, NAME_HOUSING_TYPE, and CNT_CHILDREN
SELECT NAME_FAMILY_STATUS,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS def_cnt,
    ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM application
GROUP BY NAME_FAMILY_STATUS;

SELECT NAME_HOUSING_TYPE,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS def_cnt,
    ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM application
GROUP BY NAME_HOUSING_TYPE;

SELECT CNT_CHILDREN,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS def_cnt,
    ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM application
GROUP BY CNT_CHILDREN;

-- Find default rate (%) by NAME_CONTRACT_TYPE, and by credit-to-income ratio buckets
-- (bucket AMT_CREDIT/AMT_INCOME_TOTAL into ranges: <2, 2-4, 4-6, 6+, then default rate per bucket)
SELECT NAME_CONTRACT_TYPE,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS dft_cnt,
    ROUND((SUM(TARGET) * 100) / COUNT(*),2) AS default_pct
FROM application
GROUP BY NAME_CONTRACT_TYPE;

SELECT AMT_CREDIT/AMT_INCOME_TOTAL AS ratio,
	CASE
		WHEN AMT_CREDIT/AMT_INCOME_TOTAL < 2 THEN 'less_than_two'
		WHEN AMT_CREDIT/AMT_INCOME_TOTAL >= 2 AND AMT_CREDIT/AMT_INCOME_TOTAL < 4 THEN 'two_four'
		WHEN AMT_CREDIT/AMT_INCOME_TOTAL >=4 AND AMT_CREDIT/AMT_INCOME_TOTAL < 6 THEN 'four_six'
		WHEN AMT_CREDIT/AMT_INCOME_TOTAL >= 6 THEN 'above_six'
	END AS category	
FROM application;


WITH buckets AS (
    SELECT TARGET, AMT_CREDIT/AMT_INCOME_TOTAL AS ratio,
        CASE
            WHEN AMT_CREDIT/AMT_INCOME_TOTAL < 2 THEN 'less_than_two'
            WHEN AMT_CREDIT/AMT_INCOME_TOTAL >= 2 AND AMT_CREDIT/AMT_INCOME_TOTAL < 4 THEN 'two_four'
            WHEN AMT_CREDIT/AMT_INCOME_TOTAL >=4 AND AMT_CREDIT/AMT_INCOME_TOTAL < 6 THEN 'four_six'
            WHEN AMT_CREDIT/AMT_INCOME_TOTAL >= 6 THEN 'above_six'
        END AS category	
    FROM application
)
SELECT category,
    COUNT(*) AS total_applicants,
    SUM(TARGET) AS default_cnt,
    ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM buckets
GROUP BY category
ORDER BY default_pct DESC;    

-- Find default rate (%) by age bucket, derived from DAYS_BIRTH
-- (DAYS_BIRTH is negative days from application date; convert to age in years,
-- bucket into <25, 25-35, 35-45, 45-55, 55-65, 65+)

WITH age_categories AS (
	SELECT TARGET, (-1 * DAYS_BIRTH) / 365 AS years,
	CASE
		WHEN (-1 * DAYS_BIRTH) / 365 < 25 THEN 'less_than_25'
		WHEN (-1 * DAYS_BIRTH) / 365 >= 25 AND (-1 * DAYS_BIRTH) / 365 < 35 THEN '25_to_35'
		WHEN (-1 * DAYS_BIRTH) / 365 >= 35 AND (-1 * DAYS_BIRTH) / 365 < 45 THEN '35_to_45'
		WHEN (-1 * DAYS_BIRTH) / 365 >= 45 AND (-1 * DAYS_BIRTH) / 365 < 55 THEN '45_to_55'
		WHEN (-1 * DAYS_BIRTH) / 365 >= 55 AND (-1 * DAYS_BIRTH) / 365 < 65 THEN '55_to_65'
		WHEN (-1 * DAYS_BIRTH) / 365 >= 65 THEN 'above_65'
	END AS age_buckets	
	FROM application
)
SELECT 
	age_buckets,
	COUNT(*) AS total_applicants,
	SUM(TARGET) AS default_cnt,
	ROUND((100 * SUM(TARGET)) / COUNT(*),2) AS default_pct
FROM age_categories
GROUP BY age_buckets
ORDER BY default_pct DESC;	
