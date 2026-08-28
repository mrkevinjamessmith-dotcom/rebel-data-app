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
# USER ACTIVITY LOGGING
# ==================================================

def log_activity(
    activity_type,
    search_params=None,
    result_count=None,
    company_viewed=None,
    download_count=None
):

    """
    Write a user activity event to dbo.Rebel_UserActivity.

    Logging is deliberately non-blocking. If the audit insert fails,
    the client-facing application will continue to work.
    """

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        login_username = st.session_state.get("username")
        display_name = st.session_state.get("name")
        client = st.session_state.get("client")

        company_name_search = None
        company_number_search = None
        company_status = None
        sic = None
        location = None
        accountant = None
        auditor = None
        min_employees = None
        max_employees = None

        if search_params:

            company_name_search = search_params.get("company_name")
            company_number_search = search_params.get("company_number")
            company_status = search_params.get("company_status")
            sic = search_params.get("sic")
            location = search_params.get("location")
            accountant = search_params.get("accountant")
            auditor = search_params.get("auditor")
            min_employees = search_params.get("min_employees")
            max_employees = search_params.get("max_employees")

            # Store "All" as NULL in the audit table to keep the log cleaner.
            if company_status == "All":
                company_status = None

            if accountant == "All":
                accountant = None

            if auditor == "All":
                auditor = None

        cursor.execute(
            """
            INSERT INTO dbo.Rebel_UserActivity
            (
                LoginUsername,
                DisplayName,
                Client,
                ActivityType,
                CompanyNameSearch,
                CompanyNumberSearch,
                CompanyStatus,
                SIC,
                Location,
                Accountant,
                Auditor,
                MinEmployees,
                MaxEmployees,
                ResultCount,
                CompanyViewed,
                DownloadCount
            )
            VALUES
            (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                login_username,
                display_name,
                client,
                activity_type,
                company_name_search,
                company_number_search,
                company_status,
                sic,
                location,
                accountant,
                auditor,
                min_employees,
                max_employees,
                result_count,
                company_viewed,
                download_count
            )
        )

        conn.commit()

    except Exception:
        # Audit logging must never stop a user from using the app.
        pass

    finally:

        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass

        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


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
# ACCOUNTS COMPARISON
# ==================================================

def get_accounts_comparison(company_number):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT TOP 1 *
            FROM dbo.RD_AccountsComparison
            WHERE LTRIM(RTRIM(CRO)) = LTRIM(RTRIM(%s))
            """,
            (str(company_number),)
        )
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            return None
        columns = [column[0] for column in cursor.description]
        result = dict(zip(columns, row))
        cursor.close()
        return result
    finally:
        conn.close()


def to_number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_financial_value(value, value_type="currency"):
    number = to_number(value)
    if number is None:
        return "Not available"
    if value_type == "integer":
        return f"{number:,.0f}"
    return f"£{number:,.0f}"


def calculate_change_pct(latest, previous):
    latest_number = to_number(latest)
    previous_number = to_number(previous)
    if latest_number is None or previous_number is None or previous_number == 0:
        return None
    return ((latest_number - previous_number) / abs(previous_number)) * 100


def format_change(latest, previous):
    latest_number = to_number(latest)
    previous_number = to_number(previous)
    if latest_number is None or previous_number is None:
        return "Not available"
    difference = latest_number - previous_number
    pct = calculate_change_pct(latest_number, previous_number)
    if pct is None:
        return f"{difference:+,.0f}"
    return f"{difference:+,.0f} ({pct:+.1f}%)"


def build_financial_commentary(c):
    comments = []
    checks = [
        ("Turnover", "LatestTurnover", "PreviousTurnover"),
        ("Employee numbers", "LatestEmployees", "PreviousEmployees"),
        ("Profit before tax", "LatestProfitBeforeTax", "PreviousProfitBeforeTax"),
        ("Cash", "LatestCash", "PreviousCash"),
        ("Net assets", "LatestNetAssets", "PreviousNetAssets")
    ]

    for label, latest_field, previous_field in checks:
        pct = calculate_change_pct(c.get(latest_field), c.get(previous_field))
        if pct is None:
            continue
        if pct > 0:
            comments.append(f"{label} increased by {pct:.1f}%.")
        elif pct < 0:
            comments.append(f"{label} decreased by {abs(pct):.1f}%.")
        else:
            comments.append(f"{label} was unchanged.")

    if c.get("AccountantChanged") == 1:
        comments.append("The accountant changed between the two latest accounts.")
    if c.get("AuditorChanged") == 1:
        comments.append("The auditor changed between the two latest accounts.")

    return " ".join(comments) if comments else (
        "There is not enough comparable information to generate a meaningful trend summary."
    )


def show_accounts_comparison(c):
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Financial Comparison</div>',
        unsafe_allow_html=True
    )

    if c.get("PreviousAccountsPeriodEnd") is None:
        st.info(
            "Only one set of accounts is currently available for this company, "
            "so a year-on-year comparison cannot yet be shown."
        )
        return

    latest_period = display_value(c.get("LatestAccountsPeriodEnd"))
    previous_period = display_value(c.get("PreviousAccountsPeriodEnd"))

    st.markdown(
        f"""
        <div style="color:#cfcfcf;font-size:15px;margin-bottom:22px;">
            Latest accounts <b style="color:#8bd02f;">{latest_period}</b>
            &nbsp;&nbsp;vs&nbsp;&nbsp;
            previous accounts <b style="color:white;">{previous_period}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------
    # HEADLINE KPI CARDS
    # --------------------------------------------------

    kpis = [
        ("Turnover", "LatestTurnover", "PreviousTurnover", "currency"),
        ("Profit Before Tax", "LatestProfitBeforeTax", "PreviousProfitBeforeTax", "currency"),
        ("Cash", "LatestCash", "PreviousCash", "currency"),
        ("Employees", "LatestEmployees", "PreviousEmployees", "integer")
    ]

    available_kpis = [
        item for item in kpis
        if c.get(item[1]) is not None or c.get(item[2]) is not None
    ]

    if available_kpis:
        kpi_cols = st.columns(len(available_kpis))
        for col, (label, latest_field, previous_field, value_type) in zip(kpi_cols, available_kpis):
            latest = c.get(latest_field)
            previous = c.get(previous_field)
            pct = calculate_change_pct(latest, previous)

            if pct is not None:
                delta = f"{pct:+.1f}%"
            elif latest is not None and previous is None:
                delta = "No previous value"
            else:
                delta = None

            col.metric(
                label,
                format_financial_value(latest, value_type),
                delta=delta
            )

    # --------------------------------------------------
    # YEAR-ON-YEAR MOVEMENT - % CHANGE
    # This is deliberately percentage based so turnover does not dwarf profit.
    # --------------------------------------------------

    movement_metrics = [
        ("Turnover", "LatestTurnover", "PreviousTurnover"),
        ("Gross Profit", "LatestGrossProfit", "PreviousGrossProfit"),
        ("Operating Profit", "LatestOperatingProfit", "PreviousOperatingProfit"),
        ("Profit Before Tax", "LatestProfitBeforeTax", "PreviousProfitBeforeTax"),
        ("Profit After Tax", "LatestProfitAfterTax", "PreviousProfitAfterTax"),
        ("Cash", "LatestCash", "PreviousCash"),
        ("Net Assets", "LatestNetAssets", "PreviousNetAssets"),
        ("Employees", "LatestEmployees", "PreviousEmployees")
    ]

    movement_rows = []
    for label, latest_field, previous_field in movement_metrics:
        pct = calculate_change_pct(c.get(latest_field), c.get(previous_field))
        if pct is not None:
            movement_rows.append({"Metric": label, "Change": round(pct, 1)})

    if movement_rows:
        st.markdown("### Year-on-year movement")
        st.caption("Percentage change from the previous accounts. This makes differently-sized metrics easy to compare.")

        movement_df = pd.DataFrame(movement_rows)
        movement_spec = {
            "background": "#3d3d3f",
            "height": max(220, len(movement_rows) * 42),
            "mark": {"type": "bar", "cornerRadiusEnd": 4},
            "encoding": {
                "y": {
                    "field": "Metric",
                    "type": "nominal",
                    "sort": None,
                    "axis": {
                        "title": None,
                        "labelColor": "#ffffff",
                        "labelFontSize": 13,
                        "ticks": False,
                        "domain": False
                    }
                },
                "x": {
                    "field": "Change",
                    "type": "quantitative",
                    "axis": {
                        "title": "Change vs previous (%)",
                        "titleColor": "#cfcfcf",
                        "labelColor": "#cfcfcf",
                        "gridColor": "#555557",
                        "domain": False
                    }
                },
                "color": {
                    "condition": {"test": "datum.Change >= 0", "value": "#8bd02f"},
                    "value": "#ff6b6b"
                },
                "tooltip": [
                    {"field": "Metric", "type": "nominal"},
                    {"field": "Change", "type": "quantitative", "format": "+.1f", "title": "Change (%)"}
                ]
            },
            "config": {
                "view": {"stroke": None},
                "axis": {"labelFont": "sans-serif", "titleFont": "sans-serif"}
            }
        }
        st.vega_lite_chart(movement_df, movement_spec, use_container_width=True)

    # --------------------------------------------------
    # CLEAN MINI COMPARISON CHARTS
    # Each metric gets its own scale, avoiding giant bars and unreadable charts.
    # --------------------------------------------------

    def render_two_period_chart(title, latest_field, previous_field, value_type="currency"):
        latest = to_number(c.get(latest_field))
        previous = to_number(c.get(previous_field))
        if latest is None and previous is None:
            return False

        chart_rows = []
        if previous is not None:
            chart_rows.append({"Period": "Previous", "Value": previous})
        if latest is not None:
            chart_rows.append({"Period": "Latest", "Value": latest})

        chart_df = pd.DataFrame(chart_rows)
        prefix = "" if value_type == "integer" else "£"

        spec = {
            "background": "#3d3d3f",
            "height": 170,
            "mark": {"type": "bar", "cornerRadiusTopLeft": 5, "cornerRadiusTopRight": 5},
            "encoding": {
                "x": {
                    "field": "Period",
                    "type": "nominal",
                    "sort": ["Previous", "Latest"],
                    "axis": {
                        "title": None,
                        "labelColor": "#ffffff",
                        "labelFontSize": 12,
                        "ticks": False,
                        "domain": False
                    }
                },
                "y": {
                    "field": "Value",
                    "type": "quantitative",
                    "axis": {
                        "title": None,
                        "labelColor": "#cfcfcf",
                        "gridColor": "#555557",
                        "domain": False,
                        "format": "~s"
                    }
                },
                "color": {
                    "field": "Period",
                    "type": "nominal",
                    "scale": {
                        "domain": ["Previous", "Latest"],
                        "range": ["#8a8a8d", "#8bd02f"]
                    },
                    "legend": None
                },
                "tooltip": [
                    {"field": "Period", "type": "nominal"},
                    {"field": "Value", "type": "quantitative", "format": ",.0f", "title": title}
                ]
            },
            "config": {"view": {"stroke": None}}
        }

        st.markdown(
            f'<div style="font-weight:700;color:white;margin-bottom:-8px;">{title}</div>',
            unsafe_allow_html=True
        )
        st.vega_lite_chart(chart_df, spec, use_container_width=True)

        latest_text = format_financial_value(c.get(latest_field), value_type)
        previous_text = format_financial_value(c.get(previous_field), value_type)
        st.caption(f"Latest {latest_text}  |  Previous {previous_text}")
        return True

    mini_charts = [
        ("Turnover", "LatestTurnover", "PreviousTurnover", "currency"),
        ("Profit Before Tax", "LatestProfitBeforeTax", "PreviousProfitBeforeTax", "currency"),
        ("Cash", "LatestCash", "PreviousCash", "currency"),
        ("Net Assets", "LatestNetAssets", "PreviousNetAssets", "currency")
    ]

    available_mini = [x for x in mini_charts if c.get(x[1]) is not None or c.get(x[2]) is not None]
    if available_mini:
        st.markdown("### Key financials")
        for i in range(0, len(available_mini), 2):
            cols = st.columns(2)
            for col, item in zip(cols, available_mini[i:i+2]):
                with col:
                    render_two_period_chart(*item)

    # --------------------------------------------------
    # CURRENT ASSET MIX - COMPACT DONUT
    # --------------------------------------------------

    current_assets = to_number(c.get("LatestCurrentAssets"))
    cash = to_number(c.get("LatestCash"))
    debtors = to_number(c.get("LatestDebtors"))

    if current_assets is not None and current_assets > 0:
        cash_value = max(cash or 0, 0)
        debtors_value = max(debtors or 0, 0)
        other_value = max(current_assets - cash_value - debtors_value, 0)

        asset_mix = []
        if cash_value > 0:
            asset_mix.append({"Category": "Cash", "Value": cash_value})
        if debtors_value > 0:
            asset_mix.append({"Category": "Debtors", "Value": debtors_value})
        if other_value > 0:
            asset_mix.append({"Category": "Other current assets", "Value": other_value})

        if len(asset_mix) >= 2:
            st.markdown("### Latest current asset mix")
            asset_df = pd.DataFrame(asset_mix)
            donut_spec = {
                "background": "#3d3d3f",
                "height": 280,
                "mark": {"type": "arc", "innerRadius": 72, "outerRadius": 120, "stroke": "#3d3d3f", "strokeWidth": 2},
                "encoding": {
                    "theta": {"field": "Value", "type": "quantitative"},
                    "color": {
                        "field": "Category",
                        "type": "nominal",
                        "scale": {
                            "domain": ["Cash", "Debtors", "Other current assets"],
                            "range": ["#8bd02f", "#ffffff", "#8a8a8d"]
                        },
                        "legend": {
                            "title": None,
                            "labelColor": "#ffffff",
                            "labelFontSize": 12,
                            "orient": "right"
                        }
                    },
                    "tooltip": [
                        {"field": "Category", "type": "nominal"},
                        {"field": "Value", "type": "quantitative", "format": ",.0f", "title": "Value (£)"}
                    ]
                },
                "config": {"view": {"stroke": None}}
            }
            left, right = st.columns([1.2, 1])
            with left:
                st.vega_lite_chart(asset_df, donut_spec, use_container_width=True)
            with right:
                st.markdown(
                    f"""
                    <div style="background:#333335;padding:18px;border-radius:8px;border-left:4px solid #8bd02f;margin-top:20px;">
                        <div style="font-size:13px;color:#cfcfcf;margin-bottom:6px;">CURRENT ASSETS</div>
                        <div style="font-size:28px;font-weight:800;color:#8bd02f;">{format_financial_value(current_assets)}</div>
                        <div style="font-size:13px;color:#cfcfcf;margin-top:14px;line-height:1.8;">
                            Cash: <b style="color:white;">{format_financial_value(cash)}</b><br>
                            Debtors: <b style="color:white;">{format_financial_value(debtors)}</b><br>
                            Other: <b style="color:white;">{format_financial_value(other_value)}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # --------------------------------------------------
    # DETAILED COMPARISON TABLE
    # --------------------------------------------------

    st.markdown("### Detailed financial comparison")

    metrics = [
        ("Employees", "LatestEmployees", "PreviousEmployees", "integer"),
        ("Turnover", "LatestTurnover", "PreviousTurnover", "currency"),
        ("Gross Profit", "LatestGrossProfit", "PreviousGrossProfit", "currency"),
        ("Operating Profit", "LatestOperatingProfit", "PreviousOperatingProfit", "currency"),
        ("Profit Before Tax", "LatestProfitBeforeTax", "PreviousProfitBeforeTax", "currency"),
        ("Profit After Tax", "LatestProfitAfterTax", "PreviousProfitAfterTax", "currency"),
        ("Fixed Assets", "LatestFixedAssets", "PreviousFixedAssets", "currency"),
        ("Current Assets", "LatestCurrentAssets", "PreviousCurrentAssets", "currency"),
        ("Cash", "LatestCash", "PreviousCash", "currency"),
        ("Debtors", "LatestDebtors", "PreviousDebtors", "currency"),
        ("Creditors Due Within 1 Year", "LatestCreditorsDueWithinOneYear", "PreviousCreditorsDueWithinOneYear", "currency"),
        ("Creditors Due After 1 Year", "LatestCreditorsDueAfterOneYear", "PreviousCreditorsDueAfterOneYear", "currency"),
        ("Net Current Assets", "LatestNetCurrentAssets", "PreviousNetCurrentAssets", "currency"),
        ("Total Assets Less Current Liabilities", "LatestTotalAssetsLessCurrentLiabilities", "PreviousTotalAssetsLessCurrentLiabilities", "currency"),
        ("Net Assets", "LatestNetAssets", "PreviousNetAssets", "currency"),
        ("Bank Borrowings", "LatestBankBorrowings", "PreviousBankBorrowings", "currency")
    ]

    rows = []
    for label, latest_field, previous_field, value_type in metrics:
        latest = c.get(latest_field)
        previous = c.get(previous_field)
        if latest is None and previous is None:
            continue
        rows.append({
            "Metric": label,
            "Latest": format_financial_value(latest, value_type),
            "Previous": format_financial_value(previous, value_type),
            "Change": format_change(latest, previous)
        })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No comparable financial metrics are available.")

    # --------------------------------------------------
    # FINANCIAL COMMENTARY
    # --------------------------------------------------

    st.markdown("### Financial trend")
    st.markdown(
        f"""
        <div style="
            background:#333335;
            border-left:4px solid #8bd02f;
            padding:16px 18px;
            border-radius:6px;
            color:#eeeeee;
            line-height:1.6;
            margin-bottom:18px;
        ">
            {build_financial_commentary(c)}
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------
    # PROFESSIONAL ADVISERS
    # --------------------------------------------------

    st.markdown("### Professional adviser changes")
    adviser_rows = [
        {
            "Adviser": "Accountant",
            "Latest": display_value(c.get("LatestAccountantName")),
            "Previous": display_value(c.get("PreviousAccountantName")),
            "Changed": "Yes" if c.get("AccountantChanged") == 1 else "No"
        },
        {
            "Adviser": "Auditor",
            "Latest": display_value(c.get("LatestAuditorName")),
            "Previous": display_value(c.get("PreviousAuditorName")),
            "Changed": "Yes" if c.get("AuditorChanged") == 1 else "No"
        }
    ]
    st.dataframe(pd.DataFrame(adviser_rows), use_container_width=True, hide_index=True)


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
    "page_number": 1,
    "last_viewed_company": None
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

                        log_activity(
                            "LOGIN"
                        )

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

def get_rd_referral_summary():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS AccountancyFirms,
                SUM(CASE WHEN ReferralOpportunityBand = 'Very High' THEN 1 ELSE 0 END) AS VeryHighOpportunities,
                SUM(CASE WHEN ReferralOpportunityBand = 'High' THEN 1 ELSE 0 END) AS HighOpportunities,
                SUM(CASE WHEN ReferralOpportunityBand IN ('Very High','High') THEN 1 ELSE 0 END) AS PriorityPartners,
                SUM(VeryHighRDClients) AS VeryHighRDClients,
                MAX(LastCalculatedDate) AS LastCalculatedDate
            FROM dbo.RD_AccountantOpportunities
            """
        )

        row = cursor.fetchone()

        columns = [column[0] for column in cursor.description]

        cursor.close()

    finally:

        conn.close()

    return dict(zip(columns, row))


@st.cache_data(ttl=86400)
def get_rd_referral_accountants():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT AccountantName
            FROM dbo.RD_AccountantOpportunities
            WHERE AccountantName IS NOT NULL
              AND LTRIM(RTRIM(AccountantName)) <> ''
            ORDER BY AccountantName
            """
        )

        values = [
            str(row[0]).strip()
            for row in cursor.fetchall()
            if row[0] is not None
            and str(row[0]).strip() != ""
        ]

        cursor.close()

    finally:

        conn.close()

    return values


def build_rd_referral_filters(search_params):

    sql = ""
    params = []

    accountant_name = search_params["accountant_name"]
    opportunity_bands = search_params["opportunity_bands"]
    timing_bands = search_params["timing_bands"]
    min_rd_clients = search_params["min_rd_clients"]
    min_score = search_params["min_score"]

    if accountant_name and accountant_name != "All":

        sql += """
            AND AccountantName = %s
        """

        params.append(
            accountant_name
        )

    if opportunity_bands:

        placeholders = ", ".join(
            ["%s"] * len(opportunity_bands)
        )

        sql += f"""
            AND ReferralOpportunityBand IN ({placeholders})
        """

        params.extend(
            opportunity_bands
        )

    if timing_bands:

        placeholders = ", ".join(
            ["%s"] * len(timing_bands)
        )

        sql += f"""
            AND SalesTimingBand IN ({placeholders})
        """

        params.extend(
            timing_bands
        )

    if min_rd_clients > 0:

        sql += """
            AND RDRelevantClients >= %s
        """

        params.append(
            min_rd_clients
        )

    if min_score > 0:

        sql += """
            AND ReferralOpportunityScore >= %s
        """

        params.append(
            min_score
        )

    return sql, params


def count_rd_referral_partners(search_params):

    filter_sql, params = build_rd_referral_filters(
        search_params
    )

    sql = f"""
        SELECT COUNT_BIG(*)
        FROM dbo.RD_AccountantOpportunities
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


def search_rd_referral_partners(
    search_params,
    page_number
):

    filter_sql, params = build_rd_referral_filters(
        search_params
    )

    offset_rows = (
        page_number - 1
    ) * PAGE_SIZE

    sql = f"""
        SELECT
            AccountantName AS [Accountant],
            RDRelevantClients AS [R&D Clients],
            VeryHighRDClients AS [Very High],
            HighRDClients AS [High],
            MediumRDClients AS [Medium],
            ContactNowClients AS [Contact Now],
            ReferralOpportunityScore AS [Score],
            ReferralOpportunityBand AS [Opportunity],
            SalesTimingBand AS [Timing]
        FROM dbo.RD_AccountantOpportunities
        WHERE 1 = 1
        {filter_sql}
        ORDER BY
            ReferralOpportunityScore DESC,
            VeryHighRDClients DESC,
            HighRDClients DESC,
            AccountantName
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


def get_rd_referral_download_data(search_params):

    filter_sql, params = build_rd_referral_filters(
        search_params
    )

    sql = f"""
        SELECT TOP {DOWNLOAD_LIMIT}
            AccountantName AS [Accountant],
            RDRelevantClients AS [R&D Clients],
            VeryHighRDClients AS [Very High],
            HighRDClients AS [High],
            MediumRDClients AS [Medium],
            ContactNowClients AS [Contact Now],
            ContactSoonClients AS [Contact Soon],
            NurtureClients AS [Nurture],
            LaterClients AS [Later],
            AvgRDOpportunityScore AS [Average R&D Score],
            AvgSalesTimingScore AS [Average Timing Score],
            ReferralOpportunityScore AS [Referral Score],
            ReferralOpportunityBand AS [Opportunity],
            SalesTimingBand AS [Timing],
            RDServiceStatus AS [R&D Service Status]
        FROM dbo.RD_AccountantOpportunities
        WHERE 1 = 1
        {filter_sql}
        ORDER BY
            ReferralOpportunityScore DESC,
            VeryHighRDClients DESC,
            HighRDClients DESC,
            AccountantName
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


def get_rd_accountant_detail(accountant_name):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT TOP 1
                AccountantName,
                RDRelevantClients,
                VeryHighRDClients,
                HighRDClients,
                MediumRDClients,
                LowRDClients,
                ContactNowClients,
                ContactSoonClients,
                NurtureClients,
                LaterClients,
                AvgRDOpportunityScore,
                MaxRDOpportunityScore,
                AvgSalesTimingScore,
                ReferralOpportunityScore,
                ReferralOpportunityBand,
                SalesTimingBand,
                RDServiceStatus,
                LastCalculatedDate
            FROM dbo.RD_AccountantOpportunities
            WHERE AccountantName = %s
            """,
            (accountant_name,)
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


def get_rd_accountant_clients(
    accountant_name,
    opportunity_band="All"
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        sql = """
            SELECT
                CompanyNumber AS [Company Number],
                CompanyName AS [Company Name],
                BestRDCategory AS [R&D Category],
                BestSICDescription AS [Industry],
                LatestEmployees AS [Employees],
                LatestTurnover AS [Turnover],
                RDOpportunityScore AS [R&D Score],
                RDOpportunityBand AS [Opportunity],
                SalesTimingScore AS [Timing Score],
                SalesTimingBand AS [Timing]
            FROM dbo.RD_RDProspects
            WHERE LTRIM(RTRIM(LatestAccountantName)) = %s
        """

        params = [accountant_name]

        if opportunity_band != "All":

            sql += """
                AND RDOpportunityBand = %s
            """

            params.append(
                opportunity_band
            )

        sql += """
            ORDER BY
                RDOpportunityScore DESC,
                SalesTimingScore DESC,
                CompanyName
        """

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


def get_rd_company_detail(company_number):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT TOP 1
                CompanyNumber,
                CompanyName,
                CompanyStatus,
                PostTown,
                County,
                PostCode,
                BestSICCode,
                BestSICDescription,
                BestRDCategory,
                LatestEmployees,
                EmployeeGrowthPct,
                LatestTurnover,
                TurnoverGrowthPct,
                LatestProfitBeforeTax,
                LatestCash,
                LatestAccountantName,
                LatestAuditorName,
                IndustryScore,
                GrowthScore,
                FinancialScore,
                CompanySignalScore,
                RDOpportunityScore,
                RDOpportunityBand,
                EstimatedNextAccountsDueDate,
                DaysUntilEstimatedAccountsDue,
                SalesTimingScore,
                SalesTimingBand,
                LastRefreshed
            FROM dbo.RD_RDProspects
            WHERE CompanyNumber = %s
            ORDER BY LastRefreshed DESC
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


def show_company_search_page():

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

    try:

        accountant_options = get_accountants()
        auditor_options = get_auditors()

    except Exception:

        st.warning(
            "Accountant and Auditor lists are temporarily unavailable. "
            "You can still search using the other filters."
        )

        accountant_options = []
        auditor_options = []

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
                ["All"] + accountant_options
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

            auditor = st.selectbox(
                "Auditor",
                ["All"] + auditor_options
            )

        search = st.form_submit_button(
            "SEARCH COMPANIES"
        )

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

                    result_count = count_companies(
                        search_params
                    )

                    results = search_companies(
                        search_params,
                        1
                    )

                st.session_state["search_params"] = search_params
                st.session_state["result_count"] = result_count
                st.session_state["page_number"] = 1
                st.session_state["last_viewed_company"] = None
                st.session_state["results"] = results

                log_activity(
                    "SEARCH",
                    search_params=search_params,
                    result_count=result_count
                )

            except Exception as e:

                st.error(
                    "Unable to search the Rebel Data database."
                )

                st.exception(e)

    if st.session_state["results"] is not None:

        results = st.session_state["results"]
        result_count = st.session_state["result_count"]
        page_number = st.session_state["page_number"]

        st.markdown(
            "<hr>",
            unsafe_allow_html=True
        )

        metric1, metric2, metric3 = st.columns(
            [1, 1, 2]
        )

        total_pages = max(
            1,
            math.ceil(
                result_count / PAGE_SIZE
            )
        )

        start_record = (
            ((page_number - 1) * PAGE_SIZE) + 1
            if result_count > 0
            else 0
        )

        end_record = min(
            page_number * PAGE_SIZE,
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

        if len(results) > 0:

            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True,
                height=500
            )

            previous_col, page_col, next_col = st.columns(
                [1, 3, 1]
            )

            with previous_col:

                previous_clicked = st.button(
                    "← PREVIOUS",
                    disabled=(
                        page_number <= 1
                    ),
                    use_container_width=True,
                    key="company_previous"
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

                next_clicked = st.button(
                    "NEXT →",
                    disabled=(
                        page_number >= total_pages
                    ),
                    use_container_width=True,
                    key="company_next"
                )

            if previous_clicked:

                new_page = page_number - 1

                with st.spinner(
                    "Loading previous page..."
                ):

                    new_results = search_companies(
                        st.session_state[
                            "search_params"
                        ],
                        new_page
                    )

                st.session_state["page_number"] = new_page
                st.session_state["results"] = new_results
                st.rerun()

            if next_clicked:

                new_page = page_number + 1

                with st.spinner(
                    "Loading next page..."
                ):

                    new_results = search_companies(
                        st.session_state[
                            "search_params"
                        ],
                        new_page
                    )

                st.session_state["page_number"] = new_page
                st.session_state["results"] = new_results
                st.rerun()

            st.markdown(
                "<br>",
                unsafe_allow_html=True
            )

            with st.expander(
                "Download matching companies"
            ):

                if result_count > DOWNLOAD_LIMIT:

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
                    "PREPARE DOWNLOAD",
                    key="company_prepare_download"
                ):

                    with st.spinner(
                        "Preparing download..."
                    ):

                        download_data = get_download_data(
                            st.session_state[
                                "search_params"
                            ]
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

                        log_activity(
                            "DOWNLOAD",
                            search_params=st.session_state[
                                "search_params"
                            ],
                            result_count=st.session_state[
                                "result_count"
                            ],
                            download_count=len(
                                download_data
                            )
                        )

                    st.download_button(
                        label="DOWNLOAD CSV",
                        data=csv,
                        file_name="rebel_data_selection.csv",
                        mime="text/csv",
                        key="company_download_csv"
                    )

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

            detail_choice = st.selectbox(
                "Select a company from this page",
                [
                    "Select a company..."
                ]
                + list(
                    company_choices.keys()
                ),
                key="company_detail_choice"
            )

            if detail_choice != "Select a company...":

                selected_number = company_choices[
                    detail_choice
                ]

                if (
                    st.session_state.get(
                        "last_viewed_company"
                    )
                    != selected_number
                ):

                    log_activity(
                        "COMPANY_VIEW",
                        company_viewed=selected_number
                    )

                    st.session_state[
                        "last_viewed_company"
                    ] = selected_number

                try:

                    with st.spinner(
                        "Loading company details..."
                    ):

                        detail = get_company_detail(
                            selected_number
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

                        st.subheader(
                            "Company"
                        )

                        col1, col2, col3, col4 = st.columns(
                            4
                        )

                        col1.metric(
                            "Status",
                            display_value(
                                detail["CompanyStatus"]
                            )
                        )

                        col2.metric(
                            "Employees",
                            display_value(
                                detail["Employees"]
                            )
                        )

                        col3.metric(
                            "Category",
                            display_value(
                                detail["CompanyCategory"]
                            )
                        )

                        col4.metric(
                            "Country of Origin",
                            display_value(
                                detail["CountryOfOrigin"]
                            )
                        )

                        st.subheader(
                            "Important Dates"
                        )

                        col1, col2, col3 = st.columns(3)

                        col1.write(
                            "**Incorporated**"
                        )

                        col1.write(
                            display_value(
                                detail["IncorporationDate"]
                            )
                        )

                        col2.write(
                            "**Accounts Last Made Up**"
                        )

                        col2.write(
                            display_value(
                                detail["AccountsLastMadeUpDate"]
                            )
                        )

                        col3.write(
                            "**Confirmation Statement Last Made Up**"
                        )

                        col3.write(
                            display_value(
                                detail["ConfStmtLastMadeUpDate"]
                            )
                        )

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
                            for x in address_parts
                            if x is not None
                            and str(x).strip() != ""
                        ]

                        st.write(
                            ", ".join(address_parts)
                            if address_parts
                            else "Not available"
                        )

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
                            for x in sic_values
                            if x is not None
                            and str(x).strip() != ""
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

                        st.subheader(
                            "Professional Advisers"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            st.write(
                                "**Accountant**"
                            )

                            st.write(
                                display_value(
                                    detail["AccountantName"]
                                )
                            )

                        with col2:

                            st.write(
                                "**Auditor**"
                            )

                            st.write(
                                display_value(
                                    detail["AuditorName"]
                                )
                            )

                        st.subheader(
                            "Accounts"
                        )

                        col1, col2, col3 = st.columns(3)

                        with col1:

                            st.write(
                                "**Accounts Category**"
                            )

                            st.write(
                                display_value(
                                    detail["AccountsCategory"]
                                )
                            )

                        with col2:

                            st.write(
                                "**Next Accounts Due**"
                            )

                            st.write(
                                display_value(
                                    detail["AccountsNextDueDate"]
                                )
                            )

                        with col3:

                            st.write(
                                "**Last Accounts**"
                            )

                            st.write(
                                display_value(
                                    detail["AccountsLastMadeUpDate"]
                                )
                            )

                        st.subheader(
                            "Mortgages"
                        )

                        col1, col2, col3, col4 = st.columns(
                            4
                        )

                        col1.metric(
                            "Charges",
                            display_value(
                                detail["MortgagesNumCharges"]
                            )
                        )

                        col2.metric(
                            "Outstanding",
                            display_value(
                                detail["MortgagesOutstanding"]
                            )
                        )

                        col3.metric(
                            "Part Satisfied",
                            display_value(
                                detail["MortgagesPartSatisfied"]
                            )
                        )

                        col4.metric(
                            "Satisfied",
                            display_value(
                                detail["MortgagesSatisfied"]
                            )
                        )


                        try:
                            with st.spinner("Loading financial comparison..."):
                                accounts_comparison = get_accounts_comparison(
                                    selected_number
                                )

                            if accounts_comparison:
                                show_accounts_comparison(accounts_comparison)
                            else:
                                st.markdown("<hr>", unsafe_allow_html=True)
                                st.markdown(
                                    '<div class="section-title">Financial Comparison</div>',
                                    unsafe_allow_html=True
                                )
                                st.info(
                                    "No accounts comparison is currently available for this company."
                                )

                        except Exception as comparison_error:
                            st.markdown("<hr>", unsafe_allow_html=True)
                            st.markdown(
                                '<div class="section-title">Financial Comparison</div>',
                                unsafe_allow_html=True
                            )
                            st.warning(
                                "The company details loaded, but the financial comparison "
                                "could not be retrieved."
                            )
                            st.exception(comparison_error)

                except Exception as e:

                    st.error(
                        "Unable to load company details."
                    )

                    st.exception(e)

        else:

            st.info(
                "No companies matched your search."
            )


def show_rd_referral_page():

    st.markdown(
        """
        <div class="hero-title">
            R&D Referral Partners
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero-subtitle">
            Identify accountancy firms whose clients show strong potential for R&D tax relief.
        </div>
        """,
        unsafe_allow_html=True
    )

    try:

        summary = get_rd_referral_summary()

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "ACCOUNTANTS ANALYSED",
            f"{int(summary['AccountancyFirms'] or 0):,}"
        )

        m2.metric(
            "PRIORITY PARTNERS",
            f"{int(summary['PriorityPartners'] or 0):,}"
        )

        m3.metric(
            "VERY HIGH",
            f"{int(summary['VeryHighOpportunities'] or 0):,}"
        )

        m4.metric(
            "HIGH",
            f"{int(summary['HighOpportunities'] or 0):,}"
        )

    except Exception as e:

        st.warning(
            "Unable to load R&D referral summary."
        )

        st.exception(e)

    st.markdown(
        """
        <div class="section-title">
            Referral Partner Search
        </div>
        """,
        unsafe_allow_html=True
    )

    try:

        rd_accountant_options = get_rd_referral_accountants()

    except Exception as e:

        st.warning(
            "Unable to load the R&D accountant list. "
            "The other referral filters are still available."
        )

        rd_accountant_options = []

    with st.form(
        "rd_referral_search_form"
    ):

        col1, col2, col3 = st.columns(3)

        with col1:

            accountant_name = st.selectbox(
                "Accountant",
                ["All"] + rd_accountant_options,
                index=0,
                key="rd_accountant_filter"
            )

        with col2:

            opportunity_bands = st.multiselect(
                "Opportunity",
                [
                    "Very High",
                    "High",
                    "Medium",
                    "Low"
                ],
                default=[
                    "Very High",
                    "High"
                ]
            )

        with col3:

            timing_bands = st.multiselect(
                "Timing",
                [
                    "Contact Now",
                    "Contact Soon",
                    "Nurture",
                    "Later"
                ]
            )

        col1, col2, col3 = st.columns(3)

        with col1:

            min_rd_clients = st.number_input(
                "Minimum R&D Clients",
                min_value=0,
                value=0,
                step=1
            )

        with col2:

            min_score = st.number_input(
                "Minimum Referral Score",
                min_value=0,
                max_value=100,
                value=0,
                step=1
            )

        with col3:

            st.write("")
            st.write("")
            search = st.form_submit_button(
                "SEARCH REFERRAL PARTNERS"
            )

    if search or st.session_state.get(
        "rd_results"
    ) is None:

        search_params = {
            "accountant_name": accountant_name,
            "opportunity_bands": opportunity_bands,
            "timing_bands": timing_bands,
            "min_rd_clients": min_rd_clients,
            "min_score": min_score
        }

        try:

            with st.spinner(
                "Searching referral opportunities..."
            ):

                result_count = count_rd_referral_partners(
                    search_params
                )

                results = search_rd_referral_partners(
                    search_params,
                    1
                )

            st.session_state["rd_search_params"] = search_params
            st.session_state["rd_result_count"] = result_count
            st.session_state["rd_page_number"] = 1
            st.session_state["rd_results"] = results
            st.session_state["last_viewed_accountant"] = None

            log_activity(
                "RD_REFERRAL_SEARCH",
                result_count=result_count
            )

        except Exception as e:

            st.error(
                "Unable to search R&D referral partners."
            )

            st.exception(e)

    results = st.session_state.get(
        "rd_results"
    )

    if results is None:

        return

    result_count = st.session_state.get(
        "rd_result_count",
        0
    )

    page_number = st.session_state.get(
        "rd_page_number",
        1
    )

    st.markdown(
        "<hr>",
        unsafe_allow_html=True
    )

    metric1, metric2, metric3 = st.columns(
        [1, 1, 2]
    )

    total_pages = max(
        1,
        math.ceil(
            result_count / PAGE_SIZE
        )
    )

    start_record = (
        ((page_number - 1) * PAGE_SIZE) + 1
        if result_count > 0
        else 0
    )

    end_record = min(
        page_number * PAGE_SIZE,
        result_count
    )

    metric1.metric(
        "PARTNERS FOUND",
        f"{result_count:,}"
    )

    metric2.metric(
        "PAGE",
        f"{page_number:,} of {total_pages:,}"
    )

    if result_count > 0:

        metric3.markdown(
            f"""
            <div style="
                color:#cfcfcf;
                padding-top:28px;
                font-size:14px;
            ">
                Showing partners
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

    if len(results) == 0:

        st.info(
            "No referral partners matched your filters."
        )

        return

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True,
        height=500
    )

    previous_col, page_col, next_col = st.columns(
        [1, 3, 1]
    )

    with previous_col:

        previous_clicked = st.button(
            "← PREVIOUS",
            disabled=(
                page_number <= 1
            ),
            use_container_width=True,
            key="rd_previous"
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

        next_clicked = st.button(
            "NEXT →",
            disabled=(
                page_number >= total_pages
            ),
            use_container_width=True,
            key="rd_next"
        )

    if previous_clicked:

        new_page = page_number - 1

        with st.spinner(
            "Loading previous page..."
        ):

            new_results = search_rd_referral_partners(
                st.session_state[
                    "rd_search_params"
                ],
                new_page
            )

        st.session_state["rd_page_number"] = new_page
        st.session_state["rd_results"] = new_results
        st.rerun()

    if next_clicked:

        new_page = page_number + 1

        with st.spinner(
            "Loading next page..."
        ):

            new_results = search_rd_referral_partners(
                st.session_state[
                    "rd_search_params"
                ],
                new_page
            )

        st.session_state["rd_page_number"] = new_page
        st.session_state["rd_results"] = new_results
        st.rerun()

    with st.expander(
        "Download matching referral partners"
    ):

        if result_count > DOWNLOAD_LIMIT:

            st.write(
                f"Your search found {result_count:,} partners. "
                f"The current download limit is the first "
                f"{DOWNLOAD_LIMIT:,} matching partners."
            )

        else:

            st.write(
                f"Download all {result_count:,} matching partners."
            )

        if st.button(
            "PREPARE REFERRAL DOWNLOAD",
            key="rd_prepare_download"
        ):

            with st.spinner(
                "Preparing download..."
            ):

                download_data = get_rd_referral_download_data(
                    st.session_state[
                        "rd_search_params"
                    ]
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

                log_activity(
                    "RD_REFERRAL_DOWNLOAD",
                    result_count=st.session_state[
                        "rd_result_count"
                    ],
                    download_count=len(
                        download_data
                    )
                )

            st.download_button(
                label="DOWNLOAD CSV",
                data=csv,
                file_name="rd_referral_partners.csv",
                mime="text/csv",
                key="rd_download_csv"
            )

    st.markdown(
        "<hr>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-title">
            Accountant Detail
        </div>
        """,
        unsafe_allow_html=True
    )

    accountant_choices = list(
        results["Accountant"]
    )

    selected_accountant = st.selectbox(
        "Select an accountant from this page",
        [
            "Select an accountant..."
        ]
        + accountant_choices,
        key="rd_accountant_choice"
    )

    if selected_accountant == "Select an accountant...":

        return

    if (
        st.session_state.get(
            "last_viewed_accountant"
        )
        != selected_accountant
    ):

        log_activity(
            "RD_ACCOUNTANT_VIEW",
            company_viewed=selected_accountant
        )

        st.session_state[
            "last_viewed_accountant"
        ] = selected_accountant

    try:

        detail = get_rd_accountant_detail(
            selected_accountant
        )

        if not detail:

            st.warning(
                "No accountant detail was found."
            )

            return

        st.markdown(
            f"""
            <div class="detail-title">
                {display_value(detail["AccountantName"])}
            </div>

            <div class="detail-subtitle">
                {display_value(detail["ReferralOpportunityBand"])}
                referral opportunity ·
                {display_value(detail["ReferralOpportunityScore"])}/100
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3, col4, col5 = st.columns(
            5
        )

        col1.metric(
            "R&D Clients",
            f"{int(detail['RDRelevantClients'] or 0):,}"
        )

        col2.metric(
            "Very High",
            f"{int(detail['VeryHighRDClients'] or 0):,}"
        )

        col3.metric(
            "High",
            f"{int(detail['HighRDClients'] or 0):,}"
        )

        col4.metric(
            "Contact Now",
            f"{int(detail['ContactNowClients'] or 0):,}"
        )

        col5.metric(
            "Referral Score",
            f"{int(detail['ReferralOpportunityScore'] or 0):,}"
        )

        rd_clients = int(
            detail["RDRelevantClients"] or 0
        )

        very_high = int(
            detail["VeryHighRDClients"] or 0
        )

        high = int(
            detail["HighRDClients"] or 0
        )

        contact_now = int(
            detail["ContactNowClients"] or 0
        )

        st.markdown(
            "#### Why this practice is interesting"
        )

        st.write(
            f"{selected_accountant} has {rd_clients:,} potential R&D clients "
            f"identified in Rebel Data, including {very_high:,} Very High and "
            f"{high:,} High opportunities. {contact_now:,} are currently "
            f"classified as Contact Now. The practice has an overall referral "
            f"opportunity score of {int(detail['ReferralOpportunityScore'] or 0)}/100 "
            f"and is classified as {detail['ReferralOpportunityBand']}."
        )

        st.markdown(
            "#### Potential R&D Clients"
        )

        client_band = st.selectbox(
            "Client opportunity",
            [
                "All",
                "Very High",
                "High",
                "Medium",
                "Low"
            ],
            key="rd_client_band"
        )

        with st.spinner(
            "Loading R&D clients..."
        ):

            clients = get_rd_accountant_clients(
                selected_accountant,
                client_band
            )

        st.write(
            f"{len(clients):,} matching companies"
        )

        if len(clients) == 0:

            st.info(
                "No companies matched this client opportunity filter."
            )

            return

        st.dataframe(
            clients,
            use_container_width=True,
            hide_index=True,
            height=450
        )

        company_choices = {
            (
                f"{row['Company Name']} "
                f"({row['Company Number']})"
            ):
            row["Company Number"]

            for _, row in clients.iterrows()
        }

        selected_company = st.selectbox(
            "Select an R&D company",
            [
                "Select a company..."
            ]
            + list(
                company_choices.keys()
            ),
            key="rd_company_choice"
        )

        if selected_company == "Select a company...":

            return

        selected_company_number = company_choices[
            selected_company
        ]

        if (
            st.session_state.get(
                "last_viewed_rd_company"
            )
            != selected_company_number
        ):

            log_activity(
                "RD_COMPANY_VIEW",
                company_viewed=selected_company_number
            )

            st.session_state[
                "last_viewed_rd_company"
            ] = selected_company_number

        with st.spinner(
            "Loading R&D company intelligence..."
        ):

            company = get_rd_company_detail(
                selected_company_number
            )

        if not company:

            st.warning(
                "No R&D company detail was found."
            )

            return

        st.markdown(
            "<hr>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="detail-title">
                {display_value(company["CompanyName"])}
            </div>

            <div class="detail-subtitle">
                R&D Opportunity:
                {display_value(company["RDOpportunityBand"])}
                ·
                {display_value(company["RDOpportunityScore"])}/100
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(
            4
        )

        col1.metric(
            "Industry Score",
            display_value(
                company["IndustryScore"]
            )
        )

        col2.metric(
            "Growth Score",
            display_value(
                company["GrowthScore"]
            )
        )

        col3.metric(
            "Financial Score",
            display_value(
                company["FinancialScore"]
            )
        )

        col4.metric(
            "Company Signal Score",
            display_value(
                company["CompanySignalScore"]
            )
        )

        col1, col2, col3, col4 = st.columns(
            4
        )

        col1.metric(
            "Employees",
            display_value(
                company["LatestEmployees"]
            )
        )

        col2.metric(
            "Employee Growth %",
            display_value(
                company["EmployeeGrowthPct"]
            )
        )

        col3.metric(
            "Turnover",
            display_value(
                company["LatestTurnover"]
            )
        )

        col4.metric(
            "Turnover Growth %",
            display_value(
                company["TurnoverGrowthPct"]
            )
        )

        st.markdown(
            "#### Company Signals"
        )

        st.write(
            f"**R&D Category:** {display_value(company['BestRDCategory'])}"
        )

        st.write(
            f"**Industry:** {display_value(company['BestSICDescription'])}"
        )

        st.write(
            f"**Profit Before Tax:** {display_value(company['LatestProfitBeforeTax'])}"
        )

        st.write(
            f"**Cash:** {display_value(company['LatestCash'])}"
        )

        st.write(
            f"**Accountant:** {display_value(company['LatestAccountantName'])}"
        )

        st.write(
            f"**Auditor:** {display_value(company['LatestAuditorName'])}"
        )

        st.markdown(
            "#### Sales Timing"
        )

        col1, col2, col3 = st.columns(
            3
        )

        col1.metric(
            "Timing Score",
            display_value(
                company["SalesTimingScore"]
            )
        )

        col2.metric(
            "Timing Band",
            display_value(
                company["SalesTimingBand"]
            )
        )

        col3.metric(
            "Days Until Estimated Accounts Due",
            display_value(
                company["DaysUntilEstimatedAccountsDue"]
            )
        )

        st.write(
            "**Estimated Next Accounts Due:** "
            f"{display_value(company['EstimatedNextAccountsDueDate'])}"
        )

    except Exception as e:

        st.error(
            "Unable to load R&D referral detail."
        )

        st.exception(e)


# Add defaults used by the new page.
additional_defaults = {
    "rd_search_params": None,
    "rd_results": None,
    "rd_result_count": 0,
    "rd_page_number": 1,
    "last_viewed_accountant": None,
    "last_viewed_rd_company": None
}

for key, value in additional_defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


show_header(
    show_logout=True
)


# ==================================================
# TOP NAVIGATION MENU
# ==================================================

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Company Search"

st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] > div:has(button[key="nav_company_search"]),
    div[data-testid="stHorizontalBlock"] > div:has(button[key="nav_rd_referrals"]) {
        gap: 0.5rem;
    }

    button[kind="secondary"] {
        border-radius: 6px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

nav1, nav2, nav_spacer = st.columns([1.2, 1.5, 5])

with nav1:
    company_active = (
        st.session_state["active_page"] == "Company Search"
    )

    if st.button(
        "COMPANY SEARCH",
        key="nav_company_search",
        use_container_width=True,
        type="primary" if company_active else "secondary"
    ):
        st.session_state["active_page"] = "Company Search"
        st.rerun()

with nav2:
    rd_active = (
        st.session_state["active_page"] == "R&D Referral Partners"
    )

    if st.button(
        "R&D REFERRAL PARTNERS",
        key="nav_rd_referrals",
        use_container_width=True,
        type="primary" if rd_active else "secondary"
    ):
        st.session_state["active_page"] = "R&D Referral Partners"
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

if st.session_state["active_page"] == "Company Search":
    show_company_search_page()
else:
    show_rd_referral_page()


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
