import streamlit as st
import pandas as pd
import pymssql


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
# DATABASE CONNECTION
# ==================================================

def get_connection():

    return pymssql.connect(
        server=st.secrets["database"]["server"],
        user=st.secrets["database"]["username"],
        password=st.secrets["database"]["password"],
        database=st.secrets["database"]["database"],
        port=1433,
        login_timeout=30,
        timeout=30
    )


# ==================================================
# ACCOUNTANT / AUDITOR FILTER VALUES
# ==================================================

@st.cache_data(ttl=3600)
def get_accountants():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT AccountantName
            FROM dbo.vw_RebelCompanies
            WHERE AccountantName IS NOT NULL
              AND LTRIM(RTRIM(AccountantName)) <> ''
            ORDER BY AccountantName
        """)

        values = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.close()

    finally:

        conn.close()

    return values


@st.cache_data(ttl=3600)
def get_auditors():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT AuditorName
            FROM dbo.vw_RebelCompanies
            WHERE AuditorName IS NOT NULL
              AND LTRIM(RTRIM(AuditorName)) <> ''
            ORDER BY AuditorName
        """)

        values = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.close()

    finally:

        conn.close()

    return values


# ==================================================
# DATABASE SEARCH
# ==================================================

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

            AddressLine1 AS [Address 1],
            AddressLine2 AS [Address 2],
            PostTown AS [Town],
            County AS [County],
            PostCode AS [Postcode],

            CompanyCategory AS [Company Category],
            CompanyStatus AS [Company Status],

            IncorporationDate AS [Incorporation Date],

            Employees AS [Employees],

            SIC1 AS [SIC 1],
            SIC2 AS [SIC 2],
            SIC3 AS [SIC 3],
            SIC4 AS [SIC 4],

            AccountsCategory AS [Accounts Category],
            AccountsLastMadeUpDate AS [Accounts Last Made Up],

            AccountantName AS [Accountant],
            AuditorName AS [Auditor]

        FROM dbo.vw_RebelCompanies

        WHERE 1 = 1
    """

    params = []


    # COMPANY NAME

    if company_name:

        sql += """
            AND CompanyName LIKE %s
        """

        params.append(
            f"%{company_name}%"
        )


    # COMPANY NUMBER

    if company_number:

        sql += """
            AND CompanyNumber LIKE %s
        """

        params.append(
            f"%{company_number}%"
        )


    # COMPANY STATUS

    if company_status != "All":

        sql += """
            AND CompanyStatus = %s
        """

        params.append(
            company_status
        )


    # SIC

    if sic:

        sql += """
            AND
            (
                SIC1 LIKE %s
                OR SIC2 LIKE %s
                OR SIC3 LIKE %s
                OR SIC4 LIKE %s
            )
        """

        sic_search = f"%{sic}%"

        params.extend(
            [
                sic_search,
                sic_search,
                sic_search,
                sic_search
            ]
        )


    # LOCATION

    if location:

        sql += """
            AND
            (
                PostTown LIKE %s
                OR County LIKE %s
                OR PostCode LIKE %s
            )
        """

        location_search = f"%{location}%"

        params.extend(
            [
                location_search,
                location_search,
                location_search
            ]
        )


    # ACCOUNTANT

    if accountant != "All":

        sql += """
            AND AccountantName = %s
        """

        params.append(
            accountant
        )


    # AUDITOR

    if auditor != "All":

        sql += """
            AND AuditorName = %s
        """

        params.append(
            auditor
        )


    # MIN EMPLOYEES

    if min_employees > 0:

        sql += """
            AND Employees >= %s
        """

        params.append(
            min_employees
        )


    # MAX EMPLOYEES

    if max_employees > 0:

        sql += """
            AND Employees <= %s
        """

        params.append(
            max_employees
        )


    sql += """
        ORDER BY CompanyName
    """


    # RUN QUERY

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            sql,
            tuple(params)
        )

        rows = cursor.fetchall()

        columns = [
            column[0]
            for column in cursor.description
        ]

        results = pd.DataFrame(
            rows,
            columns=columns
        )

        cursor.close()

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

    col1, col2 = st.columns(
        [4, 1]
    )

    with col1:

        st.markdown(
            """
            <div class="rebel-logo">
                <span class="rebel-green">Rebel</span>
                <span class="rebel-white"> Data</span>
            </div>

            <div class="rebel-subtitle">
                UK Business Intelligence
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        if show_logout:

            if st.session_state["client"]:

                st.markdown(
                    f"""
                    <div style="
                        text-align:right;
                        color:white;
                        font-size:14px;
                        margin-bottom:8px;
                    ">

                        {st.session_state["name"]}

                        <br>

                        <span style="
                            color:#8bd02f;
                        ">
                            {st.session_state["client"]}
                        </span>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if st.button(
                "LOG OUT"
            ):

                st.session_state[
                    "authenticated"
                ] = False

                st.session_state[
                    "username"
                ] = None

                st.session_state[
                    "name"
                ] = None

                st.session_state[
                    "client"
                ] = None

                if "results" in st.session_state:

                    del st.session_state[
                        "results"
                    ]

                st.rerun()

        else:

            st.markdown(
                """
                <div style="
                    text-align:right;
                    color:#8bd02f;
                    font-size:14px;
                    font-weight:800;
                    padding-top:12px;
                ">
                    CLIENT PORTAL
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown(
        "<hr>",
        unsafe_allow_html=True
    )


# ==================================================
# LOGIN SCREEN
# ==================================================

if not st.session_state[
    "authenticated"
]:

    show_header()

    st.markdown(
        """
        <div class="hero-title">
            Welcome to Rebel Data.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero-subtitle">
            Sign in to access the Rebel Data client portal.
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1, 1.3, 1]
    )

    with col2:

        with st.form(
            "login_form"
        ):

            username = st.text_input(
                "Username"
            )

            password = st.text_input(
                "Password",
                type="password"
            )

            login_button = (
                st.form_submit_button(
                    "SIGN IN"
                )
            )

            if login_button:

                users = st.secrets[
                    "users"
                ]

                if username in users:

                    user = users[
                        username
                    ]

                    if (
                        password
                        == user["password"]
                    ):

                        st.session_state[
                            "authenticated"
                        ] = True

                        st.session_state[
                            "username"
                        ] = username

                        st.session_state[
                            "name"
                        ] = user["name"]

                        st.session_state[
                            "client"
                        ] = user["client"]

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

show_header(
    show_logout=True
)

st.markdown(
    """
    <div class="hero-title">
        Find the businesses that matter.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero-subtitle">
        Search and select UK companies using Rebel Data.
    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# LOAD SEARCHABLE FILTER VALUES
# ==================================================

try:

    accountant_options = get_accountants()
    auditor_options = get_auditors()

except Exception as e:

    st.error(
        "Unable to load Accountant and Auditor lists."
    )

    st.exception(e)

    accountant_options = []
    auditor_options = []


# ==================================================
# COMPANY SEARCH
# ==================================================

st.markdown(
    """
    <div class="section-title">
        Company Search
    </div>
    """,
    unsafe_allow_html=True
)


with st.form(
    "company_search_form"
):

    # ROW 1

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


    # ROW 2

    col1, col2, col3 = st.columns(3)

    with col1:

        sic = st.text_input(
            "SIC Code / Industry",
            placeholder="e.g. 69201"
        )

    with col2:

        location = st.text_input(
            "Location / Postcode",
            placeholder="e.g. GL or Gloucester"
        )

    with col3:

        accountant = st.selectbox(
            "Accountant",
            ["All"] + accountant_options,
            index=0
        )


    # ROW 3

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

        auditor = st.selectbox(
            "Auditor",
            ["All"] + auditor_options,
            index=0
        )


    search = (
        st.form_submit_button(
            "SEARCH COMPANIES"
        )
    )


# ==================================================
# SEARCH DATABASE
# ==================================================

if search:

    no_filters = (
        not company_name
        and not company_number
        and company_status == "All"
        and not sic
        and not location
        and accountant == "All"
        and auditor == "All"
        and min_employees == 0
        and max_employees == 0
    )

    if no_filters:

        st.warning(
            "Enter at least one search criterion."
        )

    elif (
        max_employees > 0
        and min_employees > max_employees
    ):

        st.warning(
            "Maximum Employees must be greater than or equal to Minimum Employees."
        )

    else:

        try:

            with st.spinner(
                "Searching Rebel Data..."
            ):

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

            st.session_state[
                "results"
            ] = results

        except Exception as e:

            st.error(
                "Unable to search the Rebel Data database."
            )

            st.exception(e)


# ==================================================
# RESULTS
# ==================================================

if "results" in st.session_state:

    results = st.session_state[
        "results"
    ]

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

    if len(results) > 0:

        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
        )

        csv = results.to_csv(
            index=False
        ).encode(
            "utf-8"
        )

        st.download_button(
            label="DOWNLOAD SELECTION",
            data=csv,
            file_name="rebel_data_selection.csv",
            mime="text/csv"
        )

    else:

        st.info(
            "No companies matched your search."
        )


# ==================================================
# FOOTER
# ==================================================

st.markdown(
    "<hr>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="
        color:#999999;
        font-size:13px;
        padding-bottom:20px;
    ">
        © Rebel Data | UK Business Intelligence
    </div>
    """,
    unsafe_allow_html=True
)
