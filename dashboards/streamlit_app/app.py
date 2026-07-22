"""
Credit Risk Analytics Dashboard
Home Credit Default Risk dataset (307,511 applicants, 8.07% default rate)

Presentation layer for a project whose full pipeline was:
MySQL (7-table relational schema) -> SQL analysis -> Python (outlier treatment,
distribution testing, hypothesis testing) -> this dashboard.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# CONFIG / CONSTANTS
# ---------------------------------------------------------------------------

DATA_PATH = "/Users/yasir/Desktop/credit-risk-analytics/data/processed/clean_data.csv"
GITHUB_URL = "https://github.com/Muhammad-Ghulam-Ali/credit-risk-analytics"

# Column name mapping. Left side is what the app looks for. If your merged
# clean_data.csv used different names for the bureau / previous_application
# derived columns, change the values here rather than hunting through the
# rest of the file.
COLS = {
    "target": "TARGET",
    "income": "AMT_INCOME_TOTAL",
    "credit": "AMT_CREDIT",
    "annuity": "AMT_ANNUITY",
    "goods_price": "AMT_GOODS_PRICE",
    "gender": "CODE_GENDER",
    "education": "NAME_EDUCATION_TYPE",
    "family_status": "NAME_FAMILY_STATUS",
    "housing": "NAME_HOUSING_TYPE",
    "income_type": "NAME_INCOME_TYPE",
    "contract_type": "NAME_CONTRACT_TYPE",
    "children": "CNT_CHILDREN",
    "fam_members": "CNT_FAM_MEMBERS",
    "days_birth": "DAYS_BIRTH",
    "days_employed": "DAYS_EMPLOYED",
    "days_employed_anomaly": "DAYS_EMPLOYED_ANOMALY",
    "ext1": "EXT_SOURCE_1",
    "ext2": "EXT_SOURCE_2",
    "ext3": "EXT_SOURCE_3",
    # FIX: these three now match the actual column names produced by
    # utils.outlier_detection(), which appends '_OUTLIER' to the original
    # column name (e.g. 'AMT_INCOME_TOTAL' -> 'AMT_INCOME_TOTAL_OUTLIER').
    "income_outlier": "AMT_INCOME_TOTAL_OUTLIER",
    "credit_outlier": "AMT_CREDIT_OUTLIER",
    "annuity_outlier": "AMT_ANNUITY_OUTLIER",
    # Derived from bureau / previous_application tables during the MySQL/Python
    # phase. Update these three if your merged column names differ.
    "bureau_credit_count": "BUREAU_CREDIT_COUNT",
    "bureau_has_overdue": "BUREAU_HAS_OVERDUE",
    "prev_app_refused": "PREV_APP_WAS_REFUSED",
}

PALETTE = ["#1B4F72", "#148F77", "#5DADE2", "#B03A2E", "#7D6608", "#5B2C6F"]
PLOTLY_TEMPLATE = "plotly_white"

st.set_page_config(
    page_title="Credit Risk Analytics | Home Credit Default Risk",
    page_icon="\U0001F4CA",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# STYLING
# ---------------------------------------------------------------------------

def inject_css():
    st.markdown(
        """
        <style>
        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #E1E8EB;
            border-left: 5px solid #1B4F72;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            /* FIX: consistent card height regardless of whether a sub-caption
               is present, so KPI rows line up evenly. */
            min-height: 118px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .kpi-label {
            font-size: 0.80rem;
            color: #5B6B73;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }
        .kpi-value {
            font-size: 1.65rem;
            font-weight: 700;
            color: #1C2B36;
        }
        .kpi-sub {
            font-size: 0.78rem;
            color: #7D8A91;
            margin-top: 0.2rem;
            min-height: 1.4em;
        }
        .section-note {
            background-color: #EAF0F3;
            border-radius: 6px;
            padding: 0.7rem 1rem;
            font-size: 0.92rem;
            color: #1C2B36;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }
        header[data-testid="stHeader"] { background-color: #F7F9FA; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, sub=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def note(text):
    st.markdown(f'<div class="section-note">{text}</div>', unsafe_allow_html=True)


def col_exists(df, key):
    return COLS.get(key) in df.columns


def outlier_rate(df, key):
    """
    FIX: outlier columns hold string values ('Outlier' / 'Normal'), not
    booleans, so a plain .mean() would fail. Handle both string and boolean
    cases safely.
    """
    if not col_exists(df, key):
        return np.nan
    col = df[COLS[key]]
    if col.dtype == bool:
        return col.mean() * 100
    return (col.astype(str).str.strip().str.lower() == "outlier").mean() * 100


# ---------------------------------------------------------------------------
# DATA LOADING / PREP
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading applicant data...")
def load_data(path):
    df = pd.read_csv(path)

    if COLS["days_birth"] in df.columns:
        df["AGE"] = (-df[COLS["days_birth"]] / 365.25).round(1)

    if COLS["days_employed_anomaly"] not in df.columns and COLS["days_employed"] in df.columns:
        df[COLS["days_employed_anomaly"]] = df[COLS["days_employed"]] == 365243

    if col_exists(df, "credit") and col_exists(df, "income"):
        income_safe = df[COLS["income"]].replace(0, np.nan)
        df["CREDIT_INCOME_RATIO"] = df[COLS["credit"]] / income_safe

    if col_exists(df, "annuity") and col_exists(df, "income"):
        income_safe = df[COLS["income"]].replace(0, np.nan)
        df["ANNUITY_INCOME_RATIO"] = df[COLS["annuity"]] / income_safe

    return df


def apply_filters(df, gender_sel, education_sel, income_type_sel, age_range):
    filtered = df.copy()
    if col_exists(df, "gender") and gender_sel:
        filtered = filtered[filtered[COLS["gender"]].isin(gender_sel)]
    if col_exists(df, "education") and education_sel:
        filtered = filtered[filtered[COLS["education"]].isin(education_sel)]
    if col_exists(df, "income_type") and income_type_sel:
        filtered = filtered[filtered[COLS["income_type"]].isin(income_type_sel)]
    if "AGE" in filtered.columns:
        filtered = filtered[filtered["AGE"].between(age_range[0], age_range[1])]
    return filtered


def default_rate(df):
    if COLS["target"] not in df.columns or len(df) == 0:
        return np.nan
    return df[COLS["target"]].mean() * 100


def age_bucket(age):
    bins = [18, 25, 35, 45, 55, 65, 100]
    labels = ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
    return pd.cut(age, bins=bins, labels=labels, right=True)


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

def render_sidebar(df):
    st.sidebar.markdown("### Filters")

    gender_opts = sorted(df[COLS["gender"]].dropna().unique()) if col_exists(df, "gender") else []
    gender_sel = st.sidebar.multiselect("Gender", gender_opts, default=gender_opts)

    edu_opts = sorted(df[COLS["education"]].dropna().unique()) if col_exists(df, "education") else []
    edu_sel = st.sidebar.multiselect("Education", edu_opts, default=edu_opts)

    inc_opts = sorted(df[COLS["income_type"]].dropna().unique()) if col_exists(df, "income_type") else []
    inc_sel = st.sidebar.multiselect("Income type", inc_opts, default=inc_opts)

    if "AGE" in df.columns:
        age_min, age_max = int(df["AGE"].min()), int(df["AGE"].max())
        age_range = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))
    else:
        age_range = (0, 100)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"[View repository on GitHub]({GITHUB_URL})",
        unsafe_allow_html=True,
    )
    st.sidebar.caption(
        "Data: Home Credit Default Risk (public, anonymized). "
        "Pipeline: MySQL -> SQL analysis -> Python -> this dashboard."
    )

    return gender_sel, edu_sel, inc_sel, age_range


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------

def render_header(n_filtered, n_total):
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:0.5rem;">
            <div>
                <h1 style="margin-bottom:0;">Credit Risk Analytics</h1>
                <p style="color:#5B6B73; margin-top:0;">
                    Consumer lending default risk, Home Credit Default Risk dataset &middot;
                    <a href="{GITHUB_URL}" target="_blank">GitHub repo</a>
                </p>
            </div>
            <div style="text-align:right; color:#7D8A91; font-size:0.85rem;">
                Showing {n_filtered:,} of {n_total:,} applicants
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# PAGE 1: OVERVIEW
# ---------------------------------------------------------------------------

def page_overview(df):
    st.subheader("Portfolio Overview")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Applicants", f"{len(df):,}")
    with c2:
        dr = default_rate(df)
        kpi_card("Default Rate", f"{dr:.2f}%" if not np.isnan(dr) else "n/a")
    with c3:
        med_income = df[COLS["income"]].median() if col_exists(df, "income") else np.nan
        kpi_card("Median Income", f"{med_income:,.0f}" if not np.isnan(med_income) else "n/a"
    )
    with c4:
        med_credit = df[COLS["credit"]].median() if col_exists(df, "credit") else np.nan
        kpi_card("Median Credit Amount", f"{med_credit:,.0f}" if not np.isnan(med_credit) else "n/a")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.4])

    with col_left:
        st.markdown("**Default vs. Non-default composition**")
        if COLS["target"] in df.columns:
            counts = df[COLS["target"]].value_counts().rename({0: "Non-default", 1: "Default"})
            fig = px.pie(
                values=counts.values, names=counts.index,
                color=counts.index,
                color_discrete_map={"Non-default": PALETTE[0], "Default": PALETTE[3]},
                hole=0.5, template=PLOTLY_TEMPLATE,
            )
            fig.update_traces(textinfo="percent+label")
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig, use_container_width=True)
        note("8.07% baseline default rate across the full applicant base. Two-category "
             "split, one of the few places a pie chart earns its keep here.")

    with col_right:
        st.markdown("**Default rate by age group**")
        if "AGE" in df.columns and COLS["target"] in df.columns:
            tmp = df.dropna(subset=["AGE", COLS["target"]]).copy()
            tmp["AGE_GROUP"] = age_bucket(tmp["AGE"])
            grp = tmp.groupby("AGE_GROUP", observed=True)[COLS["target"]].mean().reset_index()
            grp[COLS["target"]] *= 100
            fig = px.bar(
                grp, x="AGE_GROUP", y=COLS["target"],
                labels={"AGE_GROUP": "Age group", COLS["target"]: "Default rate (%)"},
                color_discrete_sequence=[PALETTE[0]], template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig, use_container_width=True)
        note("Default rate falls sharply with age, from roughly 12% under 25 to under 4% "
             "at 65+, confirmed with a t-test (p < 0.001). Age is one of the strongest "
             "single risk signals in the dataset.")


# ---------------------------------------------------------------------------
# PAGE 2: DEMOGRAPHIC RISK
# ---------------------------------------------------------------------------

def page_demographic(df):
    st.subheader("Demographic Risk Segments")

    if col_exists(df, "education") and col_exists(df, "income_type") and COLS["target"] in df.columns:
        st.markdown("**Default rate by education x income type**")
        pivot = (
            df.groupby([COLS["education"], COLS["income_type"]], observed=True)[COLS["target"]]
            .mean().mul(100).reset_index()
        )
        pivot_wide = pivot.pivot(index=COLS["education"], columns=COLS["income_type"], values=COLS["target"])
        fig = px.imshow(
            pivot_wide, text_auto=".1f", aspect="auto",
            color_continuous_scale=[PALETTE[0], "#F7F9FA", PALETTE[3]],
            labels=dict(color="Default rate (%)"),
            template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=420)
        st.plotly_chart(fig, use_container_width=True)
        note("Combined education and income-type segments span roughly a 4x range in "
             "default rate, from about 3.9% to 14.6%. Neither factor alone explains this; "
             "the combination is what separates low- and high-risk applicants.")
    else:
        st.warning("Education / income type / target columns not found for this chart.")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Default rate by family status**")
        if col_exists(df, "family_status") and COLS["target"] in df.columns:
            grp = df.groupby(COLS["family_status"], observed=True)[COLS["target"]].mean().mul(100).sort_values()
            fig = px.bar(
                x=grp.values, y=grp.index, orientation="h",
                labels={"x": "Default rate (%)", "y": ""},
                color_discrete_sequence=[PALETTE[1]], template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Default rate by housing type**")
        if col_exists(df, "housing") and COLS["target"] in df.columns:
            grp = df.groupby(COLS["housing"], observed=True)[COLS["target"]].mean().mul(100).sort_values()
            fig = px.bar(
                x=grp.values, y=grp.index, orientation="h",
                labels={"x": "Default rate (%)", "y": ""},
                color_discrete_sequence=[PALETTE[2]], template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE 3: CREDIT BEHAVIOR
# ---------------------------------------------------------------------------

def page_credit_behavior(df):
    st.subheader("Credit Behavior")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Credit-to-income ratio vs. default rate**")
        if "CREDIT_INCOME_RATIO" in df.columns and COLS["target"] in df.columns:
            tmp = df.dropna(subset=["CREDIT_INCOME_RATIO", COLS["target"]]).copy()
            tmp = tmp[tmp["CREDIT_INCOME_RATIO"] < tmp["CREDIT_INCOME_RATIO"].quantile(0.99)]
            tmp["RATIO_BUCKET"] = pd.qcut(tmp["CREDIT_INCOME_RATIO"], 8, duplicates="drop")
            grp = tmp.groupby("RATIO_BUCKET", observed=True)[COLS["target"]].mean().mul(100).reset_index()
            grp["RATIO_BUCKET"] = grp["RATIO_BUCKET"].astype(str)
            fig = px.line(
                grp, x="RATIO_BUCKET", y=COLS["target"], markers=True,
                labels={"RATIO_BUCKET": "Credit / income ratio (bucket)", COLS["target"]: "Default rate (%)"},
                color_discrete_sequence=[PALETTE[0]], template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        note("Risk does not rise monotonically with leverage. Mid-range credit-to-income "
             "ratios show the highest default rates, likely because underwriting already "
             "screens out the highest-leverage applicants before approval.")

    with c2:
        st.markdown("**Annuity-to-income ratio vs. default rate**")
        if "ANNUITY_INCOME_RATIO" in df.columns and COLS["target"] in df.columns:
            tmp = df.dropna(subset=["ANNUITY_INCOME_RATIO", COLS["target"]]).copy()
            tmp = tmp[tmp["ANNUITY_INCOME_RATIO"] < tmp["ANNUITY_INCOME_RATIO"].quantile(0.99)]
            tmp["RATIO_BUCKET"] = pd.qcut(tmp["ANNUITY_INCOME_RATIO"], 8, duplicates="drop")
            grp = tmp.groupby("RATIO_BUCKET", observed=True)[COLS["target"]].mean().mul(100).reset_index()
            grp["RATIO_BUCKET"] = grp["RATIO_BUCKET"].astype(str)
            fig = px.line(
                grp, x="RATIO_BUCKET", y=COLS["target"], markers=True,
                labels={"RATIO_BUCKET": "Annuity / income ratio (bucket)", COLS["target"]: "Default rate (%)"},
                color_discrete_sequence=[PALETTE[1]], template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        note("Same pattern as credit-to-income: the annuity burden relationship is not a "
             "straight line. Treat leverage ratios as one input among several, not a "
             "standalone risk score.")

    st.markdown("**Default rate by contract type**")
    if col_exists(df, "contract_type") and COLS["target"] in df.columns:
        grp = df.groupby(COLS["contract_type"], observed=True)[COLS["target"]].mean().mul(100).reset_index()
        fig = px.bar(
            grp, x=COLS["contract_type"], y=COLS["target"],
            labels={COLS["contract_type"]: "Contract type", COLS["target"]: "Default rate (%)"},
            color_discrete_sequence=[PALETTE[4]], template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE 4: EXTERNAL CREDIT HISTORY
# ---------------------------------------------------------------------------

def page_external_credit(df):
    st.subheader("External Credit History (Bureau Signals)")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Bureau credit line count vs. default rate**")
        if col_exists(df, "bureau_credit_count") and COLS["target"] in df.columns:
            tmp = df.dropna(subset=[COLS["bureau_credit_count"], COLS["target"]]).copy()
            tmp["BUREAU_COUNT_BUCKET"] = tmp[COLS["bureau_credit_count"]].clip(upper=10)
            grp = tmp.groupby("BUREAU_COUNT_BUCKET", observed=True)[COLS["target"]].mean().mul(100).reset_index()
            fig = px.bar(
                grp, x="BUREAU_COUNT_BUCKET", y=COLS["target"],
                labels={"BUREAU_COUNT_BUCKET": "Bureau credit lines (10 = 10+)", COLS["target"]: "Default rate (%)"},
                color_discrete_sequence=[PALETTE[0]], template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig, use_container_width=True)
            note("Applicants with zero prior bureau credit lines have the highest default "
                 "rate (about 10.1%), higher than applicants with some credit history. "
                 "'Thin file' does not mean low risk; it means no track record to score.")
        else:
            st.warning(f"Column '{COLS['bureau_credit_count']}' not found. "
                       "Update COLS['bureau_credit_count'] at the top of app.py to match "
                       "your merged dataset.")

    with c2:
        st.markdown("**Overdue bureau history vs. default rate**")
        if col_exists(df, "bureau_has_overdue") and COLS["target"] in df.columns:
            grp = df.groupby(COLS["bureau_has_overdue"], observed=True)[COLS["target"]].mean().mul(100).reset_index()
            grp[COLS["bureau_has_overdue"]] = grp[COLS["bureau_has_overdue"]].map(
                {True: "Has overdue history", False: "No overdue history", 1: "Has overdue history", 0: "No overdue history"}
            )
            fig = px.bar(
                grp, x=COLS["bureau_has_overdue"], y=COLS["target"],
                labels={COLS["bureau_has_overdue"]: "", COLS["target"]: "Default rate (%)"},
                color_discrete_sequence=[PALETTE[3]], template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig, use_container_width=True)
            note("Applicants with any overdue bureau credit history default at roughly "
                 "2x the rate of those without. Of the bureau-derived signals, this is "
                 "the most direct.")
        else:
            st.warning(f"Column '{COLS['bureau_has_overdue']}' not found. "
                       "Update COLS['bureau_has_overdue'] at the top of app.py to match "
                       "your merged dataset.")

    st.markdown("**Prior application outcome vs. default rate**")
    if col_exists(df, "prev_app_refused") and COLS["target"] in df.columns:
        grp = df.groupby(COLS["prev_app_refused"], observed=True)[COLS["target"]].mean().mul(100).reset_index()
        grp[COLS["prev_app_refused"]] = grp[COLS["prev_app_refused"]].map(
            {True: "Previously refused", False: "Previously approved / no history",
             1: "Previously refused", 0: "Previously approved / no history"}
        )
        fig = px.bar(
            grp, x=COLS["prev_app_refused"], y=COLS["target"],
            labels={COLS["prev_app_refused"]: "", COLS["target"]: "Default rate (%)"},
            color_discrete_sequence=[PALETTE[5]], template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig, use_container_width=True)
        note("Applicants previously refused by the lender default at about 12.5%, versus "
             "7.4% for those previously approved, roughly 70% higher. Application history "
             "is a meaningful signal even when the current application looks clean.")
    else:
        st.warning(f"Column '{COLS['prev_app_refused']}' not found. "
                   "Update COLS['prev_app_refused'] at the top of app.py to match your "
                   "merged dataset.")

    if col_exists(df, "gender") and COLS["target"] in df.columns:
        st.markdown("**Default rate by gender**")
        grp = df.groupby(COLS["gender"], observed=True)[COLS["target"]].mean().mul(100).reset_index()
        fig = px.bar(
            grp, x=COLS["gender"], y=COLS["target"],
            labels={COLS["gender"]: "Gender", COLS["target"]: "Default rate (%)"},
            color_discrete_sequence=[PALETTE[2]], template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
        note("A chi-square test confirms a statistically significant association between "
             "gender and default (p < 0.001). The gap in the chart above is the effect "
             "size; with this sample size, statistical significance alone does not imply "
             "the gap is large in practical terms.")


# ---------------------------------------------------------------------------
# PAGE 5: DATA QUALITY NOTES
# ---------------------------------------------------------------------------

def page_data_quality(df):
    st.subheader("Data Quality Notes")

    st.markdown("#### DAYS_EMPLOYED anomaly")
    if col_exists(df, "days_employed_anomaly"):
        pct_anomaly = df[COLS["days_employed_anomaly"]].mean() * 100
        st.write(
            f"About **{pct_anomaly:.1f}%** of applicants have `DAYS_EMPLOYED = 365243`, "
            "a placeholder value rather than a real employment duration. This affects "
            "roughly 18% of the applicant base in the source dataset, and it is not "
            "randomly distributed: it concentrates among pensioners and unemployed "
            "applicants. It was kept as a flag column rather than imputed with a guessed "
            "value, so any model or chart using employment duration can condition on it "
            "instead of treating it as a real number."
        )
    else:
        st.warning("DAYS_EMPLOYED_ANOMALY column not found in this dataset.")

    st.markdown("#### Outlier treatment")
    st.write(
        "Income, credit amount, and annuity were treated with an IQR-based approach "
        "rather than removal: values outside 1.5x IQR were flagged rather than dropped, "
        "since a handful of genuinely high-income, high-credit applicants are real "
        "signal, not data errors. Charts on this dashboard use medians and log-scale-"
        "friendly bucketing rather than raw means for exactly this reason."
    )

    c1, c2, c3 = st.columns(3)
    for c, key, label in zip(
        [c1, c2, c3],
        ["income_outlier", "credit_outlier", "annuity_outlier"],
        ["Income outlier rate", "Credit outlier rate", "Annuity outlier rate"],
    ):
        with c:
            # FIX: use the outlier_rate() helper, which correctly handles the
            # string-valued 'Outlier' / 'Normal' columns instead of calling
            # .mean() directly on non-numeric data.
            rate = outlier_rate(df, key)
            kpi_card(label, f"{rate:.2f}%" if not np.isnan(rate) else "n/a")

    st.markdown("#### Distribution testing conclusions")
    st.write(
        "Income, credit amount, and annuity are all heavily right-skewed, confirmed via "
        "skewness and kurtosis testing rather than eyeballing histograms. This is why "
        "the dashboard reports medians instead of means for these fields, and why ratio "
        "charts use quantile-based bucketing instead of fixed-width bins: fixed bins on "
        "a right-skewed variable put almost all applicants in the first one or two "
        "buckets and hide the pattern."
    )

    if col_exists(df, "income"):
        st.markdown("**Income distribution (log scale)**")
        tmp = df[df[COLS["income"]] > 0].copy()
        # FIX: plotly's px.histogram with log_x=True does not always bin
        # correctly on wide-range, heavily skewed data (bars can silently
        # fail to render). Transforming to log10 first and plotting on a
        # linear axis is more reliable.
        tmp["LOG10_INCOME"] = np.log10(tmp[COLS["income"]])
        fig = px.histogram(
            tmp, x="LOG10_INCOME", nbins=60,
            color_discrete_sequence=[PALETTE[0]], template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320,
                          xaxis_title="Total income (log10 scale)", yaxis_title="Applicants")
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    inject_css()

    try:
        df_raw = load_data(DATA_PATH)
    except FileNotFoundError:
        st.error(
            f"Could not find `{DATA_PATH}`. Place the cleaned dataset there, or update "
            "DATA_PATH at the top of app.py."
        )
        st.stop()

    gender_sel, edu_sel, inc_sel, age_range = render_sidebar(df_raw)
    df = apply_filters(df_raw, gender_sel, edu_sel, inc_sel, age_range)

    render_header(len(df), len(df_raw))

    tabs = st.tabs([
        "Overview",
        "Demographic Risk",
        "Credit Behavior",
        "External Credit History",
        "Data Quality Notes",
    ])

    with tabs[0]:
        page_overview(df)
    with tabs[1]:
        page_demographic(df)
    with tabs[2]:
        page_credit_behavior(df)
    with tabs[3]:
        page_external_credit(df)
    with tabs[4]:
        page_data_quality(df)


if __name__ == "__main__":
    main()