import streamlit as st
import pandas as pd
import pyodbc

# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="Rebel Data",
    page_icon="🟩",
    layout="wide"
)

# ==================================================
# BRANDING / CSS
# ==================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #3d3d3f;
        color: white;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 3rem !important;
        max-width: 1450px;
    }

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

    .section-title {
        font-size: 28px;
        font-weight: 800;
        color: white;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    label {
        color: white !important;
        font-weight: 600 !important;
    }

    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stButton"] button {
        background-color: #8bd02f !important;
        color: #222222 !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: 800 !important;
    }

    div[data-testid="stDownloadButton"] button {
        background-color: #8bd02f !important;
        color: #222222 !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricValue"] {
        color: #8bd02f !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricLabel"] {
        color: white !important;
    }

    hr {
        border-color: #5a5a5c !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ==================================================
# DATABASE
# ==================================================

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={st.secrets['database']['server']};"
        f"DATABASE={st.secrets['database']['database']};"
        f"UID={st.secrets['database']['username']};"
        f"PWD={st.secrets['database']['password']};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )


def search_companies(
    company_name,
    company_number,
    company_status,
    sic,
    location,
    accountant,
    auditor,
    min_employees,
    max_employees
):

    sql = """
    SELECT TOP 1000
        CompanyNumber AS [Company Number],
        CompanyName AS [Company Name],
        CompanyStatus AS [Company Status],
        SIC1 AS [SIC 1],
        SIC2 AS [SIC 2],
        SIC3 AS [SIC 3],
        SIC4 AS [SIC 4],
        PostTown AS [Town],
        County,
        PostCode AS [Postcode],
        Employees,
        AccountantName AS [Accountant],
        AuditorName AS [Auditor]
    FROM dbo.vw_RebelCompanies
    WHERE 1 = 1
    """

    params = []

    if company_name:
        sql += " AND CompanyName LIKE ?"
        params.append(f"%{company_name}%")

    if company_number:
        sql += " AND CompanyNumber LIKE ?"
        params.append(f"%{company_number}%")

    if company_status != "All":
        sql += " AND CompanyStatus = ?"
        params.append(company_status)

    if sic:
        sql += """
        AND (
            SIC1 LIKE ?
            OR SIC2 LIKE ?
            OR SIC3 LIKE ?
            OR SIC4 LIKE ?
        )
        """
        sic_search = f"%{sic}%"
        params.extend([
            sic_search,
            sic_search,
            sic_search,
            sic_search
        ])

    if location:
        sql += """
        AND (
            PostTown LIKE ?
            OR County LIKE ?
            OR PostCode LIKE ?
        )
        """
        location_search = f"%{location}%"
        params.extend([
            location_search,
            location_search,
            location_search
        ])

    if accountant:
        sql += " AND AccountantName LIKE ?"
        params.append(f"%{accountant}%")

    if auditor:
        sql += " AND AuditorName LIKE ?"
        params.append(f"%{auditor}%")

    if min_employees > 0:
        sql += " AND Employees >= ?"
        params.append(min_employees)

    if max_employees > 0:
        sql += " AND Employees <= ?"
        params.append(max_employees)

    sql += " ORDER BY CompanyName"

    conn = get_connection()

    try:
        results = pd.read_sql_query(
            sql,
            conn,
            params=params
        )
    finally:
        conn.close()

    return results


# ==================================================
# SESSION STATE
# ==================================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "username" not in st.session_state:
    st.session_state["username"] = None

if "name" not in st.session_state:
    st.session_state["name"] = None

if "client" not in st.session_state:
    st.session_state["client"] = None


# ==================================================
# HEADER
# ==================================================

def show_header(show_logout=False):

    col1, col2 = st.columns([4, 1])

    with col1:

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

    with col2:

        if show_logout:

            if st.session_state["client"]:

                st.markdown(
                    f'<div style="'
                    f'text-align:right;'
                    f'color:white;'
                    f'font-size:14px;'
                    f'margin-bottom:8px;'
                    f'">'
                    f'{st.session_state["name"]}<br>'
                    f'<span style="color:#8bd02f;">'
                    f'{st.session_state["client"]}'
                    f'</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            if st.button("LOG OUT"):

                st.session_state["authenticated"] = False
                st.session_state["username"] = None
                st.session_state["name"] = None
                st.session_state["client"] = None

                if "results" in st.session_state:
                    del st.session_state["results"]

                st.rerun()

        else:

            st.markdown(
                '<div style="'
                'text-align:right;'
                'color:#8bd02f;'
                'font-size:14px;'
                'font-weight:800;'
                'padding-top:12px;'
                '">'
                'CLIENT PORTAL'
                '</div>',
                unsafe_allow_html=True
            )

    st.markdown(
        "<hr>",
        unsafe_allow_html=True
    )


# ==================================================
# LOGIN SCREEN
# ==================================================

if not st.session_state["authenticated"]:

    show_header()

    st.markdown(
        '<div class="hero-title">'
        'Welcome to Rebel Data.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="hero-subtitle">'
        'Sign in to access the Rebel Data client portal.'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.3, 1])

    with col2:

        with st.form("login_form"):

            username = st.text_input("Username")

            password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "SIGN IN"
            )

            if login_button:

                users = st.secrets["users"]

                if username in users:

                    user = users[username]

                    if password == user["password"]:

                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["name"] = user["name"]
                        st.session_state["client"] = user["client"]

                        st.rerun()

                    else:

                        st.error(
                            "Incorrect username or password."
                        )

                else:

                    st.error(
                        "Incorrect username or password."
                    )

    st.stop()


# ==================================================
# MAIN APP
# ==================================================

show_header(show_logout=True)

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
# COMPANY SEARCH
# ==================================================

st.markdown(
    '<div class="section-title">'
    'Company Search'
    '</div>',
    unsafe_allow_html=True
)

with st.form("company_search_form"):

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

    col1, col2, col3 = st.columns(3)

    with col1:
        sic = st.text_input(
            "SIC Code",
            placeholder="e.g. 69201"
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

    search = st.form_submit_button(
        "SEARCH COMPANIES"
    )


# ==================================================
# SEARCH AZURE
# ==================================================

if search:

    try:

        with st.spinner("Searching Rebel Data..."):

            results = search_companies(
                company_name,
                company_number,
                company_status,
                sic,
                location,
                accountant,
                auditor,
                min_employees,
                max_employees
            )

        st.session_state["results"] = results

    except Exception as e:

        st.error(
            "Unable to search the Rebel Data database."
        )

        st.exception(e)


# ==================================================
# RESULTS
# ==================================================

if "results" in st.session_state:

    results = st.session_state["results"]

    st.markdown(
        "<hr>",
        unsafe_allow_html=True
    )

    st.metric(
        "COMPANIES FOUND",
        f"{len(results):,}"
    )

    if len(results) == 1000:

        st.info(
            "Showing the first 1,000 matching companies. "
            "Refine your search to narrow the results."
        )

    st.dataframe(
        results,
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
