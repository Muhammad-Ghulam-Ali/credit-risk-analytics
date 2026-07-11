-- Tables in home credit database
SHOW TABLES IN home_credit;

-- Find the total row count for each of the 7 tables in home_credit
SELECT COUNT(*) AS total_rows, 'application' AS table_name FROM application
UNION ALL
SELECT COUNT(*) AS total_rows, 'bureau' AS table_name FROM bureau
UNION ALL
SELECT COUNT(*) AS total_rows, 'bureau_balance' AS table_name FROM bureau_balance
UNION ALL
SELECT COUNT(*) AS total_rows, 'credit_card_balance' AS table_name FROM credit_card_balance
UNION ALL
SELECT COUNT(*) AS total_rows, 'installments_payments' AS table_name FROM installments_payments
UNION ALL
SELECT COUNT(*) AS total_rows, 'pos_cash_balance' AS table_name FROM pos_cash_balance
UNION ALL
SELECT COUNT(*) AS total_rows, 'previous_application' AS table_name FROM previous_application
ORDER BY total_rows DESC;

-- Find TARGET distribution in application: count and % of defaults vs non-defaults
WITH total_default AS (
    SELECT COUNT(*) AS default_count
    FROM application
    WHERE TARGET = 1
),
total_non_default AS (
    SELECT COUNT(*) AS non_default_count
    FROM application
    WHERE TARGET = 0
),
total_rows AS (
    SELECT COUNT(*) AS application_rows
	FROM application
),
default_ratio AS (
    SELECT default_count / application_rows AS percentage_default
    FROM total_default, total_rows
),
non_default_ratio AS (
    SELECT non_default_count / application_rows AS percentage_non_default
    FROM total_non_default, total_rows
)
SELECT default_count, non_default_count, percentage_default, percentage_non_default
FROM total_default, total_non_default, default_ratio, non_default_ratio;

-- Find  missing values for key columns: AMT_INCOME_TOTAL, AMT_CREDIT, AMT_ANNUITY,
-- EXT_SOURCE_1, EXT_SOURCE_2, EXT_SOURCE_3, OCCUPATION_TYPE, DAYS_EMPLOYED
SELECT
    COUNT(*) - COUNT(AMT_INCOME_TOTAL) AS missing_income_total,
    COUNT(*) - COUNT(AMT_CREDIT) AS missing_amount_credit,
    COUNT(*) - COUNT(AMT_ANNUITY) AS missing_amount_annuity,
    COUNT(*) - COUNT(EXT_SOURCE_1) AS missing_ext_1,
    COUNT(*) - COUNT(EXT_SOURCE_2) AS missing_ext_2,
    COUNT(*) - COUNT(EXT_SOURCE_3) AS missing_ext_3,
    COUNT(*) - COUNT(OCCUPATION_TYPE) AS missing_occupation_type,
    COUNT(*) - COUNT(DAYS_EMPLOYED) AS missing_days_employeed
FROM application;

-- Find distribution of NAME_CONTRACT_TYPE, CODE_GENDER, NAME_EDUCATION_TYPE
-- (count and % share for each category)
SELECT NAME_CONTRACT_TYPE,
    COUNT(*) AS cnt,
    ROUND((COUNT(*) * 100) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM application
GROUP BY NAME_CONTRACT_TYPE;    

SELECT CODE_GENDER,
    COUNT(*) AS cnt,
    ROUND((COUNT(*) * 100) / SUM(COUNT(*)) OVER(), 2)AS pct
FROM application
GROUP BY CODE_GENDER;    

SELECT NAME_EDUCATION_TYPE,
    COUNT(*) AS cnt,
    ROUND(COUNT(*) * 100/ SUM(COUNT(*)) OVER() , 2)
FROM application
GROUP BY NAME_EDUCATION_TYPE;    