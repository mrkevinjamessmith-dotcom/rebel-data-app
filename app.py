import streamlit as st
import pandas as pd
import pymssql
import math
import time


# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="Rebel Data",
    page_icon="🟩",
    layout="wide"
)

PAGE_SIZE = 100
DOWNLOAD_LIMIT = 1000


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

    .detail-title {
        font-size: 26px;
        font-weight: 800;
        color: white;
        margin-top: 20px;
        margin-bottom: 4px;
    }

    .detail-subtitle {
        color: #8bd02f;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 18px;
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

    max_attempts = 6

    for attempt in range(1, max_attempts + 1):

        try:

            return pymssql.connect(
                server=st.secrets["database"]["server"],
                user=st.secrets["database"]["username"],
                password=st.secrets["database"]["password"],
                database=st.secrets["database"]["database"],
                port=1433,
                login_timeout=60,
                timeout=60
            )

        except pymssql.OperationalError:

            if attempt == max_attempts:
                raise

            time.sleep(10)


# ==================================================
# ACCOUNTANT / AUDITOR FILTER VALUES
# ==================================================

@st.cache_data(ttl=86400)
def get_accountants():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT AccountantName
            FROM dbo.Rebel_Accountants
            ORDER BY AccountantName
            """
        )

        values = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.close()

    finally:

        conn.close()

    return values


@st.cache_data(ttl=86400)
def get_auditors():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT AuditorName
            FROM dbo.Rebel_Auditors
            ORDER BY AuditorName
            """
        )

        values = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.close()

    finally:

        conn.close()

    return values


# ==================================================
# BUILD SEARCH WHERE CLAUSE
# ==================================================

def build_filters(search_params):

    sql = ""
    params = []

    company_name = search_params["company_name"]
    company_number = search_params["company_number"]
    company_status = search_params["company_status"]
    sic = search_params["sic"]
    location = search_params["location"]
    accountant = search_params["accountant"]
    auditor = search_params["auditor"]
    min_employees = search_params["min_employees"]
    max_employees = search_params["max_employees"]


    # Company name

    if company_name:

        sql += """
            AND CompanyName LIKE %s
        """

        params.append(
            f"%{company_name}%"
        )


    # Company number

    if company_number:

        sql += """
            AND CompanyNumber LIKE %s
        """

        params.append(
            f"%{company_number}%"
        )


    # Status

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


    # Location

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


    # Accountant

    if accountant != "All":

        sql += """
            AND AccountantName = %s
        """

        params.append(
            accountant
        )


    # Auditor

    if auditor != "All":

        sql += """
            AND AuditorName = %s
        """

        params.append(
            auditor
        )


    # Minimum employees

    if min_employees > 0:

        sql += """
            AND TRY_CONVERT(INT, Employees) >= %s
        """

        params.append(
            min_employees
        )


    # Maximum employees

    if max_employees > 0:

        sql += """
            AND TRY_CONVERT(INT, Employees) <= %s
        """

        params.append(
            max_employees
        )


    return sql, params


# ==================================================
# TRUE RESULT COUNT
# ==================================================

def count_companies(search_params):

    filter_sql, params = build_filters(
        search_params
    )

    sql = f"""
        SELECT COUNT_BIG(*)
        FROM dbo.vw_RebelCompanies
        WHERE 1 = 1
        {filter_sql}
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            sql,
            tuple(params)
        )

        result = cursor.fetchone()[0]

        cursor.close()

    finally:
        conn.close()

    return int(result)


# ==================================================
# PAGINATED SEARCH
# ==================================================

def search_companies(
    search_params,
    page_number
):

    filter_sql, params = build_filters(
        search_params
    )

    offset_rows = (
        page_number - 1
    ) * PAGE_SIZE

    sql = f"""
        SELECT

            CompanyNumber AS [Company Number],
            CompanyName AS [Company Name],

            PostTown AS [Town],
            County AS [County],
            PostCode AS [Postcode],

            CompanyStatus AS [Company Status],
            CompanyCategory AS [Company Category],

            TRY_CONVERT(INT, Employees) AS [Employees],

            SIC1 AS [SIC 1],

            AccountantName AS [Accountant],
            AuditorName AS [Auditor]

        FROM dbo.vw_RebelCompanies

        WHERE 1 = 1

        {filter_sql}

        ORDER BY
            CompanyName,
            CompanyNumber

        OFFSET %s ROWS

        FETCH NEXT %s ROWS ONLY
    """

    params.extend(
        [
            offset_rows,
            PAGE_SIZE
        ]
    )

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
# DOWNLOAD FIRST 1,000 MATCHES
# ==================================================

def get_download_data(
    search_params
):

    filter_sql, params = build_filters(
        search_params
    )

    sql = f"""
        SELECT TOP {DOWNLOAD_LIMIT}

            CompanyNumber AS [Company Number],
            CompanyName AS [Company Name],

            AddressLine1 AS [Address 1],
            AddressLine2 AS [Address 2],
            PostTown AS [Town],
            County AS [County],
            Country AS [Country],
            PostCode AS [Postcode],

            CompanyCategory AS [Company Category],
            CompanyStatus AS [Company Status],
            CountryOfOrigin AS [Country Of Origin],

            IncorporationDate AS [Incorporation Date],

            TRY_CONVERT(INT, Employees) AS [Employees],

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

        {filter_sql}

        ORDER BY
            CompanyName,
            CompanyNumber
    """

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
# COMPANY DETAIL
# ==================================================

def get_company_detail(
    company_number
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT TOP 1

                CompanyNumber,
                CompanyName,

                POBox,
                AddressLine1,
                AddressLine2,
                PostTown,
                County,
                Country,
                PostCode,

                CompanyCategory,
                CompanyStatus,
                CountryOfOrigin,

                DissolutionDate,
                IncorporationDate,

                AccountsRefDay,
                AccountsRefMonth,
                AccountsNextDueDate,
                AccountsLastMadeUpDate,
                AccountsCategory,

                ReturnsNextDueDate,
                ReturnsLastMadeUpDate,

                MortgagesNumCharges,
                MortgagesOutstanding,
                MortgagesPartSatisfied,
                MortgagesSatisfied,

                SIC1,
                SIC2,
                SIC3,
                SIC4,

                NumGeneralPartners,
                NumLimitedPartners,

                ConfStmtNextDueDate,
                ConfStmtLastMadeUpDate,

                TRY_CONVERT(INT, Employees) AS Employees,

                AuditorName,
                AccountantName

            FROM dbo.vw_RebelCompanies

            WHERE CompanyNumber = %s
            """,
            (company_number,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [
            column[0]
            for column in cursor.description
        ]

        detail = dict(
            zip(
                columns,
                row
            )
        )

        cursor.close()

    finally:
        conn.close()

    return detail


# ==================================================
# DISPLAY VALUE
# ==================================================

def display_value(value):

    if value is None:
        return "Not available"

    if isinstance(
        value,
        pd.Timestamp
    ):
        return value.strftime(
            "%d/%m/%Y"
        )

    if hasattr(
        value,
        "strftime"
    ):
        try:
            return value.strftime(
                "%d/%m/%Y"
            )
        except:
            pass

    text = str(value).strip()

    if text == "":
        return "Not available"

    return text


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "authenticated": False,
    "username": None,
    "name": None,
    "client": None,
    "search_params": None,
    "results": None,
    "result_count": 0,
    "page_number": 1
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# HEADER
# ==================================================

def show_header(
    show_logout=False
):

    col1, col2 = st.columns(
        [4, 1]
    )

    with col1:

        st.markdown(
            """
            <div class="rebel-logo">
                <span class="rebel-green">
                    Rebel
                </span>
                <span class="rebel-white">
                    Data
                </span>
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

                name = st.session_state[
                    "name"
                ]

                client = st.session_state[
                    "client"
                ]

                st.markdown(
                    f"""<div style="text-align:right; color:white; font-size:14px; margin-bottom:8px;">
{name}<br>
<span style="color:#8bd02f; font-weight:700;">{client}</span>
</div>""",
                    unsafe_allow_html=True
                )

            if st.button(
                "LOG OUT",
                use_container_width=True
            ):

                for key in defaults:

                    st.session_state[
                        key
                    ] = defaults[key]

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
# LOAD ACCOUNTANTS / AUDITORS
# ==================================================

try:

    accountant_options = (
        get_accountants()
    )

    auditor_options = (
        get_auditors()
    )

except Exception:

    st.warning(
        "Accountant and Auditor lists are temporarily unavailable. You can still search using the other filters."
    )

    accountant_options = []
    auditor_options = []


# ==================================================
# SEARCH FORM
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

    col1, col2, col3 = st.columns(
        3
    )

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

    col1, col2, col3 = st.columns(
        3
    )

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
            ["All"]
            + accountant_options
        )


    # ROW 3

    col1, col2, col3 = st.columns(
        3
    )

    with col1:

        min_employees = (
            st.number_input(
                "Minimum Employees",
                min_value=0,
                value=0,
                step=1
            )
        )

    with col2:

        max_employees = (
            st.number_input(
                "Maximum Employees",
                min_value=0,
                value=0,
                step=1
            )
        )

    with col3:

        auditor = st.selectbox(
            "Auditor",
            ["All"]
            + auditor_options
        )


    search = (
        st.form_submit_button(
            "SEARCH COMPANIES"
        )
    )


# ==================================================
# RUN NEW SEARCH
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
        and min_employees
        > max_employees
    ):

        st.warning(
            "Maximum Employees must be greater than or equal to Minimum Employees."
        )

    else:

        search_params = {
            "company_name": company_name,
            "company_number": company_number,
            "company_status": company_status,
            "sic": sic,
            "location": location,
            "accountant": accountant,
            "auditor": auditor,
            "min_employees": min_employees,
            "max_employees": max_employees
        }

        try:

            with st.spinner(
                "Searching Rebel Data..."
            ):

                result_count = (
                    count_companies(
                        search_params
                    )
                )

                results = (
                    search_companies(
                        search_params,
                        1
                    )
                )

            st.session_state[
                "search_params"
            ] = search_params

            st.session_state[
                "result_count"
            ] = result_count

            st.session_state[
                "page_number"
            ] = 1

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

if (
    st.session_state["results"]
    is not None
):

    results = st.session_state[
        "results"
    ]

    result_count = (
        st.session_state[
            "result_count"
        ]
    )

    page_number = (
        st.session_state[
            "page_number"
        ]
    )

    st.markdown(
        "<hr>",
        unsafe_allow_html=True
    )


    # ----------------------------------------------
    # TRUE RESULT COUNT
    # ----------------------------------------------

    metric1, metric2, metric3 = (
        st.columns(
            [1, 1, 2]
        )
    )

    total_pages = max(
        1,
        math.ceil(
            result_count
            / PAGE_SIZE
        )
    )

    start_record = (
        ((page_number - 1)
         * PAGE_SIZE)
        + 1
        if result_count > 0
        else 0
    )

    end_record = min(
        page_number
        * PAGE_SIZE,
        result_count
    )


    with metric1:

        st.metric(
            "COMPANIES FOUND",
            f"{result_count:,}"
        )


    with metric2:

        st.metric(
            "PAGE",
            f"{page_number:,} of {total_pages:,}"
        )


    with metric3:

        if result_count > 0:

            st.markdown(
                f"""
                <div style="
                    color:#cfcfcf;
                    padding-top:28px;
                    font-size:14px;
                ">
                    Showing companies
                    <b style="color:white;">
                    {start_record:,}–{end_record:,}
                    </b>
                    of
                    <b style="color:#8bd02f;">
                    {result_count:,}
                    </b>
                </div>
                """,
                unsafe_allow_html=True
            )


    # ----------------------------------------------
    # RESULTS TABLE
    # ----------------------------------------------

    if len(results) > 0:

        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True,
            height=500
        )


        # ------------------------------------------
        # PAGINATION
        # ------------------------------------------

        previous_col, page_col, next_col = (
            st.columns(
                [1, 3, 1]
            )
        )

        with previous_col:

            previous_clicked = (
                st.button(
                    "← PREVIOUS",
                    disabled=(
                        page_number <= 1
                    ),
                    use_container_width=True
                )
            )

        with page_col:

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    padding-top:10px;
                    color:#cfcfcf;
                ">
                    Page
                    <b style="color:white;">
                    {page_number:,}
                    </b>
                    of
                    <b style="color:#8bd02f;">
                    {total_pages:,}
                    </b>
                </div>
                """,
                unsafe_allow_html=True
            )

        with next_col:

            next_clicked = (
                st.button(
                    "NEXT →",
                    disabled=(
                        page_number
                        >= total_pages
                    ),
                    use_container_width=True
                )
            )


        # Previous page

        if previous_clicked:

            new_page = (
                page_number - 1
            )

            with st.spinner(
                "Loading previous page..."
            ):

                new_results = (
                    search_companies(
                        st.session_state[
                            "search_params"
                        ],
                        new_page
                    )
                )

            st.session_state[
                "page_number"
            ] = new_page

            st.session_state[
                "results"
            ] = new_results

            st.rerun()


        # Next page

        if next_clicked:

            new_page = (
                page_number + 1
            )

            with st.spinner(
                "Loading next page..."
            ):

                new_results = (
                    search_companies(
                        st.session_state[
                            "search_params"
                        ],
                        new_page
                    )
                )

            st.session_state[
                "page_number"
            ] = new_page

            st.session_state[
                "results"
            ] = new_results

            st.rerun()


        # ------------------------------------------
        # DOWNLOAD
        # ------------------------------------------

        st.markdown(
            "<br>",
            unsafe_allow_html=True
        )

        with st.expander(
            "Download matching companies"
        ):

            if (
                result_count
                > DOWNLOAD_LIMIT
            ):

                st.write(
                    f"Your search found {result_count:,} companies. "
                    f"The MVP currently allows downloads of the first "
                    f"{DOWNLOAD_LIMIT:,} matching companies."
                )

            else:

                st.write(
                    f"Download all {result_count:,} matching companies."
                )

            if st.button(
                "PREPARE DOWNLOAD"
            ):

                with st.spinner(
                    "Preparing download..."
                ):

                    download_data = (
                        get_download_data(
                            st.session_state[
                                "search_params"
                            ]
                        )
                    )

                    csv = (
                        download_data
                        .to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8"
                        )
                    )

                st.download_button(
                    label="DOWNLOAD CSV",
                    data=csv,
                    file_name=(
                        "rebel_data_selection.csv"
                    ),
                    mime="text/csv"
                )


        # ------------------------------------------
        # COMPANY DETAIL
        # ------------------------------------------

        st.markdown(
            "<hr>",
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="section-title">
                Company Details
            </div>
            """,
            unsafe_allow_html=True
        )

        company_choices = {
            (
                f"{row['Company Name']} "
                f"({row['Company Number']})"
            ):
            row["Company Number"]

            for _, row
            in results.iterrows()
        }

        detail_choice = (
            st.selectbox(
                "Select a company from this page",
                [
                    "Select a company..."
                ]
                + list(
                    company_choices.keys()
                )
            )
        )

        if (
            detail_choice
            != "Select a company..."
        ):

            selected_number = (
                company_choices[
                    detail_choice
                ]
            )

            try:

                with st.spinner(
                    "Loading company details..."
                ):

                    detail = (
                        get_company_detail(
                            selected_number
                        )
                    )

                if detail:

                    st.markdown(
                        f"""
                        <div class="detail-title">
                            {display_value(detail["CompanyName"])}
                        </div>

                        <div class="detail-subtitle">
                            Company Number:
                            {display_value(detail["CompanyNumber"])}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                    # ----------------------------------
                    # BASIC COMPANY DETAILS
                    # ----------------------------------

                    st.subheader(
                        "Company"
                    )

                    col1, col2, col3, col4 = (
                        st.columns(4)
                    )

                    col1.metric(
                        "Status",
                        display_value(
                            detail[
                                "CompanyStatus"
                            ]
                        )
                    )

                    col2.metric(
                        "Employees",
                        display_value(
                            detail[
                                "Employees"
                            ]
                        )
                    )

                    col3.metric(
                        "Category",
                        display_value(
                            detail[
                                "CompanyCategory"
                            ]
                        )
                    )

                    col4.metric(
                        "Country of Origin",
                        display_value(
                            detail[
                                "CountryOfOrigin"
                            ]
                        )
                    )


                    # ----------------------------------
                    # IMPORTANT DATES
                    # ----------------------------------

                    st.subheader(
                        "Important Dates"
                    )

                    col1, col2, col3 = (
                        st.columns(3)
                    )

                    col1.write(
                        "**Incorporated**"
                    )

                    col1.write(
                        display_value(
                            detail[
                                "IncorporationDate"
                            ]
                        )
                    )

                    col2.write(
                        "**Accounts Last Made Up**"
                    )

                    col2.write(
                        display_value(
                            detail[
                                "AccountsLastMadeUpDate"
                            ]
                        )
                    )

                    col3.write(
                        "**Confirmation Statement Last Made Up**"
                    )

                    col3.write(
                        display_value(
                            detail[
                                "ConfStmtLastMadeUpDate"
                            ]
                        )
                    )


                    # ----------------------------------
                    # ADDRESS
                    # ----------------------------------

                    st.subheader(
                        "Registered Address"
                    )

                    address_parts = [
                        detail["POBox"],
                        detail["AddressLine1"],
                        detail["AddressLine2"],
                        detail["PostTown"],
                        detail["County"],
                        detail["Country"],
                        detail["PostCode"]
                    ]

                    address_parts = [
                        str(x).strip()
                        for x
                        in address_parts
                        if x is not None
                        and str(x).strip()
                        != ""
                    ]

                    st.write(
                        ", ".join(
                            address_parts
                        )
                        if address_parts
                        else
                        "Not available"
                    )


                    # ----------------------------------
                    # INDUSTRY
                    # ----------------------------------

                    st.subheader(
                        "Industry"
                    )

                    sic_values = [
                        detail["SIC1"],
                        detail["SIC2"],
                        detail["SIC3"],
                        detail["SIC4"]
                    ]

                    sic_values = [
                        str(x).strip()
                        for x
                        in sic_values
                        if x is not None
                        and str(x).strip()
                        != ""
                    ]

                    if sic_values:

                        for sic_value in sic_values:
                            st.write(
                                f"• {sic_value}"
                            )

                    else:

                        st.write(
                            "No SIC information available."
                        )


                    # ----------------------------------
                    # PROFESSIONAL ADVISERS
                    # ----------------------------------

                    st.subheader(
                        "Professional Advisers"
                    )

                    col1, col2 = (
                        st.columns(2)
                    )

                    with col1:

                        st.write(
                            "**Accountant**"
                        )

                        st.write(
                            display_value(
                                detail[
                                    "AccountantName"
                                ]
                            )
                        )

                    with col2:

                        st.write(
                            "**Auditor**"
                        )

                        st.write(
                            display_value(
                                detail[
                                    "AuditorName"
                                ]
                            )
                        )


                    # ----------------------------------
                    # ACCOUNTS
                    # ----------------------------------

                    st.subheader(
                        "Accounts"
                    )

                    col1, col2, col3 = (
                        st.columns(3)
                    )

                    with col1:

                        st.write(
                            "**Accounts Category**"
                        )

                        st.write(
                            display_value(
                                detail[
                                    "AccountsCategory"
                                ]
                            )
                        )

                    with col2:

                        st.write(
                            "**Next Accounts Due**"
                        )

                        st.write(
                            display_value(
                                detail[
                                    "AccountsNextDueDate"
                                ]
                            )
                        )

                    with col3:

                        st.write(
                            "**Last Accounts**"
                        )

                        st.write(
                            display_value(
                                detail[
                                    "AccountsLastMadeUpDate"
                                ]
                            )
                        )


                    # ----------------------------------
                    # MORTGAGES
                    # ----------------------------------

                    st.subheader(
                        "Mortgages"
                    )

                    col1, col2, col3, col4 = (
                        st.columns(4)
                    )

                    col1.metric(
                        "Charges",
                        display_value(
                            detail[
                                "MortgagesNumCharges"
                            ]
                        )
                    )

                    col2.metric(
                        "Outstanding",
                        display_value(
                            detail[
                                "MortgagesOutstanding"
                            ]
                        )
                    )

                    col3.metric(
                        "Part Satisfied",
                        display_value(
                            detail[
                                "MortgagesPartSatisfied"
                            ]
                        )
                    )

                    col4.metric(
                        "Satisfied",
                        display_value(
                            detail[
                                "MortgagesSatisfied"
                            ]
                        )
                    )

            except Exception as e:

                st.error(
                    "Unable to load company details."
                )

                st.exception(e)

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
