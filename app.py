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
# REBEL DATA BRANDING
# --------------------------------------------------

st.markdown("""
<style>

/* Main background */
.stApp {
    background-color: #3d3d3f;
    color: white;
}

/* Hide Streamlit default header/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Main content width */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Rebel Data logo-style heading */
.rebel-logo {
    font-size: 38px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 5px;
}

.rebel-green {
    color: #8bd02f;
}

.rebel-white {
    color: #ffffff;
}

/* Headings */
h1, h2, h3 {
    color: white !important;
}

.search-title {
    font-size: 42px;
    font-weight: 800;
    color: white;
    margin-top: 25px;
}

.search-subtitle {
    font-size: 18px;
    color: #d6d6d6;
    margin-bottom: 25px;
}

/* Labels */
label {
    color: white !important;
    font-weight: 600 !important;
}

/* Search button */
.stButton > button {
    background-color: #8bd02f;
    color: #222222;
    border: none;
    border-radius: 5px;
    font-weight: 800;
    padding: 0.65rem 2rem;
}

.stButton > button:hover {
    background-color: #9be33b;
    color: #222222;
    border: none;
}

/* Download button */
.stDownloadButton > button {
    background-color: #8bd02f;
    color: #222222;
    border: none;
    font-weight: 800;
}

/* Horizontal lines */
hr {
    border-color: #666666;
}

/* Metric */
[data-testid="stMetricValue"] {
    color: #8bd02f;
}

[data-testid="stMetricLabel"] {
    color: white;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

col_logo, col_right = st.columns([3, 1])

with col_logo:

    st.markdown("""
        <div class="rebel-logo">
            <span class="rebel-green">Rebel</span>
            <span class="rebel-white">Data</span>
        </div>
        <div style="color:#bdbdbd;">
            UK Business Intelligence
        </div>
    """, unsafe_allow_html=True)

with col_right:

    st.markdown("""
        <div style="
            text-align:right;
            color:#8bd02f;
            font-weight:700;
            padding-top:15px;
        ">
            COMPANY SEARCH
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.markdown(
    '<div class="search-title">Find the businesses that matter.</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="search-subtitle">'
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
# SEARCH
# --------------------------------------------------

st.subheader("Company Search")

col1, col2, col3 = st.columns(3)

with col1:

    company_name = st.text_input(
        "Company Name",
        placeholder="e.g. Rebel"
    )

    location = st.text_input(
        "Location / Postcode",
        placeholder="e.g. GL or Gloucester"
    )

with col2:

    industry = st.selectbox(
        "Industry",
        ["All"] + sorted(df["Industry"].unique().tolist())
    )

    accountant = st.text_input(
        "Accountant",
        placeholder="e.g. Smith"
    )

with col3:

    min_employees = st.number_input(
        "Minimum Employees",
        min_value=0,
        value=0
    )

    auditor = st.text_input(
        "Auditor",
        placeholder="e.g. Grant"
    )


search = st.button(
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
            results["Company Name"]
            .str.contains(
                company_name,
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

    if industry != "All":

        results = results[
            results["Industry"] == industry
        ]

    if min_employees > 0:

        results = results[
            results["Employees"] >= min_employees
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

    st.session_state["results"] = results


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if "results" in st.session_state:

    results = st.session_state["results"]

    st.markdown("<hr>", unsafe_allow_html=True)

    st.metric(
        "COMPANIES FOUND",
        f"{len(results):,}"
    )

    display_df = results.copy()

    display_df["Turnover"] = display_df[
        "Turnover"
    ].apply(
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
        label="DOWNLOAD CSV",
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
