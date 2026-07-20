# Raw Data

This folder is intentionally empty in the repository. The raw dataset is excluded from
version control via `.gitignore` due to its size (~688MB across 8 CSV files).

## Dataset

**Home Credit Default Risk** — Kaggle competition dataset, real anonymized data from
Home Credit Group, a multinational consumer lending company.

Source: https://www.kaggle.com/c/home-credit-default-risk/data

## Setup

1. Download the dataset from the Kaggle link above (requires a free Kaggle account,
   accept competition rules to unlock download)
2. Extract all CSV files into this folder (`data/raw/`)
3. The project uses 7 of the 8 provided files:
   - `application_train.csv`
   - `bureau.csv`
   - `bureau_balance.csv`
   - `previous_application.csv`
   - `pos_cash_balance.csv`
   - `credit_card_balance.csv`
   - `installments_payments.csv`
4. `application_test.csv` and `sample_submission.csv` are not used, since this project
   only analyzes the labeled training population.

See `sql/schema/01_create_tables.sql` for the database schema these files are loaded into.