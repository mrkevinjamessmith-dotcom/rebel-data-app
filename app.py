import streamlit as st
import pandas as pd
import pymssql
import math
import time
import io
import re
import json
import requests
from openai import OpenAI
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak
)


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
# OPENAI / ASK REBEL
# ==================================================

def get_openai_client():
    return OpenAI(
        api_key=st.secrets["openai"]["api_key"]
    )


ASK_REBEL_DATASETS = {
    "companies": {
        "view": "dbo.vw_AskRebelCompanies",
        "fields": {
            "CompanyNumber": "CompanyNumber",
            "CompanyName": "CompanyName",
            "PostTown": "PostTown",
            "County": "County",
            "PostCode": "PostCode",
            "CompanyCategory": "CompanyCategory",
            "CompanyStatus": "CompanyStatus",
            "CountryOfOrigin": "CountryOfOrigin",
            "IncorporationDate": "IncorporationDate",
            "Employees": "Employees",
            "AccountantName": "AccountantName",
            "AuditorName": "AuditorName",
            "AccountsNextDueDate": "AccountsNextDueDate",
            "AccountsLastMadeUpDate": "AccountsLastMadeUpDate"
        },
        "virtual_fields": {"Location", "SIC"},
        "default_columns": [
            "CompanyNumber",
            "CompanyName",
            "PostTown",
            "County",
            "PostCode",
            "CompanyStatus",
            "Employees",
            "SIC1",
            "AccountantName",
            "AuditorName"
        ]
    },
    "prospects": {
        "view": "dbo.vw_AskRebelProspects",
        "fields": {
            "CompanyNumber": "CompanyNumber",
            "CompanyName": "CompanyName",
            "CompanyStatus": "CompanyStatus",
            "PostTown": "PostTown",
            "County": "County",
            "PostCode": "PostCode",
            "BestSICCode": "BestSICCode",
            "BestSICDescription": "BestSICDescription",
            "BestRDCategory": "BestRDCategory",
            "LatestEmployees": "LatestEmployees",
            "EmployeeGrowthPct": "EmployeeGrowthPct",
            "LatestTurnover": "LatestTurnover",
            "TurnoverGrowthPct": "TurnoverGrowthPct",
            "LatestProfitBeforeTax": "LatestProfitBeforeTax",
            "LatestCash": "LatestCash",
            "LatestAccountantName": "LatestAccountantName",
            "LatestAuditorName": "LatestAuditorName",
            "IndustryScore": "IndustryScore",
            "GrowthScore": "GrowthScore",
            "FinancialScore": "FinancialScore",
            "CompanySignalScore": "CompanySignalScore",
            "RDOpportunityScore": "RDOpportunityScore",
            "RDOpportunityBand": "RDOpportunityBand",
            "EstimatedNextAccountsDueDate": "EstimatedNextAccountsDueDate",
            "DaysUntilEstimatedAccountsDue": "DaysUntilEstimatedAccountsDue",
            "SalesTimingScore": "SalesTimingScore",
            "SalesTimingBand": "SalesTimingBand"
        },
        "virtual_fields": {"Location", "Industry"},
        "default_columns": [
            "CompanyNumber",
            "CompanyName",
            "PostTown",
            "County",
            "BestSICDescription",
            "LatestEmployees",
            "LatestTurnover",
            "RDOpportunityScore",
            "RDOpportunityBand",
            "SalesTimingScore",
            "SalesTimingBand",
            "LatestAccountantName"
        ]
    },
    "accountants": {
        "view": "dbo.vw_AskRebelAccountants",
        "fields": {
            "AccountantName": "AccountantName",
            "TotalClients": "TotalClients",
            "VeryHighRDClients": "VeryHighRDClients",
            "HighRDClients": "HighRDClients",
            "MediumRDClients": "MediumRDClients",
            "LowRDClients": "LowRDClients",
            "RDRelevantClients": "RDRelevantClients",
            "ContactNowClients": "ContactNowClients",
            "ContactSoonClients": "ContactSoonClients",
            "NurtureClients": "NurtureClients",
            "LaterClients": "LaterClients",
            "AvgRDOpportunityScore": "AvgRDOpportunityScore",
            "MaxRDOpportunityScore": "MaxRDOpportunityScore",
            "AvgSalesTimingScore": "AvgSalesTimingScore",
            "ReferralOpportunityScore": "ReferralOpportunityScore",
            "ReferralOpportunityBand": "ReferralOpportunityBand",
            "SalesTimingBand": "SalesTimingBand",
            "RDServiceStatus": "RDServiceStatus"
        },
        "virtual_fields": set(),
        "default_columns": [
            "AccountantName",
            "TotalClients",
            "VeryHighRDClients",
            "HighRDClients",
            "RDRelevantClients",
            "ContactNowClients",
            "ContactSoonClients",
            "ReferralOpportunityScore",
            "ReferralOpportunityBand",
            "SalesTimingBand"
        ]
    }
}


def ask_rebel_plan(question, previous_plan=None):
    """
    Convert a natural-language question into a restricted query plan.

    If previous_plan is supplied, the user's message may be a follow-up
    such as "only ones with more than 20 employees" or
    "sort those by turnover". The model must return a complete revised plan.

    The model does not write or execute SQL.
    """

    client = get_openai_client()

    system_prompt = """
You translate questions about Rebel Data into a JSON query plan.

Return JSON only. Do not return markdown and do not return SQL.

Available datasets:

1. companies
Use for general UK company searches and counts.
Fields:
CompanyNumber, CompanyName, PostTown, County, PostCode,
CompanyCategory, CompanyStatus, CountryOfOrigin, IncorporationDate,
Employees, AccountantName, AuditorName,
AccountsNextDueDate, AccountsLastMadeUpDate.
Virtual fields:
Location = search PostTown, County and PostCode together.
SIC = search SIC1, SIC2, SIC3 and SIC4 together.

2. prospects
Use when the question is specifically about Rebel R&D opportunity,
R&D scoring, sales timing, growth, turnover, cash, profit or scored prospects.
Fields:
CompanyNumber, CompanyName, CompanyStatus, PostTown, County, PostCode,
BestSICCode, BestSICDescription, BestRDCategory, LatestEmployees,
EmployeeGrowthPct, LatestTurnover, TurnoverGrowthPct,
LatestProfitBeforeTax, LatestCash, LatestAccountantName,
LatestAuditorName, IndustryScore, GrowthScore, FinancialScore,
CompanySignalScore, RDOpportunityScore, RDOpportunityBand,
EstimatedNextAccountsDueDate, DaysUntilEstimatedAccountsDue,
SalesTimingScore, SalesTimingBand.
Virtual fields:
Location = search PostTown, County and PostCode together.
Industry = search BestSICDescription.

3. accountants
Use for questions comparing or finding accountancy firms based on
their Rebel referral opportunity and R&D client profile.
Fields:
AccountantName, TotalClients, VeryHighRDClients, HighRDClients,
MediumRDClients, LowRDClients, RDRelevantClients, ContactNowClients,
ContactSoonClients, NurtureClients, LaterClients,
AvgRDOpportunityScore, MaxRDOpportunityScore, AvgSalesTimingScore,
ReferralOpportunityScore, ReferralOpportunityBand, SalesTimingBand,
RDServiceStatus.

JSON format:
{
  "dataset": "companies|prospects|accountants",
  "operation": "list|count",
  "filters": [
    {
      "field": "allowed field name",
      "operator": "eq|contains|gte|lte|gt|lt|in",
      "value": "value or array"
    }
  ],
  "sort": [
    {
      "field": "allowed real field name",
      "direction": "asc|desc"
    }
  ],
  "limit": 50,
  "interpretation": "short plain English description of how you interpreted the question"
}

General rules:
- Use count when the user asks how many, number of, count or total companies/firms.
- Otherwise use list.
- Maximum limit is 100.
- Use contains for partial company names, locations, industries, SIC text,
  accountant names or auditor names unless the user clearly asks for an exact value.
- CompanyStatus values are usually Active or Dissolved.
- For phrases such as "20+ employees", use gte 20.
- For "more than 20", use gt 20.
- For "under £2m turnover", use lt 2000000.
- "High R&D opportunity" means RDOpportunityBand = "High".
- "Very High R&D opportunity" means RDOpportunityBand = "Very High".
- "Contact Now" is SalesTimingBand = "Contact Now".
- Do not invent fields.
- Do not create SQL.

Follow-up rules:
- If a previous plan is supplied, treat it as the starting point.
- Return a COMPLETE revised plan, not just the changed part.
- "those", "them", "these", "only", "now", "also", "instead" and similar
  wording normally refer to the previous result set.
- "only ones with more than 20 employees" should KEEP all existing filters
  and add the employee filter.
- "sort those by turnover" should KEEP the existing filters and change the sort.
- "show me the top 5" should keep filters, use operation=list and set limit=5.
- "how many of those?" should keep filters and set operation=count.
- "show them" after a count should keep filters and set operation=list.
- If the user clearly starts a different search, create a new plan.
- If a follow-up requests a field that only exists in another dataset,
  move to the appropriate dataset where sensible and preserve compatible filters.
- For prospects, "strongest", "best" or "top opportunities" means sort first by
  RDOpportunityScore descending, then SalesTimingScore descending.
- For accountants, "strongest", "best" or "top opportunities" means sort first by
  ReferralOpportunityScore descending, then ContactNowClients descending.
- For general companies, do not invent a "strength" measure. If the user asks
  for strongest companies without mentioning R&D, prefer moving to prospects
  only if the previous context is clearly about R&D; otherwise preserve the
  company search and sort by Employees descending as a simple size proxy,
  explaining that interpretation.
"""

    previous_context = ""

    if previous_plan:
        previous_context = (
            "\n\nPREVIOUS QUERY PLAN:\n"
            + json.dumps(previous_plan, ensure_ascii=False, default=str)
            + "\n\nThe user's new message may be a follow-up. "
              "Apply the follow-up rules and return the full revised plan."
        )

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=system_prompt + previous_context,
        input=question
    )

    raw = response.output_text.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


def _add_ask_rebel_filter(dataset, field, operator, value, where_parts, params):
    """
    Add one validated filter to the SQL being constructed locally.
    Only allow-listed fields and operators can reach the database.
    """

    config = ASK_REBEL_DATASETS[dataset]
    real_fields = config["fields"]
    virtual_fields = config["virtual_fields"]

    if field not in real_fields and field not in virtual_fields:
        raise ValueError(f"Field '{field}' is not allowed for {dataset}.")

    allowed_operators = {"eq", "contains", "gte", "lte", "gt", "lt", "in"}

    if operator not in allowed_operators:
        raise ValueError(f"Operator '{operator}' is not allowed.")

    # Virtual search fields.
    if dataset == "companies" and field == "Location":
        if operator not in {"contains", "eq"}:
            raise ValueError("Location supports contains or eq.")
        if operator == "contains":
            search_value = f"%{value}%"
            where_parts.append(
                "(PostTown LIKE %s OR County LIKE %s OR PostCode LIKE %s)"
            )
            params.extend([search_value, search_value, search_value])
        else:
            where_parts.append(
                "(PostTown = %s OR County = %s OR PostCode = %s)"
            )
            params.extend([value, value, value])
        return

    if dataset == "companies" and field == "SIC":
        if operator not in {"contains", "eq"}:
            raise ValueError("SIC supports contains or eq.")
        if operator == "contains":
            search_value = f"%{value}%"
            where_parts.append(
                "(SIC1 LIKE %s OR SIC2 LIKE %s OR SIC3 LIKE %s OR SIC4 LIKE %s)"
            )
            params.extend(
                [search_value, search_value, search_value, search_value]
            )
        else:
            where_parts.append(
                "(SIC1 = %s OR SIC2 = %s OR SIC3 = %s OR SIC4 = %s)"
            )
            params.extend([value, value, value, value])
        return

    if dataset == "prospects" and field == "Location":
        if operator not in {"contains", "eq"}:
            raise ValueError("Location supports contains or eq.")
        if operator == "contains":
            search_value = f"%{value}%"
            where_parts.append(
                "(PostTown LIKE %s OR County LIKE %s OR PostCode LIKE %s)"
            )
            params.extend([search_value, search_value, search_value])
        else:
            where_parts.append(
                "(PostTown = %s OR County = %s OR PostCode = %s)"
            )
            params.extend([value, value, value])
        return

    if dataset == "prospects" and field == "Industry":
        if operator not in {"contains", "eq"}:
            raise ValueError("Industry supports contains or eq.")
        if operator == "contains":
            where_parts.append("BestSICDescription LIKE %s")
            params.append(f"%{value}%")
        else:
            where_parts.append("BestSICDescription = %s")
            params.append(value)
        return

    column = real_fields[field]

    if operator == "eq":
        where_parts.append(f"{column} = %s")
        params.append(value)

    elif operator == "contains":
        where_parts.append(f"{column} LIKE %s")
        params.append(f"%{value}%")

    elif operator == "gte":
        where_parts.append(f"{column} >= %s")
        params.append(value)

    elif operator == "lte":
        where_parts.append(f"{column} <= %s")
        params.append(value)

    elif operator == "gt":
        where_parts.append(f"{column} > %s")
        params.append(value)

    elif operator == "lt":
        where_parts.append(f"{column} < %s")
        params.append(value)

    elif operator == "in":
        if not isinstance(value, list) or len(value) == 0:
            raise ValueError("IN filters require a non-empty array.")
        if len(value) > 25:
            raise ValueError("Too many values supplied to an IN filter.")

        placeholders = ", ".join(["%s"] * len(value))
        where_parts.append(f"{column} IN ({placeholders})")
        params.extend(value)


def build_ask_rebel_query(plan):
    """
    Build SQL from a validated structured plan.
    The LLM never supplies SQL, table names or column expressions.
    """

    dataset = plan.get("dataset")

    if dataset not in ASK_REBEL_DATASETS:
        raise ValueError("Ask Rebel selected an unknown dataset.")

    config = ASK_REBEL_DATASETS[dataset]

    operation = plan.get("operation", "list")

    if operation not in {"list", "count"}:
        raise ValueError("Ask Rebel selected an invalid operation.")

    where_parts = []
    params = []

    filters = plan.get("filters") or []

    if len(filters) > 12:
        raise ValueError("Too many filters were generated.")

    for item in filters:
        _add_ask_rebel_filter(
            dataset=dataset,
            field=item.get("field"),
            operator=item.get("operator"),
            value=item.get("value"),
            where_parts=where_parts,
            params=params
        )

    where_sql = ""

    if where_parts:
        where_sql = " WHERE " + " AND ".join(where_parts)

    if operation == "count":
        sql = (
            f"SELECT COUNT_BIG(*) AS ResultCount "
            f"FROM {config['view']}"
            f"{where_sql}"
        )
        return sql, params

    try:
        limit = int(plan.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50

    limit = max(1, min(limit, 100))

    select_columns = ", ".join(config["default_columns"])

    sql = (
        f"SELECT TOP {limit} {select_columns} "
        f"FROM {config['view']}"
        f"{where_sql}"
    )

    order_parts = []

    for item in (plan.get("sort") or [])[:3]:
        field = item.get("field")
        direction = str(item.get("direction", "asc")).lower()

        if field not in config["fields"]:
            continue

        if direction not in {"asc", "desc"}:
            direction = "asc"

        order_parts.append(
            f"{config['fields'][field]} {direction.upper()}"
        )

    if order_parts:
        sql += " ORDER BY " + ", ".join(order_parts)

    else:
        if dataset in {"companies", "prospects"}:
            sql += " ORDER BY CompanyName, CompanyNumber"
        else:
            sql += " ORDER BY ReferralOpportunityScore DESC, AccountantName"

    return sql, params


def run_ask_rebel_query(plan):
    sql, params = build_ask_rebel_query(plan)

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))

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

    return results, sql



def create_company_report_pdf(detail, accounts_comparison=None):
    """Create a simple branded company report PDF in memory."""

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RebelTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "RebelSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#65a816"),
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        "RebelHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#222222"),
        spaceBefore=8,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        "RebelNormal",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333")
    )

    story = []

    story.append(
        Paragraph(
            f"Rebel Data - {display_value(detail.get('CompanyName'))}",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"Company Number: {display_value(detail.get('CompanyNumber'))}",
            subtitle_style
        )
    )

    def add_table(title, rows):
        story.append(Paragraph(title, heading_style))

        table_data = [
            [
                Paragraph("<b>Field</b>", normal_style),
                Paragraph("<b>Value</b>", normal_style)
            ]
        ]

        for label, value in rows:
            table_data.append(
                [
                    Paragraph(str(label), normal_style),
                    Paragraph(str(display_value(value)), normal_style)
                ]
            )

        table = Table(
            table_data,
            colWidths=[58 * mm, 112 * mm],
            repeatRows=1
        )

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#222222")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cccccc")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 5 * mm))

    address_parts = [
        detail.get("POBox"),
        detail.get("AddressLine1"),
        detail.get("AddressLine2"),
        detail.get("PostTown"),
        detail.get("County"),
        detail.get("Country"),
        detail.get("PostCode")
    ]

    address = ", ".join(
        str(x).strip()
        for x in address_parts
        if x is not None and str(x).strip()
    ) or "Not available"

    add_table(
        "Company",
        [
            ("Status", detail.get("CompanyStatus")),
            ("Employees", detail.get("Employees")),
            ("Category", detail.get("CompanyCategory")),
            ("Country of Origin", detail.get("CountryOfOrigin")),
            ("Incorporation Date", detail.get("IncorporationDate")),
            ("Registered Address", address),
        ]
    )

    sic_values = [
        detail.get("SIC1"),
        detail.get("SIC2"),
        detail.get("SIC3"),
        detail.get("SIC4")
    ]

    sic_text = "<br/>".join(
        str(x)
        for x in sic_values
        if x is not None and str(x).strip()
    ) or "Not available"

    add_table(
        "Industry and Advisers",
        [
            ("SIC", sic_text),
            ("Accountant", detail.get("AccountantName")),
            ("Auditor", detail.get("AuditorName")),
        ]
    )

    add_table(
        "Accounts",
        [
            ("Accounts Category", detail.get("AccountsCategory")),
            ("Accounts Last Made Up", detail.get("AccountsLastMadeUpDate")),
            ("Next Accounts Due", detail.get("AccountsNextDueDate")),
            ("Confirmation Statement Last Made Up", detail.get("ConfStmtLastMadeUpDate")),
            ("Confirmation Statement Next Due", detail.get("ConfStmtNextDueDate")),
        ]
    )

    add_table(
        "Mortgages",
        [
            ("Charges", detail.get("MortgagesNumCharges")),
            ("Outstanding", detail.get("MortgagesOutstanding")),
            ("Part Satisfied", detail.get("MortgagesPartSatisfied")),
            ("Satisfied", detail.get("MortgagesSatisfied")),
        ]
    )

    if accounts_comparison:
        financial_rows = [
            ("Latest Accounts Period End", accounts_comparison.get("LatestAccountsPeriodEnd")),
            ("Previous Accounts Period End", accounts_comparison.get("PreviousAccountsPeriodEnd")),
            ("Latest Employees", accounts_comparison.get("LatestEmployees")),
            ("Previous Employees", accounts_comparison.get("PreviousEmployees")),
            ("Latest Turnover", format_financial_value(accounts_comparison.get("LatestTurnover"))),
            ("Previous Turnover", format_financial_value(accounts_comparison.get("PreviousTurnover"))),
            ("Latest Profit Before Tax", format_financial_value(accounts_comparison.get("LatestProfitBeforeTax"))),
            ("Previous Profit Before Tax", format_financial_value(accounts_comparison.get("PreviousProfitBeforeTax"))),
            ("Latest Cash", format_financial_value(accounts_comparison.get("LatestCash"))),
            ("Previous Cash", format_financial_value(accounts_comparison.get("PreviousCash"))),
            ("Latest Net Assets", format_financial_value(accounts_comparison.get("LatestNetAssets"))),
            ("Previous Net Assets", format_financial_value(accounts_comparison.get("PreviousNetAssets"))),
            ("Latest Accountant", accounts_comparison.get("LatestAccountantName")),
            ("Previous Accountant", accounts_comparison.get("PreviousAccountantName")),
            ("Latest Auditor", accounts_comparison.get("LatestAuditorName")),
            ("Previous Auditor", accounts_comparison.get("PreviousAuditorName")),
        ]

        add_table(
            "Financial Comparison",
            financial_rows
        )

    story.append(
        Paragraph(
            "Source: Rebel Data business intelligence platform.",
            normal_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()



# ==================================================
# SIMILAR COMPANIES / MARKET PROFILE
# ==================================================

def get_employee_band_bounds(value):
    """
    Return a readable employee band plus its lower/upper bounds.
    The bands mirror the broad SME groupings used elsewhere in Rebel.
    """

    try:
        employees = int(value)
    except (TypeError, ValueError):
        return "Unknown", None, None

    if employees <= 0:
        return "Unknown", None, None
    if employees <= 5:
        return "1-5", 1, 5
    if employees <= 10:
        return "6-10", 6, 10
    if employees <= 19:
        return "11-19", 11, 19
    if employees <= 49:
        return "20-49", 20, 49
    if employees <= 99:
        return "50-99", 50, 99
    if employees <= 249:
        return "100-249", 100, 249
    if employees <= 499:
        return "250-499", 250, 499
    if employees <= 999:
        return "500-999", 500, 999

    return "1,000+", 1000, None


def get_primary_sic(detail):
    for field in ("SIC1", "SIC2", "SIC3", "SIC4"):
        value = detail.get(field)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def get_peer_market_profile(detail, peer_limit=25):
    """
    Find similar companies deterministically.

    Similarity is based on:
    - same SIC / industry
    - employee band
    - county
    - company category

    The LLM is not involved in the peer selection.
    """

    selected_number = str(detail.get("CompanyNumber") or "").strip()
    selected_sic = get_primary_sic(detail)

    if not selected_sic:
        return pd.DataFrame(), {
            "EmployeeBand": "Unknown",
            "PrimarySIC": None,
            "IndustryCompanies": 0,
            "SameEmployeeBand": 0,
            "SameCounty": 0,
            "SameCountyBand": 0,
            "AccountantIndustryClients": 0,
            "AccountantPeerClients": 0,
            "AccountantIndustryPenetrationPct": None,
            "AccountantPeerPenetrationPct": None
        }

    selected_county = str(detail.get("County") or "").strip()
    selected_category = str(detail.get("CompanyCategory") or "").strip()
    selected_accountant = str(detail.get("AccountantName") or "").strip()

    employee_band, emp_min, emp_max = get_employee_band_bounds(
        detail.get("Employees")
    )

    same_sic_where = """
        (
            SIC1 = %s
            OR SIC2 = %s
            OR SIC3 = %s
            OR SIC4 = %s
        )
    """

    # Build a deterministic similarity score.
    score_parts = [
        "CASE WHEN SIC1 = %s THEN 50 ELSE 40 END"
    ]
    score_params = [selected_sic]

    if emp_min is not None:
        if emp_max is None:
            emp_condition = "TRY_CONVERT(INT, Employees) >= %s"
            emp_params = [emp_min]
        else:
            emp_condition = "TRY_CONVERT(INT, Employees) BETWEEN %s AND %s"
            emp_params = [emp_min, emp_max]

        score_parts.append(
            f"CASE WHEN {emp_condition} THEN 25 ELSE 0 END"
        )
        score_params.extend(emp_params)

    if selected_county:
        score_parts.append(
            "CASE WHEN County = %s THEN 15 ELSE 0 END"
        )
        score_params.append(selected_county)

    if selected_category:
        score_parts.append(
            "CASE WHEN CompanyCategory = %s THEN 10 ELSE 0 END"
        )
        score_params.append(selected_category)

    score_sql = " + ".join(score_parts)

    peer_sql = f"""
        SELECT TOP {int(peer_limit)}
            CompanyNumber,
            CompanyName,
            PostTown,
            County,
            TRY_CONVERT(INT, Employees) AS Employees,
            SIC1,
            AccountantName,
            AuditorName,
            ({score_sql}) AS SimilarityScore
        FROM dbo.vw_RebelCompanies
        WHERE
            CompanyNumber <> %s
            AND CompanyStatus = 'Active'
            AND {same_sic_where}
        ORDER BY
            SimilarityScore DESC,
            TRY_CONVERT(INT, Employees) DESC,
            CompanyName
    """

    peer_params = (
        score_params
        + [selected_number]
        + [selected_sic] * 4
    )

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            peer_sql,
            tuple(peer_params)
        )

        peer_rows = cursor.fetchall()
        peer_columns = [
            column[0]
            for column in cursor.description
        ]

        peers = pd.DataFrame(
            peer_rows,
            columns=peer_columns
        )

        # Market profile in one scan of the matching industry.
        band_condition = None
        band_params = []

        if emp_min is not None:
            if emp_max is None:
                band_condition = (
                    "TRY_CONVERT(INT, Employees) >= %s"
                )
                band_params = [emp_min]
            else:
                band_condition = (
                    "TRY_CONVERT(INT, Employees) BETWEEN %s AND %s"
                )
                band_params = [emp_min, emp_max]

        select_parts = [
            "COUNT_BIG(*) AS IndustryCompanies"
        ]
        market_params = []

        if band_condition:
            select_parts.append(
                f"SUM(CASE WHEN {band_condition} THEN 1 ELSE 0 END) "
                "AS SameEmployeeBand"
            )
            market_params.extend(band_params)
        else:
            select_parts.append(
                "CAST(0 AS BIGINT) AS SameEmployeeBand"
            )

        if selected_county:
            select_parts.append(
                "SUM(CASE WHEN County = %s THEN 1 ELSE 0 END) "
                "AS SameCounty"
            )
            market_params.append(selected_county)
        else:
            select_parts.append(
                "CAST(0 AS BIGINT) AS SameCounty"
            )

        if selected_county and band_condition:
            select_parts.append(
                f"SUM(CASE WHEN County = %s AND {band_condition} "
                "THEN 1 ELSE 0 END) AS SameCountyBand"
            )
            market_params.append(selected_county)
            market_params.extend(band_params)
        else:
            select_parts.append(
                "CAST(0 AS BIGINT) AS SameCountyBand"
            )

        if selected_accountant:
            select_parts.append(
                "SUM(CASE WHEN AccountantName = %s THEN 1 ELSE 0 END) "
                "AS AccountantIndustryClients"
            )
            market_params.append(selected_accountant)
        else:
            select_parts.append(
                "CAST(0 AS BIGINT) AS AccountantIndustryClients"
            )

        if selected_accountant and band_condition:
            select_parts.append(
                f"SUM(CASE WHEN AccountantName = %s AND {band_condition} "
                "THEN 1 ELSE 0 END) AS AccountantPeerClients"
            )
            market_params.append(selected_accountant)
            market_params.extend(band_params)
        else:
            select_parts.append(
                "CAST(0 AS BIGINT) AS AccountantPeerClients"
            )

        market_sql = f"""
            SELECT
                {", ".join(select_parts)}
            FROM dbo.vw_RebelCompanies
            WHERE
                CompanyStatus = 'Active'
                AND {same_sic_where}
        """

        market_params.extend(
            [selected_sic] * 4
        )

        cursor.execute(
            market_sql,
            tuple(market_params)
        )

        market_row = cursor.fetchone()
        market_columns = [
            column[0]
            for column in cursor.description
        ]

        market = dict(
            zip(
                market_columns,
                market_row
            )
        )

        cursor.close()

    finally:
        conn.close()

    market["EmployeeBand"] = employee_band
    market["PrimarySIC"] = selected_sic

    industry_total = int(
        market.get("IndustryCompanies") or 0
    )
    band_total = int(
        market.get("SameEmployeeBand") or 0
    )
    accountant_industry = int(
        market.get("AccountantIndustryClients") or 0
    )
    accountant_peer = int(
        market.get("AccountantPeerClients") or 0
    )

    market["AccountantIndustryPenetrationPct"] = (
        accountant_industry / industry_total * 100
        if selected_accountant and industry_total
        else None
    )

    market["AccountantPeerPenetrationPct"] = (
        accountant_peer / band_total * 100
        if selected_accountant and band_total
        else None
    )

    # Add latest financial measures for the similar-company table.
    if not peers.empty and "CompanyNumber" in peers.columns:

        peer_numbers = [
            str(value).strip()
            for value in peers["CompanyNumber"].tolist()
            if value is not None and str(value).strip()
        ]

        if peer_numbers:
            placeholders = ", ".join(
                ["%s"] * len(peer_numbers)
            )

            conn = get_connection()

            try:
                cursor = conn.cursor()

                cursor.execute(
                    f"""
                    SELECT
                        LTRIM(RTRIM(CRO)) AS CompanyNumber,
                        LatestEmployees,
                        LatestTurnover,
                        LatestProfitBeforeTax,
                        LatestCash,
                        EmployeeGrowthPct,
                        TurnoverGrowthPct
                    FROM dbo.RD_AccountsComparison
                    WHERE LTRIM(RTRIM(CRO)) IN ({placeholders})
                    """,
                    tuple(peer_numbers)
                )

                rows = cursor.fetchall()
                columns = [
                    column[0]
                    for column in cursor.description
                ]

                financials = pd.DataFrame(
                    rows,
                    columns=columns
                )

                cursor.close()

            finally:
                conn.close()

            if not financials.empty:
                peers["CompanyNumber"] = peers[
                    "CompanyNumber"
                ].astype(str).str.strip()

                financials["CompanyNumber"] = financials[
                    "CompanyNumber"
                ].astype(str).str.strip()

                peers = peers.merge(
                    financials,
                    on="CompanyNumber",
                    how="left"
                )

    return peers, market


def create_peer_market_pdf(detail, peers, market):
    """
    Create a Rebel-branded peer and market profile PDF.
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=13 * mm,
        leftMargin=13 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PeerTitle",
        parent=styles["Title"],
        fontSize=19,
        leading=23,
        textColor=colors.HexColor("#222222"),
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        "PeerSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#65a816"),
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        "PeerHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#222222"),
        spaceBefore=8,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        "PeerNormal",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#333333")
    )

    story = []

    story.append(
        Paragraph(
            "Rebel Data - Peer & Market Profile",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"{display_value(detail.get('CompanyName'))} "
            f"({display_value(detail.get('CompanyNumber'))})",
            subtitle_style
        )
    )

    market_rows = [
        ["Measure", "Value"],
        ["Primary industry / SIC", display_value(market.get("PrimarySIC"))],
        ["Employee band", display_value(market.get("EmployeeBand"))],
        ["Active companies in same industry", f"{int(market.get('IndustryCompanies') or 0):,}"],
        ["Same employee band", f"{int(market.get('SameEmployeeBand') or 0):,}"],
        ["Same county", f"{int(market.get('SameCounty') or 0):,}"],
        ["Same county and employee band", f"{int(market.get('SameCountyBand') or 0):,}"],
    ]

    accountant = str(
        detail.get("AccountantName") or ""
    ).strip()

    if accountant:
        industry_pen = market.get(
            "AccountantIndustryPenetrationPct"
        )
        peer_pen = market.get(
            "AccountantPeerPenetrationPct"
        )

        market_rows.extend(
            [
                ["Identified accountant", accountant],
                [
                    "Accountant share of same industry",
                    (
                        f"{industry_pen:.2f}%"
                        if industry_pen is not None
                        else "Not available"
                    )
                ],
                [
                    "Accountant share of same industry + employee band",
                    (
                        f"{peer_pen:.2f}%"
                        if peer_pen is not None
                        else "Not available"
                    )
                ]
            ]
        )

    story.append(
        Paragraph(
            "Market Profile",
            heading_style
        )
    )

    market_table = Table(
        market_rows,
        colWidths=[83 * mm, 92 * mm],
        repeatRows=1
    )

    market_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(market_table)
    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "Similar Companies",
            heading_style
        )
    )

    if peers is None or peers.empty:
        story.append(
            Paragraph(
                "No suitable similar companies were found.",
                normal_style
            )
        )
    else:
        peer_rows = [
            [
                "Company",
                "Town",
                "Employees",
                "Turnover",
                "Similarity"
            ]
        ]

        for _, row in peers.head(15).iterrows():
            peer_rows.append(
                [
                    str(row.get("CompanyName") or ""),
                    str(row.get("PostTown") or ""),
                    (
                        f"{float(row.get('Employees')):,.0f}"
                        if pd.notna(row.get("Employees"))
                        else ""
                    ),
                    (
                        format_financial_value(
                            row.get("LatestTurnover")
                        )
                        if "LatestTurnover" in peers.columns
                        else ""
                    ),
                    (
                        f"{float(row.get('SimilarityScore')):.0f}%"
                        if pd.notna(row.get("SimilarityScore"))
                        else ""
                    ),
                ]
            )

        peer_table = Table(
            peer_rows,
            colWidths=[
                67 * mm,
                35 * mm,
                23 * mm,
                31 * mm,
                20 * mm
            ],
            repeatRows=1
        )

        peer_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        story.append(peer_table)

    story.append(Spacer(1, 4 * mm))

    story.append(
        Paragraph(
            "Similarity is calculated consistently from industry, employee band, "
            "location and company category. Accountant penetration is an estimated "
            "share based on accountant relationships identified in Rebel Data, not "
            "a claim of total market share.",
            normal_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()


def show_peer_market_profile(detail):
    """
    Render peer companies and market profile below the selected company.
    """

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Similar Companies & Market Profile</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Peers are selected using Rebel's deterministic similarity logic, "
        "not generated by the AI."
    )

    with st.spinner(
        "Building peer and market profile..."
    ):
        peers, market = get_peer_market_profile(
            detail,
            peer_limit=25
        )

    if not market.get("PrimarySIC"):
        st.info(
            "A peer profile cannot be created because this company "
            "does not currently have a usable SIC classification."
        )
        return

    industry_count = int(
        market.get("IndustryCompanies") or 0
    )
    band_count = int(
        market.get("SameEmployeeBand") or 0
    )
    county_count = int(
        market.get("SameCounty") or 0
    )
    county_band_count = int(
        market.get("SameCountyBand") or 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Same Industry",
        f"{industry_count:,}"
    )

    col2.metric(
        f"Employees {market.get('EmployeeBand')}",
        f"{band_count:,}"
    )

    col3.metric(
        "Same County",
        f"{county_count:,}"
    )

    col4.metric(
        "Same County + Size",
        f"{county_band_count:,}"
    )

    st.markdown("### Market definition")

    st.write(
        f"**Primary industry:** {display_value(market.get('PrimarySIC'))}"
    )

    st.write(
        f"**Employee band:** {display_value(market.get('EmployeeBand'))}"
    )

    accountant = str(
        detail.get("AccountantName") or ""
    ).strip()

    if accountant:

        st.markdown("### Accountant penetration")

        industry_clients = int(
            market.get("AccountantIndustryClients") or 0
        )
        peer_clients = int(
            market.get("AccountantPeerClients") or 0
        )

        industry_pen = market.get(
            "AccountantIndustryPenetrationPct"
        )
        peer_pen = market.get(
            "AccountantPeerPenetrationPct"
        )

        p1, p2 = st.columns(2)

        p1.metric(
            "Same Industry",
            (
                f"{industry_pen:.2f}%"
                if industry_pen is not None
                else "N/A"
            ),
            delta=f"{industry_clients:,} identified clients"
        )

        p2.metric(
            "Same Industry + Size",
            (
                f"{peer_pen:.2f}%"
                if peer_pen is not None
                else "N/A"
            ),
            delta=f"{peer_clients:,} identified clients"
        )

        st.caption(
            "Penetration is based on companies where Rebel has identified "
            f"{accountant} as the accountant. It is an indicative Rebel Data "
            "measure rather than a claim of the firm's total market share."
        )

    st.markdown("### Most Similar Companies")

    if peers.empty:
        st.info(
            "No suitable similar active companies were found."
        )
    else:

        display_df = peers.copy()

        if "SimilarityScore" in display_df.columns:
            display_df["Similarity"] = display_df[
                "SimilarityScore"
            ].apply(
                lambda value: (
                    f"{float(value):.0f}%"
                    if pd.notna(value)
                    else ""
                )
            )

        if "LatestTurnover" in display_df.columns:
            display_df["Turnover"] = display_df[
                "LatestTurnover"
            ].apply(
                lambda value: (
                    format_financial_value(value)
                    if pd.notna(value)
                    else ""
                )
            )

        if "LatestProfitBeforeTax" in display_df.columns:
            display_df["Profit Before Tax"] = display_df[
                "LatestProfitBeforeTax"
            ].apply(
                lambda value: (
                    format_financial_value(value)
                    if pd.notna(value)
                    else ""
                )
            )

        desired_columns = [
            "CompanyNumber",
            "CompanyName",
            "PostTown",
            "County",
            "Employees",
            "Turnover",
            "Profit Before Tax",
            "AccountantName",
            "Similarity"
        ]

        desired_columns = [
            column
            for column in desired_columns
            if column in display_df.columns
        ]

        st.dataframe(
            display_df[desired_columns],
            use_container_width=True,
            hide_index=True,
            height=500
        )

        peer_csv = (
            display_df[desired_columns]
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "DOWNLOAD SIMILAR COMPANIES CSV",
            data=peer_csv,
            file_name=(
                f"similar_companies_"
                f"{detail.get('CompanyNumber')}.csv"
            ),
            mime="text/csv",
            key=(
                f"similar_companies_csv_"
                f"{detail.get('CompanyNumber')}"
            )
        )

    try:
        peer_pdf = create_peer_market_pdf(
            detail,
            peers,
            market
        )

        safe_company_name = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            str(
                detail.get("CompanyName")
                or detail.get("CompanyNumber")
            )
        ).strip("_")

        st.download_button(
            "DOWNLOAD PEER & MARKET PROFILE PDF",
            data=peer_pdf,
            file_name=(
                f"Rebel_Peer_Market_Profile_"
                f"{safe_company_name}_"
                f"{detail.get('CompanyNumber')}.pdf"
            ),
            mime="application/pdf",
            key=(
                f"peer_market_pdf_"
                f"{detail.get('CompanyNumber')}"
            )
        )

    except Exception as peer_pdf_error:
        st.warning(
            "The peer and market profile PDF could not be generated."
        )
        st.exception(peer_pdf_error)


def show_ask_rebel_company_detail(selected_number):
    """Show the same core company intelligence used in Company Search."""

    if (
        st.session_state.get("last_viewed_company")
        != selected_number
    ):
        log_activity(
            "COMPANY_VIEW",
            company_viewed=selected_number
        )

        st.session_state["last_viewed_company"] = selected_number

    with st.spinner("Loading company details..."):
        detail = get_company_detail(selected_number)

    if not detail:
        st.warning("No company detail was found for this company.")
        return

    st.markdown("<hr>", unsafe_allow_html=True)

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

    st.subheader("Company")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Status",
        display_value(detail["CompanyStatus"])
    )

    col2.metric(
        "Employees",
        display_value(detail["Employees"])
    )

    col3.metric(
        "Category",
        display_value(detail["CompanyCategory"])
    )

    col4.metric(
        "Country of Origin",
        display_value(detail["CountryOfOrigin"])
    )

    st.subheader("Important Dates")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Incorporated**")
        st.write(display_value(detail["IncorporationDate"]))

    with col2:
        st.write("**Accounts Last Made Up**")
        st.write(display_value(detail["AccountsLastMadeUpDate"]))

    with col3:
        st.write("**Confirmation Statement Last Made Up**")
        st.write(display_value(detail["ConfStmtLastMadeUpDate"]))

    st.subheader("Registered Address")

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
        if x is not None and str(x).strip() != ""
    ]

    st.write(
        ", ".join(address_parts)
        if address_parts
        else "Not available"
    )

    st.subheader("Industry")

    sic_values = [
        detail["SIC1"],
        detail["SIC2"],
        detail["SIC3"],
        detail["SIC4"]
    ]

    sic_values = [
        str(x).strip()
        for x in sic_values
        if x is not None and str(x).strip() != ""
    ]

    if sic_values:
        for sic_value in sic_values:
            st.write(f"• {sic_value}")
    else:
        st.write("No SIC information available.")

    st.subheader("Professional Advisers")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Accountant**")
        st.write(display_value(detail["AccountantName"]))

    with col2:
        st.write("**Auditor**")
        st.write(display_value(detail["AuditorName"]))

    st.subheader("Accounts")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Accounts Category**")
        st.write(display_value(detail["AccountsCategory"]))

    with col2:
        st.write("**Next Accounts Due**")
        st.write(display_value(detail["AccountsNextDueDate"]))

    with col3:
        st.write("**Last Accounts**")
        st.write(display_value(detail["AccountsLastMadeUpDate"]))

    st.subheader("Mortgages")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Charges",
        display_value(detail["MortgagesNumCharges"])
    )

    col2.metric(
        "Outstanding",
        display_value(detail["MortgagesOutstanding"])
    )

    col3.metric(
        "Part Satisfied",
        display_value(detail["MortgagesPartSatisfied"])
    )

    col4.metric(
        "Satisfied",
        display_value(detail["MortgagesSatisfied"])
    )

    accounts_comparison = None

    try:
        with st.spinner("Loading financial comparison..."):
            accounts_comparison = get_accounts_comparison(selected_number)

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

    try:
        show_peer_market_profile(detail)
    except Exception as peer_profile_error:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">Similar Companies & Market Profile</div>',
            unsafe_allow_html=True
        )
        st.warning(
            "The company details loaded, but the peer and market profile "
            "could not be generated."
        )
        st.exception(peer_profile_error)

    try:
        pdf_bytes = create_company_report_pdf(
            detail,
            accounts_comparison
        )

        safe_company_name = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            str(detail.get("CompanyName") or selected_number)
        ).strip("_")

        st.download_button(
            label="DOWNLOAD COMPANY REPORT PDF",
            data=pdf_bytes,
            file_name=f"Rebel_Data_{safe_company_name}_{selected_number}.pdf",
            mime="application/pdf",
            key=f"ask_rebel_company_pdf_{selected_number}"
        )

    except Exception as pdf_error:
        st.warning("The company report PDF could not be generated.")
        st.exception(pdf_error)


def show_ask_rebel_page():

    st.markdown(
        """
        <div class="hero-title">
            Ask Rebel
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero-subtitle">
            Ask questions about UK companies, R&D prospects and accountant opportunities in plain English.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="
            background:#333335;
            border-left:4px solid #8bd02f;
            padding:14px 18px;
            border-radius:6px;
            color:#d9d9d9;
            margin-bottom:18px;
            line-height:1.6;
        ">
            Start with a search, then refine it naturally.<br>
            Example: <b style="color:white;">Show high R&amp;D opportunity companies in Gloucestershire</b><br>
            Then: <b style="color:white;">Only ones with more than 20 employees</b><br>
            Then: <b style="color:white;">Sort those by turnover</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
        /* Ask Rebel question box only */
        div[data-testid="stForm"]:has(textarea[aria-label="Ask Rebel a question"]) textarea {
            color: #000000 !important;
            background-color: #ffffff !important;
            -webkit-text-fill-color: #000000 !important;
        }

        div[data-testid="stForm"]:has(textarea[aria-label="Ask Rebel a question"]) textarea::placeholder {
            color: #777777 !important;
            -webkit-text-fill-color: #777777 !important;
            opacity: 1 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # -------------------------
    # Conversation controls
    # -------------------------
    control_col1, control_col2 = st.columns([1.2, 5])

    with control_col1:
        if st.button(
            "NEW SEARCH",
            key="ask_rebel_new_search",
            use_container_width=True
        ):
            st.session_state["ask_rebel_question"] = None
            st.session_state["ask_rebel_plan"] = None
            st.session_state["ask_rebel_results"] = None
            st.session_state["ask_rebel_generated_sql"] = None
            st.session_state["ask_rebel_selected_company"] = None
            st.session_state["ask_rebel_conversation"] = []
            st.rerun()

    conversation = st.session_state.get(
        "ask_rebel_conversation",
        []
    )

    if conversation:
        with st.expander(
            f"Conversation ({len(conversation)} messages)",
            expanded=False
        ):
            for message in conversation:
                role = message.get("role")

                if role == "user":
                    st.markdown(
                        f"**You:** {message.get('text', '')}"
                    )
                else:
                    st.markdown(
                        f"**Ask Rebel:** {message.get('text', '')}"
                    )

    # -------------------------
    # Ask / follow-up form
    # -------------------------
    has_existing_search = (
        st.session_state.get("ask_rebel_plan") is not None
    )

    form_label = (
        "Ask a follow-up question"
        if has_existing_search
        else "Ask Rebel a question"
    )

    placeholder = (
        "e.g. Only ones with more than 20 employees"
        if has_existing_search
        else "e.g. Find active manufacturing companies in Gloucestershire with more than 20 employees"
    )

    with st.form(
        "ask_rebel_form",
        clear_on_submit=True
    ):

        question = st.text_area(
            "Ask Rebel a question",
            placeholder=placeholder,
            height=100,
            label_visibility="collapsed"
        )

        ask_clicked = st.form_submit_button(
            "ASK REBEL"
        )

    if has_existing_search:
        st.caption(
            "Ask Rebel will treat this as a follow-up to the current result set. "
            "Use NEW SEARCH to start again."
        )

    # -------------------------
    # Execute a question
    # -------------------------
    if ask_clicked:

        question = (question or "").strip()

        if not question:
            st.warning("Enter a question for Ask Rebel.")
        else:
            try:

                previous_plan = st.session_state.get(
                    "ask_rebel_plan"
                )

                with st.spinner(
                    "Ask Rebel is interpreting your question..."
                ):

                    plan = ask_rebel_plan(
                        question,
                        previous_plan=previous_plan
                    )

                    results, generated_sql = run_ask_rebel_query(
                        plan
                    )

                st.session_state["ask_rebel_question"] = question
                st.session_state["ask_rebel_plan"] = plan
                st.session_state["ask_rebel_results"] = results
                st.session_state["ask_rebel_generated_sql"] = generated_sql
                st.session_state["ask_rebel_selected_company"] = None

                conversation = st.session_state.get(
                    "ask_rebel_conversation",
                    []
                )

                conversation.append(
                    {
                        "role": "user",
                        "text": question
                    }
                )

                if plan.get("operation") == "count":
                    result_value = (
                        int(results.iloc[0, 0])
                        if len(results) > 0
                        else 0
                    )

                    reply_text = (
                        f"{plan.get('interpretation', 'Query completed.')} "
                        f"Result: {result_value:,}."
                    )
                else:
                    reply_text = (
                        f"{plan.get('interpretation', 'Query completed.')} "
                        f"I found {len(results):,} matching records."
                    )

                conversation.append(
                    {
                        "role": "assistant",
                        "text": reply_text
                    }
                )

                # Keep session history compact.
                st.session_state["ask_rebel_conversation"] = (
                    conversation[-20:]
                )

                log_activity(
                    "ASK_REBEL",
                    result_count=(
                        int(results.iloc[0, 0])
                        if plan.get("operation") == "count"
                        and len(results) > 0
                        else len(results)
                    )
                )

                st.rerun()

            except json.JSONDecodeError:
                st.error(
                    "Ask Rebel could not interpret the question into a valid query plan. "
                    "Try wording the question a little more simply."
                )

            except Exception as e:
                st.error(
                    "Ask Rebel could not complete the request."
                )
                st.exception(e)

    # -------------------------
    # Current result
    # -------------------------
    plan = st.session_state.get("ask_rebel_plan")
    results = st.session_state.get("ask_rebel_results")
    generated_sql = st.session_state.get(
        "ask_rebel_generated_sql"
    )

    if plan is None or results is None:
        return

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-title">
            Current Result
        </div>
        """,
        unsafe_allow_html=True
    )

    interpretation = plan.get(
        "interpretation",
        "No interpretation was supplied."
    )

    st.markdown(
        f"""
        <div style="
            background:#333335;
            padding:12px 16px;
            border-radius:6px;
            margin-bottom:16px;
            color:#d9d9d9;
        ">
            <b style="color:white;">How Rebel interpreted this:</b>
            {interpretation}
        </div>
        """,
        unsafe_allow_html=True
    )

    if plan.get("operation") == "count":

        count_value = (
            int(results.iloc[0, 0])
            if len(results) > 0
            else 0
        )

        st.metric(
            "RESULT",
            f"{count_value:,}"
        )

        st.caption(
            "You can now ask a follow-up such as 'show them' or add another filter."
        )

    else:

        st.write(
            f"Ask Rebel returned **{len(results):,}** matching records."
        )

        if len(results) > 0:

            st.dataframe(
                results,
                use_container_width=True,
                hide_index=True,
                height=500
            )

            csv = (
                results
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                "DOWNLOAD RESULTS CSV",
                data=csv,
                file_name="ask_rebel_results.csv",
                mime="text/csv",
                key="ask_rebel_download"
            )

            dataset = plan.get("dataset")

            if (
                dataset == "accountants"
                and "AccountantName" in results.columns
            ):

                st.markdown("<hr>", unsafe_allow_html=True)

                st.markdown(
                    """
                    <div class="section-title">
                        Accountancy Profile
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                accountant_choices = [
                    str(value).strip()
                    for value in results["AccountantName"].tolist()
                    if value is not None
                    and str(value).strip()
                ]

                selected_ask_accountant = st.selectbox(
                    "Select an accountant from the Ask Rebel results",
                    ["Select an accountant..."] + accountant_choices,
                    key="ask_rebel_accountant_profile_choice"
                )

                if selected_ask_accountant != "Select an accountant...":
                    try:
                        show_accountancy_profile(
                            selected_ask_accountant,
                            key_prefix="ask_rebel_accountancy_profile"
                        )
                    except Exception as profile_error:
                        st.warning(
                            "The accountant was selected, but the accountancy "
                            "profile could not be generated."
                        )
                        st.exception(profile_error)

            if (
                dataset in {"companies", "prospects"}
                and "CompanyNumber" in results.columns
                and "CompanyName" in results.columns
            ):

                st.markdown("<hr>", unsafe_allow_html=True)

                st.markdown(
                    """
                    <div class="section-title">
                        Company Details
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                company_choices = {
                    f"{row['CompanyName']} ({row['CompanyNumber']})":
                    row["CompanyNumber"]
                    for _, row in results.iterrows()
                }

                choice_labels = [
                    "Select a company..."
                ] + list(company_choices.keys())

                selected_number_state = st.session_state.get(
                    "ask_rebel_selected_company"
                )

                default_index = 0

                if selected_number_state:
                    for idx, label in enumerate(choice_labels):
                        if (
                            label != "Select a company..."
                            and company_choices.get(label)
                            == selected_number_state
                        ):
                            default_index = idx
                            break

                detail_choice = st.selectbox(
                    "Select a company from the Ask Rebel results",
                    choice_labels,
                    index=default_index,
                    key="ask_rebel_company_detail_choice"
                )

                if detail_choice != "Select a company...":

                    selected_number = company_choices[
                        detail_choice
                    ]

                    st.session_state[
                        "ask_rebel_selected_company"
                    ] = selected_number

                    try:
                        show_ask_rebel_company_detail(
                            selected_number
                        )
                    except Exception as e:
                        st.error(
                            "The company was selected, but the full company detail could not be loaded."
                        )
                        st.exception(e)

        else:
            st.info(
                "No records matched the question as interpreted."
            )

    with st.expander("Technical details"):

        st.write(
            f"**Dataset:** {plan.get('dataset')}"
        )

        st.write(
            f"**Operation:** {plan.get('operation')}"
        )

        if plan.get("filters"):
            st.write("**Filters:**")

            for item in plan["filters"]:
                st.write(
                    f"- {item.get('field')} "
                    f"{item.get('operator')} "
                    f"{item.get('value')}"
                )

        if plan.get("sort"):
            st.write("**Sort:**")

            for item in plan["sort"]:
                st.write(
                    f"- {item.get('field')} "
                    f"{item.get('direction')}"
                )

        if generated_sql:
            st.code(
                generated_sql,
                language="sql"
            )



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
# ACCOUNTANT REPORT MAP / PDF HELPERS
# ==================================================

REBEL_GREEN = "#8bd02f"
REBEL_DARK = "#3d3d3f"
REBEL_LIGHT_GREY = "#d2d2d2"

POSTCODE_AREA_GEOJSON_URL = (
    "https://gist.githubusercontent.com/cgddrd/"
    "1a34e6ca8c5c2f8731346a5ff24fe1c9/raw/"
    "ec220207dbf2685ca6bc6df7042cd803d6260bb3/"
    "uk-postcode-areas.geojson"
)


def normalise_postcode(value):

    if value is None:
        return None

    postcode = str(value).strip().upper()

    if postcode == "":
        return None

    return postcode


def get_postcode_area(value):

    """
    Extract the UK postcode area from a postcode.

    Examples:
        GL1 2AA   -> GL
        SW1A 1AA  -> SW
        B1 1AA    -> B
    """

    postcode = normalise_postcode(
        value
    )

    if not postcode:
        return None

    compact = postcode.replace(
        " ",
        ""
    )

    match = re.match(
        r"^(GIR|[A-Z]{1,2})",
        compact
    )

    if not match:
        return None

    return match.group(1)


@st.cache_data(ttl=604800, show_spinner=False)
def get_postcode_area_geojson():

    """
    Load postcode-area boundary polygons.

    The GeoJSON contains UK postcode-area boundaries. It is cached
    for seven days so normal app use does not repeatedly download it.
    """

    response = requests.get(
        POSTCODE_AREA_GEOJSON_URL,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def build_postcode_area_counts(
    clients
):

    if (
        clients is None
        or len(clients) == 0
        or "Postcode" not in clients.columns
    ):

        return pd.DataFrame(
            columns=[
                "Postcode Area",
                "Clients"
            ]
        )

    areas = clients[
        "Postcode"
    ].apply(
        get_postcode_area
    )

    counts = (
        areas
        .dropna()
        .value_counts()
        .rename_axis(
            "Postcode Area"
        )
        .reset_index(
            name="Clients"
        )
    )

    return counts


def _geometry_polygons(
    geometry
):

    """
    Yield exterior polygon coordinate arrays from GeoJSON Polygon
    and MultiPolygon geometries.
    """

    if not geometry:
        return

    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates",
        []
    )

    if geometry_type == "Polygon":

        if coordinates:
            yield coordinates[0]

    elif geometry_type == "MultiPolygon":

        for polygon in coordinates:

            if polygon:
                yield polygon[0]


def create_postcode_area_map_figure(
    area_counts,
    accountant_name
):

    """
    Create a postcode-area choropleth for the selected accountant.

    Improvements:
    - strong Rebel green contrast
    - discrete client-count bands
    - London shown in a separate panel so it does not cover the UK map
    - same figure is used in the app and downloadable PDF
    """

    from matplotlib.patches import Polygon as MplPolygon, Rectangle
    from matplotlib.colors import ListedColormap, BoundaryNorm

    geojson = get_postcode_area_geojson()

    count_lookup = {}

    if (
        area_counts is not None
        and len(area_counts) > 0
    ):

        count_lookup = {
            str(row["Postcode Area"]).strip().upper():
            int(row["Clients"])
            for _, row in area_counts.iterrows()
        }

    colours = [
        "#4a4a4c",   # 0
        "#1f6f4a",   # 1-4
        "#2f9654",   # 5-9
        "#55b947",   # 10-19
        "#86d52f",   # 20-49
        "#d8f21e"    # 50+
    ]

    boundaries = [
        -0.5,
        0.5,
        4.5,
        9.5,
        19.5,
        49.5,
        1000000
    ]

    cmap = ListedColormap(
        colours
    )

    norm = BoundaryNorm(
        boundaries,
        cmap.N
    )

    # Separate national map and London panel.
    fig = plt.figure(
        figsize=(10.4, 8.6)
    )

    fig.patch.set_facecolor(
        REBEL_DARK
    )

    grid = fig.add_gridspec(
        1,
        2,
        width_ratios=[
            2.3,
            1
        ],
        wspace=0.05
    )

    ax = fig.add_subplot(
        grid[0, 0]
    )

    london_ax = fig.add_subplot(
        grid[0, 1]
    )

    ax.set_facecolor(
        REBEL_DARK
    )

    london_ax.set_facecolor(
        "#2f2f31"
    )

    feature_polygons = []

    for feature in geojson.get(
        "features",
        []
    ):

        properties = feature.get(
            "properties",
            {}
        )

        area = str(
            properties.get(
                "name",
                ""
            )
        ).strip().upper()

        client_count = count_lookup.get(
            area,
            0
        )

        geometry = feature.get(
            "geometry"
        )

        polygons = list(
            _geometry_polygons(
                geometry
            )
        )

        feature_polygons.append(
            (
                area,
                client_count,
                polygons
            )
        )

        # National map
        for polygon in polygons:

            if not polygon:
                continue

            points = [
                (
                    float(point[0]),
                    float(point[1])
                )
                for point in polygon
            ]

            patch = MplPolygon(
                points,
                closed=True,
                facecolor=cmap(
                    norm(
                        client_count
                    )
                ),
                edgecolor="#c6c6c8",
                linewidth=0.38,
                zorder=2
            )

            ax.add_patch(
                patch
            )

            # Draw same polygons in London panel.
            london_patch = MplPolygon(
                points,
                closed=True,
                facecolor=cmap(
                    norm(
                        client_count
                    )
                ),
                edgecolor="white",
                linewidth=0.75,
                zorder=2
            )

            london_ax.add_patch(
                london_patch
            )

    # National map framing.
    ax.set_xlim(
        -8.9,
        2.1
    )

    ax.set_ylim(
        49.7,
        61.1
    )

    ax.set_aspect(
        "equal",
        adjustable="box"
    )

    ax.axis(
        "off"
    )

    # London panel framing.
    london_ax.set_xlim(
        -0.65,
        0.35
    )

    london_ax.set_ylim(
        51.25,
        51.75
    )

    london_ax.set_aspect(
        "equal",
        adjustable="box"
    )

    london_ax.set_xticks(
        []
    )

    london_ax.set_yticks(
        []
    )

    for spine in london_ax.spines.values():

        spine.set_edgecolor(
            "white"
        )

        spine.set_linewidth(
            1.2
        )

    london_ax.set_title(
        "LONDON AREA",
        color="white",
        fontsize=11,
        fontweight="bold",
        pad=8
    )

    # Show the London extent on the main UK map.
    london_box = Rectangle(
        (-0.65, 51.25),
        1.0,
        0.50,
        fill=False,
        edgecolor="white",
        linewidth=1.1,
        linestyle="--",
        zorder=5
    )

    ax.add_patch(
        london_box
    )

    fig.suptitle(
        f"{accountant_name}\nClient distribution by postcode area",
        color="white",
        fontsize=15,
        fontweight="bold",
        y=0.98
    )

    mapped_clients = sum(
        count_lookup.values()
    )

    active_areas = len(
        [
            value
            for value in count_lookup.values()
            if value > 0
        ]
    )

    # Legend on main map.
    legend_labels = [
        ("50+", colours[5]),
        ("20-49", colours[4]),
        ("10-19", colours[3]),
        ("5-9", colours[2]),
        ("1-4", colours[1]),
        ("0", colours[0])
    ]

    legend_handles = [
        Rectangle(
            (0, 0),
            1,
            1,
            facecolor=colour,
            edgecolor="#c6c6c8"
        )
        for _, colour in legend_labels
    ]

    legend = ax.legend(
        legend_handles,
        [
            label
            for label, _
            in legend_labels
        ],
        title="CLIENTS",
        loc="upper left",
        bbox_to_anchor=(
            0.01,
            0.93
        ),
        frameon=True,
        facecolor="#2f2f31",
        edgecolor="#5f5f61",
        labelcolor="white",
        fontsize=9,
        title_fontsize=9
    )

    legend.get_title().set_color(
        "white"
    )

    # Summary on main map.
    ax.text(
        0.02,
        0.055,
        f"{mapped_clients:,}",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        color=REBEL_GREEN,
        fontsize=28,
        fontweight="bold"
    )

    ax.text(
        0.02,
        0.018,
        (
            f"clients across\n"
            f"{active_areas:,} postcode areas"
        ),
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        color="white",
        fontsize=11,
        linespacing=1.35
    )

    # London panel footer showing its total client count.
    london_areas = {
        "E", "EC", "N", "NW", "SE", "SW",
        "W", "WC", "BR", "CR", "DA", "EN",
        "HA", "IG", "KT", "RM", "SM", "TW",
        "UB", "WD"
    }

    london_clients = sum(
        count_lookup.get(
            area,
            0
        )
        for area in london_areas
    )

    london_ax.text(
        0.5,
        0.03,
        f"{london_clients:,} clients in London-area postcodes",
        transform=london_ax.transAxes,
        ha="center",
        va="bottom",
        color="white",
        fontsize=9
    )

    fig.subplots_adjust(
        top=0.89,
        left=0.03,
        right=0.98,
        bottom=0.04
    )

    return fig


def figure_to_png_bytes(
    fig
):

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    buffer.seek(0)

    return buffer.getvalue()


def format_pdf_money(
    value
):

    number = to_number(value)

    if number is None:
        return "Not available"

    return f"£{number:,.0f}"


def create_accountant_report_pdf(
    accountant_name,
    detail,
    top_clients,
    all_clients,
    map_png_bytes,
    area_counts
):

    """
    Generate a branded Rebel Data accountant intelligence report
    entirely in memory and return the PDF bytes.
    """

    output = io.BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=17 * mm,
        bottomMargin=16 * mm,
        title=f"Rebel Data - {accountant_name}",
        author="Rebel Data"
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RebelTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=27,
        textColor=colors.HexColor(
            REBEL_GREEN
        ),
        alignment=TA_LEFT,
        spaceAfter=4 * mm
    )

    subtitle_style = ParagraphStyle(
        "RebelSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor(
            "#666666"
        ),
        spaceAfter=6 * mm
    )

    h2_style = ParagraphStyle(
        "RebelH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor(
            REBEL_DARK
        ),
        spaceBefore=4 * mm,
        spaceAfter=3 * mm
    )

    body_style = ParagraphStyle(
        "RebelBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor(
            "#333333"
        )
    )

    story = []

    story.append(
        Paragraph(
            "Rebel Data",
            title_style
        )
    )

    story.append(
        Paragraph(
            "UK Business Intelligence - Accountant Intelligence Report",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            accountant_name,
            ParagraphStyle(
                "AccountantName",
                parent=h2_style,
                fontSize=19,
                leading=22,
                textColor=colors.HexColor(
                    REBEL_DARK
                ),
                spaceAfter=5 * mm
            )
        )
    )

    metric_data = [
        [
            "Clients",
            "Very High",
            "High",
            "Contact Now",
            "Referral Score"
        ],
        [
            f"{int(detail.get('RDRelevantClients') or 0):,}",
            f"{int(detail.get('VeryHighRDClients') or 0):,}",
            f"{int(detail.get('HighRDClients') or 0):,}",
            f"{int(detail.get('ContactNowClients') or 0):,}",
            f"{int(detail.get('ReferralOpportunityScore') or 0)}/100"
        ]
    ]

    metric_table = Table(
        metric_data,
        colWidths=[
            34 * mm,
            34 * mm,
            34 * mm,
            34 * mm,
            34 * mm
        ]
    )

    metric_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        REBEL_DARK
                    )
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor(
                        "#f4f4f4"
                    )
                ),
                (
                    "TEXTCOLOR",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor(
                        REBEL_GREEN
                    )
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica-Bold"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    8
                ),
                (
                    "FONTSIZE",
                    (0, 1),
                    (-1, 1),
                    13
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor(
                        "#d0d0d0"
                    )
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor(
                        "#dedede"
                    )
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ]
        )
    )

    story.append(
        metric_table
    )

    story.append(
        Spacer(
            1,
            6 * mm
        )
    )

    rd_clients = int(
        detail.get(
            "RDRelevantClients"
        )
        or 0
    )

    very_high = int(
        detail.get(
            "VeryHighRDClients"
        )
        or 0
    )

    high = int(
        detail.get(
            "HighRDClients"
        )
        or 0
    )

    contact_now = int(
        detail.get(
            "ContactNowClients"
        )
        or 0
    )

    story.append(
        Paragraph(
            "Accountant snapshot",
            h2_style
        )
    )

    story.append(
        Paragraph(
            (
                f"{accountant_name} has {rd_clients:,} clients identified "
                f"in Rebel Data, including {very_high:,} Very High and "
                f"{high:,} High opportunities. {contact_now:,} are currently "
                f"classified as Contact Now. The overall referral opportunity "
                f"score is {int(detail.get('ReferralOpportunityScore') or 0)}/100 "
                f"and the practice is classified as "
                f"{detail.get('ReferralOpportunityBand') or 'Not available'}."
            ),
            body_style
        )
    )

    story.append(
        Paragraph(
            "Top 3 clients",
            h2_style
        )
    )

    if (
        top_clients is not None
        and len(top_clients) > 0
    ):

        top_table_data = [
            [
                "Company",
                "Location",
                "R&D Score",
                "Opportunity",
                "Timing"
            ]
        ]

        for _, row in top_clients.iterrows():

            location_parts = [
                row.get("Town"),
                row.get("County"),
                row.get("Postcode")
            ]

            location = ", ".join(
                [
                    str(value)
                    for value in location_parts
                    if value is not None
                    and str(value).strip() != ""
                ]
            )

            top_table_data.append(
                [
                    Paragraph(
                        str(
                            row.get(
                                "Company Name",
                                ""
                            )
                        ),
                        body_style
                    ),
                    Paragraph(
                        location
                        or "Not available",
                        body_style
                    ),
                    str(
                        row.get(
                            "R&D Score",
                            ""
                        )
                    ),
                    str(
                        row.get(
                            "Opportunity",
                            ""
                        )
                    ),
                    str(
                        row.get(
                            "Timing",
                            ""
                        )
                    )
                ]
            )

        top_table = Table(
            top_table_data,
            colWidths=[
                56 * mm,
                48 * mm,
                22 * mm,
                27 * mm,
                27 * mm
            ],
            repeatRows=1
        )

        top_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            REBEL_DARK
                        )
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP"
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor(
                            "#d7d7d7"
                        )
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor(
                                "#f4f4f4"
                            )
                        ]
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    )
                ]
            )
        )

        story.append(
            top_table
        )

    else:

        story.append(
            Paragraph(
                "No top client opportunities are currently available.",
                body_style
            )
        )

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Client locations",
            h2_style
        )
    )

    mapped_clients = 0
    mapped_areas = 0

    if (
        area_counts is not None
        and len(area_counts) > 0
    ):

        mapped_clients = int(
            area_counts["Clients"].sum()
        )

        mapped_areas = len(
            area_counts
        )

    story.append(
        Paragraph(
            (
                f"{mapped_clients:,} clients are represented across "
                f"{mapped_areas:,} UK postcode areas. Darker Rebel green "
                f"indicates a greater concentration of clients."
            ),
            body_style
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    if map_png_bytes:

        map_buffer = io.BytesIO(
            map_png_bytes
        )

        story.append(
            RLImage(
                map_buffer,
                width=145 * mm,
                height=165 * mm
            )
        )

    if (
        area_counts is not None
        and len(area_counts) > 0
    ):

        story.append(
            Spacer(
                1,
                3 * mm
            )
        )

        story.append(
            Paragraph(
                "Top postcode areas",
                h2_style
            )
        )

        top_areas = (
            area_counts
            .sort_values(
                "Clients",
                ascending=False
            )
            .head(10)
        )

        area_table_data = [
            [
                "Postcode Area",
                "Clients",
                "% of mapped clients"
            ]
        ]

        denominator = max(
            mapped_clients,
            1
        )

        for _, row in top_areas.iterrows():

            clients_in_area = int(
                row["Clients"]
            )

            area_table_data.append(
                [
                    str(
                        row["Postcode Area"]
                    ),
                    f"{clients_in_area:,}",
                    f"{(clients_in_area / denominator) * 100:.1f}%"
                ]
            )

        area_table = Table(
            area_table_data,
            colWidths=[
                55 * mm,
                45 * mm,
                55 * mm
            ],
            repeatRows=1
        )

        area_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            REBEL_DARK
                        )
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (-1, -1),
                        "RIGHT"
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor(
                            "#d7d7d7"
                        )
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor(
                                "#f4f4f4"
                            )
                        ]
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5
                    )
                ]
            )
        )

        story.append(
            area_table
        )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        Paragraph(
            "Rebel Data | UK Business Intelligence",
            ParagraphStyle(
                "Footer",
                parent=body_style,
                fontName="Helvetica-Bold",
                textColor=colors.HexColor(
                    REBEL_GREEN
                )
            )
        )
    )

    doc.build(
        story
    )

    output.seek(0)

    return output.getvalue()


# ==================================================
# MAIN APP
# ==================================================


# ==================================================
# ACCOUNTANCY INTELLIGENCE PROFILE
# ==================================================

def get_accountancy_profile(accountant_name):
    """
    Build a deterministic profile of an accountancy firm's identified
    client portfolio using Rebel Data.

    This intentionally uses SQL/Python rules rather than the LLM so that
    the same accountant always produces the same profile.
    """

    accountant_name = str(accountant_name or "").strip()

    if not accountant_name:
        return None

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # --------------------------------------------------
        # Portfolio summary
        # --------------------------------------------------
        cursor.execute(
            """
            SELECT
                COUNT_BIG(*) AS IdentifiedClients,
                SUM(
                    CASE
                        WHEN CompanyStatus = 'Active' THEN 1
                        ELSE 0
                    END
                ) AS ActiveClients,
                AVG(
                    TRY_CONVERT(
                        DECIMAL(18,2),
                        NULLIF(Employees, '')
                    )
                ) AS AvgEmployees,
                SUM(
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 1 AND 5
                            THEN 1 ELSE 0
                    END
                ) AS Employees_1_5,
                SUM(
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 6 AND 10
                            THEN 1 ELSE 0
                    END
                ) AS Employees_6_10,
                SUM(
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 11 AND 19
                            THEN 1 ELSE 0
                    END
                ) AS Employees_11_19,
                SUM(
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 20 AND 49
                            THEN 1 ELSE 0
                    END
                ) AS Employees_20_49,
                SUM(
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 50 AND 99
                            THEN 1 ELSE 0
                    END
                ) AS Employees_50_99,
                SUM(
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 100 AND 249
                            THEN 1 ELSE 0
                    END
                ) AS Employees_100_249,
                SUM(
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) >= 250
                            THEN 1 ELSE 0
                    END
                ) AS Employees_250_Plus
            FROM dbo.vw_RebelCompanies
            WHERE
                LTRIM(RTRIM(AccountantName)) = %s
            """,
            (accountant_name,)
        )

        summary_row = cursor.fetchone()
        summary_columns = [
            column[0]
            for column in cursor.description
        ]

        summary = dict(
            zip(
                summary_columns,
                summary_row
            )
        )

        # --------------------------------------------------
        # R&D / referral summary
        # --------------------------------------------------
        cursor.execute(
            """
            SELECT TOP 1
                TotalClients,
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

        rd_row = cursor.fetchone()

        if rd_row is not None:
            rd_columns = [
                column[0]
                for column in cursor.description
            ]
            rd_summary = dict(
                zip(
                    rd_columns,
                    rd_row
                )
            )
        else:
            rd_summary = {}

        # --------------------------------------------------
        # Top industries + Rebel universe penetration
        # --------------------------------------------------
        cursor.execute(
            """
            ;WITH ClientIndustry AS
            (
                SELECT
                    SIC1,
                    COUNT_BIG(*) AS ClientCount
                FROM dbo.vw_RebelCompanies
                WHERE
                    LTRIM(RTRIM(AccountantName)) = %s
                    AND CompanyStatus = 'Active'
                    AND SIC1 IS NOT NULL
                    AND LTRIM(RTRIM(SIC1)) <> ''
                GROUP BY SIC1
            ),
            UniverseIndustry AS
            (
                SELECT
                    SIC1,
                    COUNT_BIG(*) AS UniverseCount
                FROM dbo.vw_RebelCompanies
                WHERE
                    CompanyStatus = 'Active'
                    AND SIC1 IS NOT NULL
                    AND LTRIM(RTRIM(SIC1)) <> ''
                GROUP BY SIC1
            )
            SELECT TOP 15
                c.SIC1 AS [Industry],
                c.ClientCount AS [Clients],
                u.UniverseCount AS [Universe],
                CAST(
                    100.0 * c.ClientCount
                    / NULLIF(u.UniverseCount, 0)
                    AS DECIMAL(10,2)
                ) AS [PenetrationPct]
            FROM ClientIndustry c
            JOIN UniverseIndustry u
                ON u.SIC1 = c.SIC1
            ORDER BY
                c.ClientCount DESC,
                c.SIC1
            """,
            (accountant_name,)
        )

        industry_rows = cursor.fetchall()
        industry_columns = [
            column[0]
            for column in cursor.description
        ]

        industries = pd.DataFrame(
            industry_rows,
            columns=industry_columns
        )

        # --------------------------------------------------
        # Employee band portfolio + penetration
        # --------------------------------------------------
        cursor.execute(
            """
            ;WITH UniverseBase AS
            (
                SELECT
                    CASE
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 1 AND 5 THEN '1-5'
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 6 AND 10 THEN '6-10'
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 11 AND 19 THEN '11-19'
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 20 AND 49 THEN '20-49'
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 50 AND 99 THEN '50-99'
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) BETWEEN 100 AND 249 THEN '100-249'
                        WHEN TRY_CONVERT(INT, NULLIF(Employees, '')) >= 250 THEN '250+'
                        ELSE 'Unknown'
                    END AS EmployeeBand,
                    AccountantName
                FROM dbo.vw_RebelCompanies
                WHERE CompanyStatus = 'Active'
            ),
            UniverseBands AS
            (
                SELECT
                    EmployeeBand,
                    COUNT_BIG(*) AS UniverseCount
                FROM UniverseBase
                GROUP BY EmployeeBand
            ),
            ClientBands AS
            (
                SELECT
                    EmployeeBand,
                    COUNT_BIG(*) AS ClientCount
                FROM UniverseBase
                WHERE LTRIM(RTRIM(AccountantName)) = %s
                GROUP BY EmployeeBand
            )
            SELECT
                u.EmployeeBand AS [Employee Band],
                ISNULL(c.ClientCount, 0) AS [Clients],
                u.UniverseCount AS [Universe],
                CAST(
                    100.0 * ISNULL(c.ClientCount, 0)
                    / NULLIF(u.UniverseCount, 0)
                    AS DECIMAL(10,3)
                ) AS [PenetrationPct]
            FROM UniverseBands u
            LEFT JOIN ClientBands c
                ON c.EmployeeBand = u.EmployeeBand
            ORDER BY
                CASE u.EmployeeBand
                    WHEN '1-5' THEN 1
                    WHEN '6-10' THEN 2
                    WHEN '11-19' THEN 3
                    WHEN '20-49' THEN 4
                    WHEN '50-99' THEN 5
                    WHEN '100-249' THEN 6
                    WHEN '250+' THEN 7
                    ELSE 8
                END
            """,
            (accountant_name,)
        )

        band_rows = cursor.fetchall()
        band_columns = [
            column[0]
            for column in cursor.description
        ]

        employee_bands = pd.DataFrame(
            band_rows,
            columns=band_columns
        )

        # --------------------------------------------------
        # Geography profile
        # --------------------------------------------------
        cursor.execute(
            """
            SELECT TOP 15
                CASE
                    WHEN NULLIF(LTRIM(RTRIM(County)), '') IS NOT NULL
                        THEN LTRIM(RTRIM(County))
                    WHEN NULLIF(LTRIM(RTRIM(PostTown)), '') IS NOT NULL
                        THEN LTRIM(RTRIM(PostTown))
                    ELSE 'Unknown'
                END AS [Area],
                COUNT_BIG(*) AS [Clients]
            FROM dbo.vw_RebelCompanies
            WHERE
                LTRIM(RTRIM(AccountantName)) = %s
                AND CompanyStatus = 'Active'
            GROUP BY
                CASE
                    WHEN NULLIF(LTRIM(RTRIM(County)), '') IS NOT NULL
                        THEN LTRIM(RTRIM(County))
                    WHEN NULLIF(LTRIM(RTRIM(PostTown)), '') IS NOT NULL
                        THEN LTRIM(RTRIM(PostTown))
                    ELSE 'Unknown'
                END
            ORDER BY
                COUNT_BIG(*) DESC,
                [Area]
            """,
            (accountant_name,)
        )

        geography_rows = cursor.fetchall()
        geography_columns = [
            column[0]
            for column in cursor.description
        ]

        geography = pd.DataFrame(
            geography_rows,
            columns=geography_columns
        )

        # --------------------------------------------------
        # Similar accountancy firms
        # --------------------------------------------------
        cursor.execute(
            """
            DECLARE
                @TotalClients FLOAT,
                @RDRelevant FLOAT,
                @ReferralScore FLOAT,
                @ContactNow FLOAT;

            SELECT TOP 1
                @TotalClients = ISNULL(TotalClients, 0),
                @RDRelevant = ISNULL(RDRelevantClients, 0),
                @ReferralScore = ISNULL(ReferralOpportunityScore, 0),
                @ContactNow = ISNULL(ContactNowClients, 0)
            FROM dbo.RD_AccountantOpportunities
            WHERE AccountantName = %s;

            SELECT TOP 10
                AccountantName AS [Accountant],
                TotalClients AS [Total Clients],
                RDRelevantClients AS [R&D Relevant],
                ContactNowClients AS [Contact Now],
                ReferralOpportunityScore AS [Referral Score],
                ReferralOpportunityBand AS [Opportunity],
                CAST(
                    ABS(ISNULL(TotalClients, 0) - @TotalClients)
                    + ABS(ISNULL(RDRelevantClients, 0) - @RDRelevant) * 2
                    + ABS(ISNULL(ContactNowClients, 0) - @ContactNow) * 2
                    + ABS(ISNULL(ReferralOpportunityScore, 0) - @ReferralScore) * 3
                    AS DECIMAL(18,2)
                ) AS [Distance]
            FROM dbo.RD_AccountantOpportunities
            WHERE AccountantName <> %s
            ORDER BY
                [Distance],
                ReferralOpportunityScore DESC,
                AccountantName
            """,
            (
                accountant_name,
                accountant_name
            )
        )

        similar_rows = cursor.fetchall()
        similar_columns = [
            column[0]
            for column in cursor.description
        ]

        similar_accountants = pd.DataFrame(
            similar_rows,
            columns=similar_columns
        )

        # --------------------------------------------------
        # White-space prospects:
        # active businesses in the firm's strongest industries
        # where this firm is not the identified accountant.
        # --------------------------------------------------
        cursor.execute(
            """
            ;WITH TopIndustries AS
            (
                SELECT TOP 5
                    SIC1,
                    COUNT_BIG(*) AS ClientCount
                FROM dbo.vw_RebelCompanies
                WHERE
                    LTRIM(RTRIM(AccountantName)) = %s
                    AND CompanyStatus = 'Active'
                    AND SIC1 IS NOT NULL
                    AND LTRIM(RTRIM(SIC1)) <> ''
                GROUP BY SIC1
                ORDER BY COUNT_BIG(*) DESC
            )
            SELECT TOP 100
                c.CompanyNumber AS [Company Number],
                c.CompanyName AS [Company Name],
                c.PostTown AS [Town],
                c.County AS [County],
                TRY_CONVERT(INT, NULLIF(c.Employees, '')) AS [Employees],
                c.SIC1 AS [Industry],
                c.AccountantName AS [Current Accountant]
            FROM dbo.vw_RebelCompanies c
            JOIN TopIndustries t
                ON t.SIC1 = c.SIC1
            WHERE
                c.CompanyStatus = 'Active'
                AND (
                    c.AccountantName IS NULL
                    OR LTRIM(RTRIM(c.AccountantName)) = ''
                    OR LTRIM(RTRIM(c.AccountantName)) <> %s
                )
            ORDER BY
                TRY_CONVERT(INT, NULLIF(c.Employees, '')) DESC,
                c.CompanyName
            """,
            (
                accountant_name,
                accountant_name
            )
        )

        white_space_rows = cursor.fetchall()
        white_space_columns = [
            column[0]
            for column in cursor.description
        ]

        white_space = pd.DataFrame(
            white_space_rows,
            columns=white_space_columns
        )

        cursor.close()

    finally:
        conn.close()

    return {
        "summary": summary,
        "rd_summary": rd_summary,
        "industries": industries,
        "employee_bands": employee_bands,
        "geography": geography,
        "similar_accountants": similar_accountants,
        "white_space": white_space
    }


def create_accountancy_profile_pdf(
    accountant_name,
    profile
):
    """
    Create a Rebel-branded Accountancy Intelligence Profile PDF.
    """

    summary = profile.get("summary", {})
    rd_summary = profile.get("rd_summary", {})
    industries = profile.get(
        "industries",
        pd.DataFrame()
    )
    employee_bands = profile.get(
        "employee_bands",
        pd.DataFrame()
    )
    geography = profile.get(
        "geography",
        pd.DataFrame()
    )
    similar_accountants = profile.get(
        "similar_accountants",
        pd.DataFrame()
    )

    output = io.BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=13 * mm,
        leftMargin=13 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AccountancyProfileTitle",
        parent=styles["Title"],
        fontSize=19,
        leading=23,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "AccountancyProfileSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#65a816"),
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        "AccountancyProfileHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#222222"),
        spaceBefore=8,
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        "AccountancyProfileBody",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#333333")
    )

    story = [
        Paragraph(
            "Rebel Data - Accountancy Intelligence Profile",
            title_style
        ),
        Paragraph(
            str(accountant_name),
            subtitle_style
        )
    ]

    summary_rows = [
        ["Measure", "Value"],
        [
            "Identified clients",
            f"{int(summary.get('IdentifiedClients') or 0):,}"
        ],
        [
            "Active identified clients",
            f"{int(summary.get('ActiveClients') or 0):,}"
        ],
        [
            "Average employees",
            (
                f"{float(summary.get('AvgEmployees')):,.1f}"
                if summary.get("AvgEmployees") is not None
                else "N/A"
            )
        ],
        [
            "R&D relevant clients",
            f"{int(rd_summary.get('RDRelevantClients') or 0):,}"
        ],
        [
            "Very High R&D clients",
            f"{int(rd_summary.get('VeryHighRDClients') or 0):,}"
        ],
        [
            "High R&D clients",
            f"{int(rd_summary.get('HighRDClients') or 0):,}"
        ],
        [
            "Contact Now clients",
            f"{int(rd_summary.get('ContactNowClients') or 0):,}"
        ],
        [
            "Referral opportunity score",
            f"{int(rd_summary.get('ReferralOpportunityScore') or 0):,}/100"
        ],
        [
            "Referral opportunity",
            display_value(
                rd_summary.get("ReferralOpportunityBand")
            )
        ]
    ]

    summary_table = Table(
        summary_rows,
        colWidths=[95 * mm, 80 * mm],
        repeatRows=1
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cccccc")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(
        Paragraph(
            "Portfolio Overview",
            heading_style
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 4 * mm))

    if industries is not None and not industries.empty:
        story.append(
            Paragraph(
                "Top Industries & Penetration",
                heading_style
            )
        )

        industry_rows = [
            [
                "Industry",
                "Clients",
                "Universe",
                "Penetration"
            ]
        ]

        for _, row in industries.head(10).iterrows():
            industry_rows.append(
                [
                    Paragraph(
                        str(row.get("Industry") or ""),
                        normal_style
                    ),
                    f"{int(row.get('Clients') or 0):,}",
                    f"{int(row.get('Universe') or 0):,}",
                    (
                        f"{float(row.get('PenetrationPct') or 0):.2f}%"
                    )
                ]
            )

        industry_table = Table(
            industry_rows,
            colWidths=[
                100 * mm,
                22 * mm,
                28 * mm,
                26 * mm
            ],
            repeatRows=1
        )

        industry_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        story.append(industry_table)
        story.append(Spacer(1, 4 * mm))

    if employee_bands is not None and not employee_bands.empty:
        story.append(
            Paragraph(
                "Employee Size Profile",
                heading_style
            )
        )

        band_rows = [
            [
                "Employee Band",
                "Clients",
                "Universe",
                "Penetration"
            ]
        ]

        for _, row in employee_bands.iterrows():
            band_rows.append(
                [
                    str(row.get("Employee Band") or ""),
                    f"{int(row.get('Clients') or 0):,}",
                    f"{int(row.get('Universe') or 0):,}",
                    f"{float(row.get('PenetrationPct') or 0):.3f}%"
                ]
            )

        band_table = Table(
            band_rows,
            colWidths=[
                55 * mm,
                38 * mm,
                42 * mm,
                40 * mm
            ],
            repeatRows=1
        )

        band_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(band_table)
        story.append(Spacer(1, 4 * mm))

    if geography is not None and not geography.empty:
        story.append(
            Paragraph(
                "Geographic Concentration",
                heading_style
            )
        )

        geo_rows = [["Area", "Clients"]]

        for _, row in geography.head(10).iterrows():
            geo_rows.append(
                [
                    str(row.get("Area") or ""),
                    f"{int(row.get('Clients') or 0):,}"
                ]
            )

        geo_table = Table(
            geo_rows,
            colWidths=[
                125 * mm,
                50 * mm
            ],
            repeatRows=1
        )

        geo_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )

        story.append(geo_table)
        story.append(Spacer(1, 4 * mm))

    if similar_accountants is not None and not similar_accountants.empty:
        story.append(
            Paragraph(
                "Comparable Accountancy Firms",
                heading_style
            )
        )

        similar_rows = [
            [
                "Accountant",
                "Clients",
                "R&D Relevant",
                "Referral Score"
            ]
        ]

        for _, row in similar_accountants.head(8).iterrows():
            similar_rows.append(
                [
                    Paragraph(
                        str(row.get("Accountant") or ""),
                        normal_style
                    ),
                    f"{int(row.get('Total Clients') or 0):,}",
                    f"{int(row.get('R&D Relevant') or 0):,}",
                    f"{int(row.get('Referral Score') or 0):,}"
                ]
            )

        similar_table = Table(
            similar_rows,
            colWidths=[
                95 * mm,
                28 * mm,
                30 * mm,
                25 * mm
            ],
            repeatRows=1
        )

        similar_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8bd02f")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(similar_table)

    story.append(Spacer(1, 5 * mm))

    story.append(
        Paragraph(
            "Portfolio and penetration figures are based on accountancy "
            "relationships identified in Rebel Data. They should be treated "
            "as indicative market intelligence rather than a complete statement "
            "of an accountancy firm's client base or market share.",
            normal_style
        )
    )

    doc.build(story)

    output.seek(0)

    return output.getvalue()


def show_accountancy_profile(
    accountant_name,
    compact=False,
    key_prefix="accountancy_profile"
):
    """
    Render accountancy portfolio profiling, market penetration,
    comparable firms and white-space prospects.
    """

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Accountancy Intelligence Profile</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Portfolio profiling is calculated from accountancy relationships "
        "identified in Rebel Data."
    )

    with st.spinner(
        "Profiling accountancy portfolio..."
    ):
        profile = get_accountancy_profile(
            accountant_name
        )

    if not profile:
        st.info(
            "No profile could be created for this accountant."
        )
        return

    summary = profile["summary"]
    rd_summary = profile["rd_summary"]
    industries = profile["industries"]
    employee_bands = profile["employee_bands"]
    geography = profile["geography"]
    similar_accountants = profile[
        "similar_accountants"
    ]
    white_space = profile["white_space"]

    identified_clients = int(
        summary.get("IdentifiedClients") or 0
    )
    active_clients = int(
        summary.get("ActiveClients") or 0
    )
    avg_employees = summary.get(
        "AvgEmployees"
    )
    rd_relevant = int(
        rd_summary.get("RDRelevantClients") or 0
    )
    contact_now = int(
        rd_summary.get("ContactNowClients") or 0
    )
    referral_score = int(
        rd_summary.get("ReferralOpportunityScore") or 0
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric(
        "IDENTIFIED CLIENTS",
        f"{identified_clients:,}"
    )

    c2.metric(
        "ACTIVE CLIENTS",
        f"{active_clients:,}"
    )

    c3.metric(
        "AVG EMPLOYEES",
        (
            f"{float(avg_employees):,.1f}"
            if avg_employees is not None
            else "N/A"
        )
    )

    c4.metric(
        "R&D RELEVANT",
        f"{rd_relevant:,}"
    )

    c5.metric(
        "CONTACT NOW",
        f"{contact_now:,}"
    )

    c6.metric(
        "REFERRAL SCORE",
        f"{referral_score:,}/100"
    )

    # --------------------------------------------------
    # Industry profile
    # --------------------------------------------------
    st.markdown("### Industry Profile & Market Penetration")

    if industries.empty:
        st.info(
            "No industry profile is currently available."
        )
    else:
        industry_display = industries.copy()

        industry_display["Penetration"] = industry_display[
            "PenetrationPct"
        ].apply(
            lambda x: (
                f"{float(x):.2f}%"
                if pd.notna(x)
                else ""
            )
        )

        industry_display = industry_display[
            [
                "Industry",
                "Clients",
                "Universe",
                "Penetration"
            ]
        ]

        st.dataframe(
            industry_display,
            use_container_width=True,
            hide_index=True,
            height=390
        )

        strongest = industries.sort_values(
            ["PenetrationPct", "Clients"],
            ascending=[False, False]
        ).iloc[0]

        largest = industries.sort_values(
            ["Clients", "PenetrationPct"],
            ascending=[False, False]
        ).iloc[0]

        i1, i2 = st.columns(2)

        i1.metric(
            "LARGEST CLIENT SECTOR",
            f"{int(largest['Clients']):,} clients"
        )

        i1.caption(
            str(largest["Industry"])
        )

        i2.metric(
            "STRONGEST PENETRATION",
            f"{float(strongest['PenetrationPct']):.2f}%"
        )

        i2.caption(
            str(strongest["Industry"])
        )

    # --------------------------------------------------
    # Employee profile
    # --------------------------------------------------
    st.markdown("### Client Size Profile")

    if not employee_bands.empty:
        band_display = employee_bands.copy()

        band_display["Penetration"] = band_display[
            "PenetrationPct"
        ].apply(
            lambda x: (
                f"{float(x):.3f}%"
                if pd.notna(x)
                else ""
            )
        )

        st.dataframe(
            band_display[
                [
                    "Employee Band",
                    "Clients",
                    "Universe",
                    "Penetration"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------
    # Geography
    # --------------------------------------------------
    st.markdown("### Geographic Profile")

    if geography.empty:
        st.info(
            "No geographic profile is currently available."
        )
    else:
        total_geo = max(
            int(geography["Clients"].sum()),
            1
        )

        geo_display = geography.copy()

        geo_display["% of Portfolio"] = (
            geo_display["Clients"]
            / total_geo
            * 100
        ).apply(
            lambda x: f"{x:.1f}%"
        )

        st.dataframe(
            geo_display[
                [
                    "Area",
                    "Clients",
                    "% of Portfolio"
                ]
            ],
            use_container_width=True,
            hide_index=True,
            height=360
        )

    # --------------------------------------------------
    # R&D opportunity profile
    # --------------------------------------------------
    st.markdown("### R&D Opportunity Profile")

    r1, r2, r3, r4 = st.columns(4)

    r1.metric(
        "VERY HIGH",
        f"{int(rd_summary.get('VeryHighRDClients') or 0):,}"
    )

    r2.metric(
        "HIGH",
        f"{int(rd_summary.get('HighRDClients') or 0):,}"
    )

    r3.metric(
        "CONTACT SOON",
        f"{int(rd_summary.get('ContactSoonClients') or 0):,}"
    )

    r4.metric(
        "AVG R&D SCORE",
        (
            f"{float(rd_summary.get('AvgRDOpportunityScore')):.1f}"
            if rd_summary.get("AvgRDOpportunityScore") is not None
            else "N/A"
        )
    )

    # --------------------------------------------------
    # Similar practices
    # --------------------------------------------------
    st.markdown("### Similar Accountancy Firms")

    if similar_accountants.empty:
        st.info(
            "No comparable accountancy firms are currently available."
        )
    else:
        st.dataframe(
            similar_accountants.drop(
                columns=["Distance"],
                errors="ignore"
            ),
            use_container_width=True,
            hide_index=True,
            height=360
        )

    # --------------------------------------------------
    # White space
    # --------------------------------------------------
    st.markdown("### Market White Space")

    st.write(
        "These are active businesses in the firm's strongest identified "
        "client sectors where this accountant is not currently recorded as "
        "the accountant in Rebel Data."
    )

    if white_space.empty:
        st.info(
            "No white-space businesses were found for the current profile."
        )
    else:
        st.write(
            f"Showing **{len(white_space):,}** potential white-space businesses."
        )

        st.dataframe(
            white_space,
            use_container_width=True,
            hide_index=True,
            height=450
        )

        white_space_csv = (
            white_space
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "DOWNLOAD WHITE SPACE CSV",
            data=white_space_csv,
            file_name=(
                "accountancy_white_space_"
                + re.sub(
                    r"[^A-Za-z0-9_-]+",
                    "_",
                    accountant_name
                ).strip("_")
                + ".csv"
            ),
            mime="text/csv",
            key=f"{key_prefix}_white_space_csv"
        )

    # --------------------------------------------------
    # Profile PDF
    # --------------------------------------------------
    try:
        profile_pdf = create_accountancy_profile_pdf(
            accountant_name,
            profile
        )

        safe_accountant_name = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            accountant_name
        ).strip("_")

        st.download_button(
            "DOWNLOAD ACCOUNTANCY PROFILE PDF",
            data=profile_pdf,
            file_name=(
                f"Rebel_Accountancy_Profile_"
                f"{safe_accountant_name}.pdf"
            ),
            mime="application/pdf",
            key=f"{key_prefix}_profile_pdf"
        )

    except Exception as pdf_error:
        st.warning(
            "The accountancy profile loaded, but the profile PDF "
            "could not be generated."
        )
        st.exception(pdf_error)


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
            RDRelevantClients AS [Clients],
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
            RDRelevantClients AS [Clients],
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



def get_rd_accountant_top_clients(accountant_name):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT TOP 3
                CompanyNumber AS [Company Number],
                CompanyName AS [Company Name],
                PostTown AS [Town],
                County AS [County],
                PostCode AS [Postcode],
                LatestEmployees AS [Employees],
                LatestTurnover AS [Turnover],
                RDOpportunityScore AS [R&D Score],
                RDOpportunityBand AS [Opportunity],
                SalesTimingBand AS [Timing]
            FROM dbo.RD_RDProspects
            WHERE LTRIM(RTRIM(LatestAccountantName)) = %s
            ORDER BY
                RDOpportunityScore DESC,
                SalesTimingScore DESC,
                CompanyName
            """,
            (accountant_name,)
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
                PostTown AS [Town],
                County AS [County],
                PostCode AS [Postcode],
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
                "Minimum Clients",
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
            "Clients",
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
            "#### Top 3 Clients"
        )

        try:

            top_clients = get_rd_accountant_top_clients(
                selected_accountant
            )

            if len(top_clients) > 0:

                st.dataframe(
                    top_clients,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No client opportunities are currently available."
                )

                top_clients = pd.DataFrame()

        except Exception:

            st.warning(
                "Unable to load the top client snapshot."
            )

            top_clients = pd.DataFrame()


        # --------------------------------------------------
        # ACCOUNTANCY INTELLIGENCE PROFILE
        # --------------------------------------------------

        try:
            show_accountancy_profile(
                selected_accountant,
                key_prefix="rd_accountancy_profile"
            )
        except Exception as profile_error:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(
                '<div class="section-title">Accountancy Intelligence Profile</div>',
                unsafe_allow_html=True
            )
            st.warning(
                "The accountant detail loaded, but the accountancy profile "
                "could not be generated."
            )
            st.exception(profile_error)


        # --------------------------------------------------
        # CLIENT DISTRIBUTION BY POSTCODE AREA
        # --------------------------------------------------

        st.markdown(
            "#### Client Distribution by Postcode Area"
        )

        try:

            with st.spinner(
                "Building postcode area map..."
            ):

                map_clients = get_rd_accountant_clients(
                    selected_accountant,
                    "All"
                )

                area_counts = build_postcode_area_counts(
                    map_clients
                )

                map_figure = create_postcode_area_map_figure(
                    area_counts,
                    selected_accountant
                )

                map_png = figure_to_png_bytes(
                    map_figure
                )

            mapped_clients = int(
                area_counts["Clients"].sum()
            ) if len(area_counts) > 0 else 0

            mapped_areas = len(
                area_counts
            )

            map_col, stats_col = st.columns(
                [2.2, 1]
            )

            with map_col:

                st.pyplot(
                    map_figure,
                    use_container_width=True
                )

            with stats_col:

                st.metric(
                    "CLIENTS",
                    f"{len(map_clients):,}"
                )

                st.metric(
                    "MAPPED CLIENTS",
                    f"{mapped_clients:,}"
                )

                st.metric(
                    "POSTCODE AREAS",
                    f"{mapped_areas:,}"
                )

                if len(map_clients) > 0:

                    coverage = (
                        mapped_clients
                        / len(map_clients)
                    ) * 100

                    st.metric(
                        "MAP COVERAGE",
                        f"{coverage:.1f}%"
                    )

            plt.close(
                map_figure
            )

            if len(area_counts) > 0:

                st.markdown(
                    "##### Top Postcode Areas"
                )

                top_areas = (
                    area_counts
                    .sort_values(
                        "Clients",
                        ascending=False
                    )
                    .head(10)
                    .copy()
                )

                top_areas[
                    "% of Clients"
                ] = (
                    top_areas["Clients"]
                    / max(
                        mapped_clients,
                        1
                    )
                    * 100
                ).round(1)

                top_areas[
                    "% of Clients"
                ] = top_areas[
                    "% of Clients"
                ].map(
                    lambda value:
                    f"{value:.1f}%"
                )

                st.dataframe(
                    top_areas,
                    use_container_width=True,
                    hide_index=True
                )

            # ----------------------------------------------
            # BRANDED PDF REPORT
            # ----------------------------------------------

            with st.spinner(
                "Building Rebel Data report..."
            ):

                report_pdf = create_accountant_report_pdf(
                    selected_accountant,
                    detail,
                    top_clients,
                    map_clients,
                    map_png,
                    area_counts
                )

            safe_accountant_name = re.sub(
                r"[^A-Za-z0-9_-]+",
                "_",
                selected_accountant
            ).strip("_")

            st.download_button(
                label="DOWNLOAD ACCOUNTANT REPORT PDF",
                data=report_pdf,
                file_name=(
                    f"Rebel_Data_{safe_accountant_name}_Report.pdf"
                ),
                mime="application/pdf",
                key="rd_accountant_pdf"
            )

        except Exception as map_error:

            st.warning(
                "The accountant snapshot loaded, but the postcode-area map "
                "or PDF report could not be generated."
            )

            st.exception(
                map_error
            )


        st.markdown(
            "#### Potential Clients"
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
    "last_viewed_rd_company": None,
    "ask_rebel_question": None,
    "ask_rebel_plan": None,
    "ask_rebel_results": None,
    "ask_rebel_generated_sql": None,
    "ask_rebel_selected_company": None,
    "ask_rebel_conversation": []
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
    div[data-testid="stHorizontalBlock"] > div:has(button[key="nav_rd_referrals"]),
    div[data-testid="stHorizontalBlock"] > div:has(button[key="nav_ask_rebel"]) {
        gap: 0.5rem;
    }

    button[kind="secondary"] {
        border-radius: 6px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

nav1, nav2, nav3, nav_spacer = st.columns([1.2, 1.5, 1.0, 4])

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

with nav3:
    ask_rebel_active = (
        st.session_state["active_page"] == "Ask Rebel"
    )

    if st.button(
        "ASK REBEL",
        key="nav_ask_rebel",
        use_container_width=True,
        type="primary" if ask_rebel_active else "secondary"
    ):
        st.session_state["active_page"] = "Ask Rebel"
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

if st.session_state["active_page"] == "Company Search":
    show_company_search_page()
elif st.session_state["active_page"] == "R&D Referral Partners":
    show_rd_referral_page()
else:
    show_ask_rebel_page()


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
