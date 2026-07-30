# Credit Risk Analytics

End-to-end credit risk analysis on the Home Credit Default Risk dataset, covering database design, SQL analysis, statistical testing in Python, and an interactive dashboard.

## Overview

This project analyzes 307,511 real loan applications from Home Credit Group, a multinational consumer lending company, to understand the drivers of loan default. The dataset includes seven relational tables covering application data, external bureau credit history, and prior loan behavior, totaling roughly 39 million rows.

The pipeline moves through four stages: a normalized MySQL schema, SQL-based exploratory and business analysis, Python-based outlier treatment and statistical hypothesis testing, and a Streamlit dashboard for interactive exploration of the findings.

## Dataset

Home Credit Default Risk, sourced from the Kaggle competition of the same name: https://www.kaggle.com/c/home-credit-default-risk/data

The dataset was chosen deliberately over more commonly used loan datasets because it is genuine, anonymized data from a real lender rather than a synthetic or heavily preprocessed sample. It includes realistic data quality issues, such as placeholder values in the employment duration field, that had to be identified and handled explicitly rather than assumed away.

Raw data is not included in this repository due to its size. See data/raw/README.md for download and setup instructions.

## Pipeline

Database. A normalized MySQL schema was designed across seven tables, with primary and foreign key constraints enforced throughout. The application table serves as the root entity, with bureau history, prior applications, and their associated monthly balances and payment records linked back to it. The schema is documented in sql/schema/01_create_tables.sql.

SQL analysis. Business questions were answered directly against the database, covering default rate by demographic segment, income and credit affordability, repeat client risk based on prior application outcomes, and external bureau credit signals. Queries are organized by business question rather than by SQL technique, and make use of joins, CTEs, and window functions where appropriate. See sql/analysis/.

Python analysis. Four notebooks cover exploratory data analysis, outlier detection and treatment, distribution testing, and hypothesis testing.

Outlier detection used the interquartile range method rather than Z-scores, a choice justified by testing skewness on the income, credit, and annuity fields beforehand rather than assumed.

A known data quality issue, a placeholder value in the employment duration field affecting roughly eighteen percent of applicants, was identified and handled by flagging it in a separate column rather than imputing a guessed value.

Distribution testing checked whether number of children fit a binomial distribution and whether annual credit bureau inquiries fit a Poisson distribution, comparing real data against theoretical distributions rather than assuming a fit.

Hypothesis testing used two-sample t-tests and chi-square tests to confirm which patterns found in SQL were statistically significant rather than sampling noise, with explicit attention to the difference between statistical significance and practical effect size given the large sample size.

See notebooks/.

Dashboard. An interactive Streamlit dashboard presents the key findings across five sections: portfolio overview, demographic risk, credit behavior, external credit history, and data quality notes. The dashboard includes filters for gender, education, income type, and age range. See dashboards/streamlit_app/.

## Key Findings

Default rate declines consistently with applicant age, from roughly twelve percent for applicants under twenty-five to under four percent for applicants over sixty-five. This relationship was confirmed with a two-sample t-test.

Combined education and income type segments span a fourfold range in default rate, from under four percent to over fourteen percent. Neither factor alone explains this range.

Applicants most recently refused by the lender default at roughly seventy percent higher a rate than those most recently approved.

Applicants with no external bureau credit history have a higher default rate than those with some credit history, a counterintuitive result that reflects the absence of a track record rather than genuine low risk.

Credit-to-income and annuity-to-income ratios do not show a simple linear relationship with default risk. Default rate peaks at moderate leverage rather than rising continuously, likely because underwriting already screens out the highest-leverage applicants before approval.

Income, credit amount, and annuity are all heavily right-skewed. This was confirmed through skewness and kurtosis testing and informed the choice to report medians rather than means throughout the analysis.

## Repository Structure

credit-risk-analytics/
    data/
        raw/                 Source CSVs, not tracked in version control
        processed/           Cleaned dataset produced by the notebooks
    sql/
        schema/              Database schema definition
        exploration/         Initial data profiling
        analysis/            Business question analysis
    notebooks/               Python analysis, run in order
    src/                     Reusable Python functions
    dashboards/
        streamlit_app/       Interactive dashboard
    docs/                    Data dictionary and schema reference
    outputs/                 Exported figures and summary notes
    requirements.txt

## Setup

1. Clone the repository.
2. Download the dataset following the instructions in data/raw/README.md.
3. Create the database using sql/schema/01_create_tables.sql.
4. Load the data using the load scripts referenced in that same file's accompanying notes.
5. Create a Python environment and install dependencies.

   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

6. Create a .env file with your database credentials, following the pattern expected by src/db_connection.py.
7. Run the notebooks in order, from 01_eda.ipynb through 04_hypothesis_testing.ipynb.
8. To run the dashboard.

   cd dashboards/streamlit_app
   pip install -r requirements.txt
   python -m streamlit run app.py

## Tools

MySQL, Python, pandas, NumPy, SciPy, Matplotlib, Seaborn, Streamlit, Plotly.

## Author

Muhammad Ghulam Ali