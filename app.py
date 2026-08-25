import streamlit as st
import pandas as pd

# --------------------------------------------------
# PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Rebel Data",
    page_icon="🟩",
    layout="wide"
)

# --------------------------------------------------
# BRANDING / CSS
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #3d3d3f;
    color: white;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

.rebel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 18px;
    border-bottom: 1px solid #5a5a5c;
}

.rebel-logo {
    font-size: 40px;
    font-weight: 800;
    line-height: 1;
}

.rebel-green {
    color: #8bd02f;
}

.rebel-white {
    color: #ffffff;
}

.rebel-subtitle {
    color: #c5c5c5;
    font-size: 15px;
    margin-top: 5px;
}

.header-link {
    color: #8bd02f;
    font-size: 14px;
    font-weight: 800;
}

.hero-title {
    font-size: 44px;
    font-weight: 800;
    margin-top: 42px;
    margin-bottom: 5px;
    color: white;
}

.hero-subtitle {
    font-size: 18px;
    color: #d2d2d2;
    margin-bottom: 35px;
}

.section-title {
    font-size: 28px;
    font-weight: 800;
    color: white;
    margin-top: 15px;
    margin-bottom: 12px;
}

label {
    color: white !important;
    font-weight: 600 !important;
}

.stButton > button {
    background-color: #8bd02f;
    color: #222222;
    border: none;
    border-radius: 5px;
    font-weight: 800;
    padding: 0.7rem 2rem;
}

.stButton > button:hover {
    background-color: #9be33b;
    color: #222222;
    border: none;
}

.stDownloadButton > button {
    background-color: #8bd02f;
    color: #222222;
    border: none;
    border-radius: 5px;
    font-weight: 800;
}

[data-testid="stMetricValue"] {
    color: #8bd02f;
    font-weight: 800;
}

[data-testid="stMetricLabel"] {
    color: white;
}

hr {
    border-color: #5a5a5c;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("""
<div class="rebel-header">
    <div>
        <div class="rebel-logo">
            <span class="rebel-green">Rebel</span>
            <span class="rebel-white">Data</span>
        </div>
        <div class="rebel-subtitle">
            UK Business Intelligence
        </div>
    </div>
    <div class="header-link">
        COMPANY SEARCH
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# HERO
# --------------------------------------------------

st.markdown(
    '<div class="hero-title">Find the businesses that matter.</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-subtitle">'
    'Search and select UK companies using Rebel Data.'
    '</div>',
    unsafe_allow_html=True
)

# --------------------------------------------------
# DEMO DATA
# --------------------------------------------------

data = [
    {
        "Company Number": "01234567",
        "Company Name": "ABC CONSULTING LIMITED",
        "Company Status": "Active",
        "SIC Code": "70229",
        "Industry": "Management Consultancy",
        "Location": "Gloucester",
        "Postcode": "GL1 1AA",
        "Employees": 24,
        "Turnover": 3200000,
        "Accountant": "SMITH & CO",
        "Auditor": "GRANT & PARTNERS"
    },
    {
        "Company Number": "02345678",
        "Company Name": "BRISTOL TECHNOLOGY LIMITED",
        "Company Status": "Active",
        "SIC Code": "62020",
        "Industry": "Information Technology",
        "Location": "Bristol",
        "Postcode": "BS1 4AB",
        "Employees": 51,
        "Turnover": 7800000,
        "Accountant": "WEST ACCOUNTANCY LLP",
        "Auditor": "TECH AUDIT LLP"
    },
    {
        "Company Number": "03456789",
        "Company Name": "COTSWOLD SERVICES LIMITED",
        "Company Status": "Active",
        "SIC Code": "82990",
        "Industry": "Business Services",
        "Location": "Cheltenham",
        "Postcode": "GL50 1AA",
        "Employees": 17,
        "Turnover": 1700000,
        "Accountant": "HAZELWOOD ACCOUNTANTS",
        "Auditor": ""
    },
    {
        "Company Number": "04567890",
        "Company Name": "REBEL MARKETING LIMITED",
        "Company Status": "Active",
        "SIC Code": "73110",
        "Industry": "Advertising",
        "Location": "London",
        "Postcode": "EC1A 1BB",
        "Employees": 83,
        "Turnover": 12400000,
        "Accountant": "CITY ACCOUNTANTS LLP",
        "Auditor": "LONDON AUDIT LLP"
    },
    {
        "Company Number": "05678901",
        "Company Name": "MIDLAND ENGINEERING LIMITED",
        "Company Status": "Active",
        "SIC Code": "71129",
        "Industry": "Engineering",
        "Location": "Birmingham",
        "Postcode": "B1 1AA",
        "Employees": 142,
        "Turnover": 28600000,
        "Accountant": "MIDLANDS FINANCE LLP",
        "Auditor": "CENTRAL AUDIT LLP"
    }
]

df = pd.DataFrame(data)

# --------------------------------------------------
# SEARCH FORM
# --------------------------------------------------

st.markdown(
    '<div class="section-title">Company Search</div>',
    unsafe_allow_html=True
)

with st.form("company_search_form"):

    row1_col1, row1_col2, row1_col3 = st.columns(3)

    with row1_col1:
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g. Rebel"
        )

    with row1_col2:
        company_number = st.text_input(
            "Company Number",
            placeholder="e.g. 01234567"
        )

    with row1_col3:
        company_status = st.selectbox(
            "Company Status",
            ["All"] + sorted(df["Company Status"].unique().tolist())
        )

    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row2_col1:
        sic = st.text_input(
            "SIC Code / Industry",
            placeholder="e.g. 69201 or Accountancy"
        )

    with row2_col2:
        location = st.text_input(
            "Location / Postcode",
            placeholder="e.g. GL or Gloucester"
        )

    with row2_col3:
        accountant = st.text_input(
            "Accountant",
            placeholder="e.g. Smith"
        )

    row3_col1, row3_col2, row3_col3 = st.columns(3)

    with row3_col1:
        min_employees = st.number_input(
            "Minimum Employees",
            min_value=0,
            value=0
        )

    with row3_col2:
        max_employees = st.number_input(
            "Maximum Employees",
            min_value=0,
            value=0
        )

    with row3_col3:
        auditor = st.text_input(
            "Auditor",
            placeholder="e.g. Grant"
        )

    row4_col1, row4_col2 = st.columns(2)

    with row4_col1:
        min_turnover = st.number_input(
            "Minimum Turnover (£)",
            min_value=0,
            value=0,
            step=100000
        )

    with row4_col2:
        max_turnover = st.number_input(
            "Maximum Turnover (£)",
            min_value=0,
            value=0,
            step=100000
        )

    search = st.form_submit_button(
        "SEARCH COMPANIES",
        type="primary"
    )

# --------------------------------------------------
# FILTER RESULTS
# --------------------------------------------------

if search:

    results = df.copy()

    if company_name:
        results = results[
            results["Company Name"].str.contains(
                company_name,
                case=False,
                na=False
            )
        ]

    if company_number:
        results = results[
            results["Company Number"].str.contains(
                company_number,
                case=False,
                na=False
            )
        ]

    if company_status != "All":
        results = results[
            results["Company Status"] == company_status
        ]

    if sic:
        results = results[
            results["SIC Code"].str.contains(
                sic,
                case=False,
                na=False
            )
            |
            results["Industry"].str.contains(
                sic,
                case=False,
                na=False
            )
        ]

    if location:
        results = results[
            results["Location"].str.contains(
                location,
                case=False,
                na=False
            )
            |
            results["Postcode"].str.contains(
                location,
                case=False,
                na=False
            )
        ]

    if accountant:
        results = results[
            results["Accountant"].str.contains(
                accountant,
                case=False,
                na=False
            )
        ]

    if auditor:
        results = results[
            results["Auditor"].str.contains(
                auditor,
                case=False,
                na=False
            )
        ]

    if min_employees > 0:
        results = results[
            results["Employees"] >= min_employees
        ]

    if max_employees > 0:
        results = results[
            results["Employees"] <= max_employees
        ]

    if min_turnover > 0:
        results = results[
            results["Turnover"] >= min_turnover
        ]

    if max_turnover > 0:
        results = results[
            results["Turnover"] <= max_turnover
        ]

    st.session_state["results"] = results

# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if "results" in st.session_state:

    results = st.session_state["results"]

    st.markdown("<hr>", unsafe_allow_html=True)

    metric_col1, metric_col2 = st.columns([1, 4])

    with metric_col1:
        st.metric(
            "COMPANIES FOUND",
            f"{len(results):,}"
        )

    display_df = results.copy()

    display_df["Turnover"] = display_df["Turnover"].apply(
        lambda x: f"£{x:,.0f}"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    csv = results.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="DOWNLOAD SELECTION",
        data=csv,
        file_name="rebel_data_selection.csv",
        mime="text/csv"
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("""
<div style="
    color:#999999;
    font-size:13px;
">
    © Rebel Data | UK Business Intelligence
</div>
""", unsafe_allow_html=True)
