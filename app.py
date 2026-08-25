import streamlit as st
import pandas as pd

# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="Rebel Data",
    page_icon="🟩",
    layout="wide"
)


# ==================================================
# REBEL DATA BRANDING / CSS
# ==================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background-color: #3d3d3f;
        color: white;
    }

    /* Hide Streamlit menu and footer */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* Main page area */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        max-width: 1450px;
    }

    /* Logo */
    .rebel-logo {
        font-size: 40px;
        font-weight: 800;
        line-height: 1.1;
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
        margin-top: 6px;
    }

    /* Hero */
    .hero-title {
        font-size: 44px;
        font-weight: 800;
        margin-top: 40px;
        margin-bottom: 5px;
        color: white;
    }

    .hero-subtitle {
        font-size: 18px;
        color: #d2d2d2;
        margin-bottom: 35px;
    }

    /* Section titles */
    .section-title {
        font-size: 28px;
        font-weight: 800;
        color: white;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    /* Input labels */
    label {
        color: white !important;
        font-weight: 600 !important;
    }

    /* Search button */
    div[data-testid="stFormSubmitButton"] button {
        background-color: #8bd02f !important;
        color: #222222 !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: 800 !important;
        padding: 0.7rem 2rem !important;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #9be33b !important;
        color: #222222 !important;
        border: none !important;
    }

    /* Download button */
    div[data-testid="stDownloadButton"] button {
        background-color: #8bd02f !important;
        color: #222222 !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: 800 !important;
    }

    div[data-testid="stDownloadButton"] button:hover {
        background-color: #9be33b !important;
        color: #222222 !important;
        border: none !important;
    }

    /* Results metric */
    [data-testid="stMetricValue"] {
        color: #8bd02f !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricLabel"] {
        color: white !important;
    }

    /* Horizontal lines */
    hr {
        border-color: #5a5a5c !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# HEADER
# ==================================================

header_col1, header_col2 = st.columns([4, 1])

with header_col1:

    st.markdown(
        '<div class="rebel-logo">'
        '<span class="rebel-green">Rebel</span> '
        '<span class="rebel-white">Data</span>'
        '</div>'
        '<div class="rebel-subtitle">'
        'UK Business Intelligence'
        '</div>',
        unsafe_allow_html=True
    )


with header_col2:

    st.markdown(
        '<div style="'
        'text-align:right;'
        'color:#8bd02f;'
        'font-size:14px;'
        'font-weight:800;'
        'padding-top:12px;'
        '">'
        'COMPANY SEARCH'
        '</div>',
        unsafe_allow_html=True
    )


st.markdown(
    "<hr>",
    unsafe_allow_html=True
)


# ==================================================
# HERO
# ==================================================

st.markdown(
    '<div class="hero-title">'
    'Find the businesses that matter.'
    '</div>',
    unsafe_allow_html=True
)


st.markdown(
    '<div class="hero-subtitle">'
    'Search and select UK companies using Rebel Data.'
    '</div>',
    unsafe_allow_html=True
)


# ==================================================
# DEMO DATA
# ==================================================

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
    },

    {
        "Company Number": "06789012",
        "Company Name": "GLOUCESTER ACCOUNTANCY LIMITED",
        "Company Status": "Active",
        "SIC Code": "69201",
        "Industry": "Accounting and Auditing",
        "Location": "Gloucester",
        "Postcode": "GL2 5AA",
        "Employees": 36,
        "Turnover": 4600000,
        "Accountant": "INTERNAL",
        "Auditor": "WESTERN AUDIT LLP"
    }

]


df = pd.DataFrame(data)


# ==================================================
# COMPANY SEARCH
# ==================================================

st.markdown(
    '<div class="section-title">'
    'Company Search'
    '</div>',
    unsafe_allow_html=True
)


with st.form("company_search_form"):


    # --------------------------------------------------
    # ROW 1
    # --------------------------------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        company_name = st.text_input(
            "Company Name",
            placeholder="e.g. Rebel"
        )


    with col2:

        company_number = st.text_input(
            "Company Number",
            placeholder="e.g. 01234567"
        )


    with col3:

        company_status = st.selectbox(
            "Company Status",
            [
                "All",
                "Active",
                "Dissolved"
            ]
        )


    # --------------------------------------------------
    # ROW 2
    # --------------------------------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        sic = st.text_input(
            "SIC Code / Industry",
            placeholder="e.g. 69201 or Accountancy"
        )


    with col2:

        location = st.text_input(
            "Location / Postcode",
            placeholder="e.g. GL or Gloucester"
        )


    with col3:

        accountant = st.text_input(
            "Accountant",
            placeholder="e.g. Smith"
        )


    # --------------------------------------------------
    # ROW 3
    # --------------------------------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        min_employees = st.number_input(
            "Minimum Employees",
            min_value=0,
            value=0,
            step=1
        )


    with col2:

        max_employees = st.number_input(
            "Maximum Employees",
            min_value=0,
            value=0,
            step=1
        )


    with col3:

        auditor = st.text_input(
            "Auditor",
            placeholder="e.g. Grant"
        )


    # --------------------------------------------------
    # ROW 4
    # --------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        min_turnover = st.number_input(
            "Minimum Turnover (£)",
            min_value=0,
            value=0,
            step=100000
        )


    with col2:

        max_turnover = st.number_input(
            "Maximum Turnover (£)",
            min_value=0,
            value=0,
            step=100000
        )


    # --------------------------------------------------
    # SEARCH BUTTON
    # --------------------------------------------------

    search = st.form_submit_button(
        "SEARCH COMPANIES",
        type="primary"
    )


# ==================================================
# FILTER RESULTS
# ==================================================

if search:

    results = df.copy()


    # Company Name

    if company_name:

        results = results[
            results["Company Name"].str.contains(
                company_name,
                case=False,
                na=False
            )
        ]


    # Company Number

    if company_number:

        results = results[
            results["Company Number"].str.contains(
                company_number,
                case=False,
                na=False
            )
        ]


    # Company Status

    if company_status != "All":

        results = results[
            results["Company Status"] == company_status
        ]


    # SIC Code / Industry

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


    # Location / Postcode

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


    # Accountant

    if accountant:

        results = results[
            results["Accountant"].str.contains(
                accountant,
                case=False,
                na=False
            )
        ]


    # Auditor

    if auditor:

        results = results[
            results["Auditor"].str.contains(
                auditor,
                case=False,
                na=False
            )
        ]


    # Minimum Employees

    if min_employees > 0:

        results = results[
            results["Employees"] >= min_employees
        ]


    # Maximum Employees

    if max_employees > 0:

        results = results[
            results["Employees"] <= max_employees
        ]


    # Minimum Turnover

    if min_turnover > 0:

        results = results[
            results["Turnover"] >= min_turnover
        ]


    # Maximum Turnover

    if max_turnover > 0:

        results = results[
            results["Turnover"] <= max_turnover
        ]


    # Save results

    st.session_state["results"] = results


# ==================================================
# RESULTS
# ==================================================

if "results" in st.session_state:

    results = st.session_state["results"]


    st.markdown(
        "<hr>",
        unsafe_allow_html=True
    )


    # --------------------------------------------------
    # RESULT COUNT
    # --------------------------------------------------

    st.metric(
        "COMPANIES FOUND",
        f"{len(results):,}"
    )


    # --------------------------------------------------
    # FORMAT RESULTS FOR DISPLAY
    # --------------------------------------------------

    display_df = results.copy()


    display_df["Turnover"] = display_df[
        "Turnover"
    ].apply(
        lambda x: f"£{x:,.0f}"
    )


    # --------------------------------------------------
    # DISPLAY TABLE
    # --------------------------------------------------

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


    # --------------------------------------------------
    # CSV DOWNLOAD
    # --------------------------------------------------

    csv = results.to_csv(
        index=False
    ).encode("utf-8")


    st.download_button(
        label="DOWNLOAD SELECTION",
        data=csv,
        file_name="rebel_data_selection.csv",
        mime="text/csv"
    )


# ==================================================
# FOOTER
# ==================================================

st.markdown(
    "<hr>",
    unsafe_allow_html=True
)


st.markdown(
    '<div style="'
    'color:#999999;'
    'font-size:13px;'
    'padding-bottom:20px;'
    '">'
    '© Rebel Data | UK Business Intelligence'
    '</div>',
    unsafe_allow_html=True
)
