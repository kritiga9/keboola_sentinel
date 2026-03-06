import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import graphviz
import json
import re
from datetime import datetime, timedelta

{QUERY_DATA_FUNCTION}


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════

if "selected_org" not in st.session_state:
    st.session_state.selected_org = "All Organizations"

if "date_range_start" not in st.session_state:
    st.session_state.date_range_start = datetime.now() - timedelta(days=90)

if "date_range_end" not in st.session_state:
    st.session_state.date_range_end = datetime.now()

if "cost_per_ppu" not in st.session_state:
    st.session_state.cost_per_ppu = 0.50

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - LIGHT THEME
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Sentinel | Data Governance", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div { color: #1e293b !important; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 { color: #0f172a !important; }
    .stMarkdown, .stMarkdown p, .stMarkdown span { color: #334155 !important; }
    .stCaption, small, .stApp small { color: #64748b !important; }
    section[data-testid="stSidebar"] { background-color: #1e293b !important; }
    section[data-testid="stSidebar"] * { color: #f1f5f9 !important; }
    section[data-testid="stSidebar"] .stRadio label { color: #f1f5f9 !important; }
    .stTextInput input, .stSelectbox select, .stMultiSelect, .stNumberInput input {
        background-color: #ffffff !important; color: #1e293b !important; border-color: #cbd5e1 !important;
    }
    .stDataFrame, [data-testid="stDataFrame"] { background-color: #ffffff !important; }
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        padding: 1.25rem; border-radius: 12px; border: 1px solid #e2e8f0;
        text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-label { color: #64748b !important; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
    .kpi-value { font-size: 1.75rem; font-weight: 700; color: #1e293b !important; }
    .org-selection-box {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        padding: 0.75rem; border-radius: 8px; margin-top: 0.5rem; margin-bottom: 0.5rem;
    }
    .org-selection-label { color: #bfdbfe !important; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .org-selection-value { color: #ffffff !important; font-size: 0.9rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA SOURCES
# ══════════════════════════════════════════════════════════════════════════════

TABLES_FQN = '"KBC_USE4_37"."out.c-kbc_public_telemetry"."kbc_table"'
PROJECTS_FQN = '"KBC_USE4_37"."out.c-kbc_public_telemetry"."kbc_project"'
ORGANIZATIONS_FQN = '"KBC_USE4_37"."out.c-kbc_public_telemetry"."kbc_organization"'
CONFIGS_FQN = '"KBC_USE4_37"."out.c-kbc_billing"."kbc_component_configuration"'
JOBS_FQN = '"KBC_USE4_37"."out.c-kbc_billing"."kbc_job"'

SINGLE_TENANT_ORG_TABLES = [
    ('"KBC_USE4_33"."in.c-raw-data"."connection-bi-organizations"', 'Coates'),
    ('"KBC_USE4_34"."in.c-raw-data"."connection-bi-organizations"', 'Creditinfo'),
    ('"KBC_USE4_35"."in.c-raw-data"."connection-bi-organizations"', 'CSAS'),
    ('"KBC_USE4_20"."in.c-raw-data"."connection-bi-organizations"', 'Groupon'),
    ('"KBC_USE4_21"."in.c-raw-data"."connection-bi-organizations"', 'HCI'),
    ('"KBC_USE4_286"."in.c-raw-data"."connection-bi-organizations"', 'HCKZ'),
    ('"KBC_USE4_22"."in.c-raw-data"."connection-bi-organizations"', 'Innogy Hub'),
    ('"KBC_USE4_377"."in.c-raw-data"."connection-bi-organizations"', 'Pasha'),
    ('"KBC_USE4_69"."in.c-raw-data"."connection-bi-organizations"', 'RBI'),
    ('"KBC_USE4_23"."in.c-raw-data"."connection-bi-organizations"', 'SLSP'),
]

COMPONENT_FRIENDLY_NAMES = {
    # Extractors
    'ex-salesforce': 'Salesforce CRM',
    'ex-hubspot': 'HubSpot',
    'ex-google-analytics': 'Google Analytics',
    'ex-facebook': 'Facebook Ads',
    'ex-google-ads': 'Google Ads',
    'ex-db-mysql': 'MySQL database',
    'ex-db-postgres': 'PostgreSQL database',
    'ex-db-mssql': 'SQL Server',
    'ex-db-snowflake': 'Snowflake',
    'ex-db-bigquery': 'BigQuery',
    'ex-aws-s3': 'AWS S3',
    'ex-google-drive': 'Google Drive',
    'ex-dropbox': 'Dropbox',
    'ex-shopify': 'Shopify',
    'ex-stripe': 'Stripe payments',
    'ex-zendesk': 'Zendesk',
    'ex-jira': 'Jira',
    'ex-slack': 'Slack',
    'ex-linkedin': 'LinkedIn',
    'ex-twitter': 'Twitter/X',
    'ex-instagram': 'Instagram',
    'ex-mailchimp': 'Mailchimp',
    'ex-intercom': 'Intercom',
    'ex-pipedrive': 'Pipedrive',
    'ex-asana': 'Asana',
    'ex-airtable': 'Airtable',
    'ex-notion': 'Notion',
    'ex-quickbooks': 'QuickBooks',
    'ex-xero': 'Xero accounting',
    'ex-netsuite': 'NetSuite',
    'ex-sap': 'SAP',
    'ex-dynamics': 'Microsoft Dynamics',
    'ex-http': 'REST API',
    'ex-generic': 'external API',
    # Writers
    'wr-google-sheets': 'Google Sheets',
    'wr-google-drive': 'Google Drive',
    'wr-google-bigquery': 'BigQuery',
    'wr-snowflake': 'Snowflake',
    'wr-redshift': 'Redshift',
    'wr-db-mysql': 'MySQL',
    'wr-db-postgres': 'PostgreSQL',
    'wr-db-mssql': 'SQL Server',
    'wr-tableau': 'Tableau',
    'wr-looker': 'Looker',
    'wr-powerbi': 'Power BI',
    'wr-slack': 'Slack',
    'wr-email': 'email',
    'wr-aws-s3': 'AWS S3',
    'wr-dropbox': 'Dropbox',
    'wr-salesforce': 'Salesforce',
    'wr-hubspot': 'HubSpot',
    # Transformations
    'snowflake-transformation': 'data transformation',
    'python-transformation': 'Python processing',
    'r-transformation': 'R analysis',
    'dbt-transformation': 'dbt models',
    # Apps
    'app-': 'data application',
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def render_kpi(label, value, color="#3b82f6", tooltip=None):
    tooltip_html = f'title="{tooltip}"' if tooltip else ''
    st.markdown(f"""
        <div class="kpi-card" {tooltip_html}>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value" style="color: {color};">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def format_data_size(mb_value):
    if mb_value >= 1024 * 1024:
        return f"{mb_value / (1024 * 1024):,.2f} TB"
    elif mb_value >= 1024:
        return f"{mb_value / 1024:,.2f} GB"
    else:
        return f"{mb_value:,.0f} MB"

def safe_datetime_convert(series):
    try:
        result = pd.to_datetime(series, errors="coerce", utc=True)
        if hasattr(result.dt, 'tz_localize'):
            return result.dt.tz_localize(None)
        return result
    except Exception:
        return pd.Series([pd.NaT] * len(series))

def get_table_url(table_id, kbc_project_id):
    if not kbc_project_id or not table_id:
        return None
    parts = str(kbc_project_id).split("_")
    proj_num = parts[0] if parts else ""
    if len(parts) > 1:
        stack = "_".join(parts[1:])
        if "azure-north-europe" in stack:
            base_url = "https://connection.north-europe.azure.keboola.com"
        elif "eu-central-1" in stack:
            base_url = "https://connection.eu-central-1.keboola.com"
        elif "europe-west3" in stack or "gcp" in stack:
            base_url = "https://connection.europe-west3.gcp.keboola.com"
        else:
            base_url = "https://connection.keboola.com"
    else:
        base_url = "https://connection.keboola.com"
    table_parts = table_id.split(".")
    if len(table_parts) >= 3:
        bucket_id = f"{table_parts[0]}.{table_parts[1]}"
        table_name = table_parts[2]
        return f"{base_url}/admin/projects/{proj_num}/storage/{bucket_id}/table/{table_name}"
    return None

def escape_sql_string(value):
    if value is None:
        return value
    return str(value).replace("'", "''")

def get_friendly_component_name(component_id):
    if not component_id:
        return None
    component_id = component_id.lower()
    for key, friendly_name in COMPONENT_FRIENDLY_NAMES.items():
        if key in component_id:
            return friendly_name
    return None

def generate_use_case_summary(config_json_str):
    if not config_json_str:
        return "Data pipeline"
    try:
        config = json.loads(config_json_str)
        tasks = config.get("tasks", [])
        if not tasks:
            return "Data pipeline"
        extractors, transformations, writers, apps = [], [], [], []
        for task in tasks:
            task_info = task.get("task", {})
            component_id = task_info.get("componentId", "")
            friendly_name = get_friendly_component_name(component_id)
            if not friendly_name:
                continue
            if "ex-" in component_id or "extractor" in component_id:
                if friendly_name not in extractors:
                    extractors.append(friendly_name)
            elif "wr-" in component_id or "writer" in component_id:
                if friendly_name not in writers:
                    writers.append(friendly_name)
            elif "transformation" in component_id:
                if friendly_name not in transformations:
                    transformations.append(friendly_name)
            elif "app-" in component_id:
                if friendly_name not in apps:
                    apps.append(friendly_name)
        if extractors and writers:
            src = extractors[0] if len(extractors) == 1 else f"{len(extractors)} sources"
            dst = writers[0] if len(writers) == 1 else f"{len(writers)} destinations"
            return f"Sync {src} to {dst}" + (" with processing" if transformations else "")
        if extractors:
            if len(extractors) == 1:
                return f"Import data from {extractors[0]}"
            return f"Import from {', '.join(extractors[:2])}" + (f" +{len(extractors)-2} more" if len(extractors) > 2 else "")
        if writers:
            if len(writers) == 1:
                return f"Export data to {writers[0]}"
            return f"Export to {', '.join(writers[:2])}" + (f" +{len(writers)-2} more" if len(writers) > 2 else "")
        if transformations:
            return "Data transformation & processing"
        if apps:
            return "Run data applications"
        return f"Automated workflow ({len(tasks)} tasks)"
    except (json.JSONDecodeError, TypeError, KeyError):
        return "Data pipeline"

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADERS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_organizations():
    main_orgs_df = query_data(f"""
        SELECT "kbc_organization_id", "kbc_organization"
        FROM {ORGANIZATIONS_FQN}
        WHERE "kbc_organization_is_deleted" = 'false' OR "kbc_organization_is_deleted" IS NULL
        ORDER BY "kbc_organization"
    """)
    all_orgs = []
    if not main_orgs_df.empty:
        all_orgs.append(main_orgs_df)
    for fqn, stack_name in SINGLE_TENANT_ORG_TABLES:
        try:
            st_df = query_data(f"""
                SELECT "id" as "kbc_organization_id", "name" as "kbc_organization"
                FROM {fqn}
                WHERE "isDeleted" = 'false' OR "isDeleted" IS NULL OR "isDeleted" = '0'
                LIMIT 100
            """)
            if not st_df.empty:
                st_df["kbc_organization"] = st_df["kbc_organization"] + f" [{stack_name}]"
                all_orgs.append(st_df)
        except Exception:
            pass
    if all_orgs:
        combined_df = pd.concat(all_orgs, ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=["kbc_organization"])
        return combined_df
    return pd.DataFrame(columns=["kbc_organization_id", "kbc_organization"])

@st.cache_data(ttl=300)
def get_governance_data(org_filter=None):
    org_join = ""
    org_where = ""
    if org_filter and org_filter != "All Organizations":
        base_org = org_filter.split(" [")[0] if " [" in org_filter else org_filter
        escaped_org = escape_sql_string(base_org)
        org_join = f"""
            INNER JOIN {PROJECTS_FQN} p ON t."kbc_project_id" = p."kbc_project_id"
            INNER JOIN {ORGANIZATIONS_FQN} o ON p."kbc_organization_id" = o."kbc_organization_id"
        """
        org_where = f"""WHERE o."kbc_organization" = '{escaped_org}'"""
    df = query_data(f"""
        SELECT t."table_id" as "id", t."kbc_project_id" as "project_id", t."table_name",
               t."last_import" as "last_import_date", t."source_table_id" as "sharing",
               t."rows", t."bytes"
        FROM {TABLES_FQN} t {org_join} {org_where} LIMIT 5000
    """)
    if df.empty:
        return df
    df["last_import_date"] = safe_datetime_convert(df["last_import_date"])
    now = datetime.utcnow()
    df["hours_stale"] = df["last_import_date"].apply(lambda x: int((now - x).total_seconds() / 3600) if pd.notna(x) else 99999)
    df["health"] = df["hours_stale"].apply(lambda x: "🟢 Healthy" if x < 24 else "🟡 Warning" if x < 72 else "🔴 Stale")
    df["is_shared"] = df["sharing"].apply(lambda x: x is not None and str(x).strip() != "")
    df["rows"] = pd.to_numeric(df["rows"], errors="coerce").fillna(0).astype(int)
    df["bytes"] = pd.to_numeric(df["bytes"], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=300)
def get_project_id_mapping():
    df = query_data(f"""SELECT "kbc_project_id" FROM {PROJECTS_FQN}""")
    if df.empty:
        return {}
    mapping = {}
    for _, row in df.iterrows():
        full_id = row["kbc_project_id"]
        simple_id = str(full_id).split("_")[0]
        mapping[simple_id] = full_id
    return mapping

@st.cache_data(ttl=300)
def get_all_tables(org_filter=None):
    org_join = ""
    org_where = ""
    if org_filter and org_filter != "All Organizations":
        base_org = org_filter.split(" [")[0] if " [" in org_filter else org_filter
        escaped_org = escape_sql_string(base_org)
        org_join = f"""
            INNER JOIN {PROJECTS_FQN} p ON t."kbc_project_id" = p."kbc_project_id"
            INNER JOIN {ORGANIZATIONS_FQN} o ON p."kbc_organization_id" = o."kbc_organization_id"
        """
        org_where = f"""WHERE o."kbc_organization" = '{escaped_org}'"""
    df = query_data(f"""
        SELECT t."table_id" as "id", t."table_name" as "name", t."kbc_project_id" as "project_id"
        FROM {TABLES_FQN} t {org_join} {org_where} LIMIT 5000
    """)
    return df

@st.cache_data(ttl=300)
def get_configurations_with_mappings(org_filter=None):
    org_join = ""
    org_where = ""
    if org_filter and org_filter != "All Organizations":
        base_org = org_filter.split(" [")[0] if " [" in org_filter else org_filter
        escaped_org = escape_sql_string(base_org)
        org_join = f"""
            INNER JOIN {PROJECTS_FQN} p ON c."kbc_project_id" = p."kbc_project_id"
            INNER JOIN {ORGANIZATIONS_FQN} o ON p."kbc_organization_id" = o."kbc_organization_id"
        """
        org_where = f"""AND o."kbc_organization" = '{escaped_org}'"""
    df = query_data(f"""
        SELECT c."kbc_component_configuration_id", c."kbc_component_configuration" as "config_name",
               c."kbc_component_id", c."kbc_component" as "component_name", c."kbc_component_type",
               c."kbc_project_id", c."configuration_json"
        FROM {CONFIGS_FQN} c {org_join}
        WHERE c."configuration_json" IS NOT NULL AND c."configuration_json" != ''
          AND c."kbc_configuration_is_deleted" = 'false' {org_where}
        LIMIT 5000
    """)
    return df

@st.cache_data(ttl=300)
def get_project_names(org_filter=None):
    org_join = ""
    org_where = ""
    if org_filter and org_filter != "All Organizations":
        base_org = org_filter.split(" [")[0] if " [" in org_filter else org_filter
        escaped_org = escape_sql_string(base_org)
        org_join = f"""INNER JOIN {ORGANIZATIONS_FQN} o ON p."kbc_organization_id" = o."kbc_organization_id" """
        org_where = f"""WHERE o."kbc_organization" = '{escaped_org}'"""
    df = query_data(f"""SELECT p."kbc_project_id", p."kbc_project" as "project_name" FROM {PROJECTS_FQN} p {org_join} {org_where}""")
    if df.empty:
        return {}
    df["project_id"] = df["kbc_project_id"].apply(lambda x: str(x).split("_")[0] if pd.notna(x) else None)
    return dict(zip(df["project_id"], df["project_name"]))

@st.cache_data(ttl=300)
def get_cost_per_flow(start_date=None, end_date=None, org_filter=None):
    date_filter = ""
    if start_date and end_date:
        date_filter = f"""AND j."job_start_at" >= '{start_date}' AND j."job_start_at" <= '{end_date}'"""
    org_join = ""
    org_where = ""
    if org_filter and org_filter != "All Organizations":
        base_org = org_filter.split(" [")[0] if " [" in org_filter else org_filter
        escaped_org = escape_sql_string(base_org)
        org_join = f"""
            INNER JOIN {PROJECTS_FQN} proj ON fj."kbc_project_id" = proj."kbc_project_id"
            INNER JOIN {ORGANIZATIONS_FQN} org ON proj."kbc_organization_id" = org."kbc_organization_id"
        """
        org_where = f"""AND org."kbc_organization" = '{escaped_org}'"""
    df = query_data(f"""
        WITH flow_jobs AS (
            SELECT "kbc_job_id", "kbc_component_configuration_id", "kbc_project_id", "job_run_id", "job_start_at"
            FROM {JOBS_FQN}
            WHERE ("kbc_component_id" LIKE '%orchestrator%' OR "kbc_component_id" LIKE '%flow%')
        ),
        child_jobs AS (
            SELECT SPLIT_PART(j."job_run_id", '.', 1) as "parent_job_id",
                SUM(TRY_TO_DOUBLE(j."job_billed_credits_used")) as "credits",
                SUM(TRY_TO_DOUBLE(j."job_network_mb")) as "data_transferred_mb",
                COUNT(*) as "task_count",
                SUM(CASE WHEN j."job_status" = 'success' THEN 1 ELSE 0 END) as "success_count",
                SUM(CASE WHEN j."job_status" = 'error' THEN 1 ELSE 0 END) as "error_count"
            FROM {JOBS_FQN} j
            WHERE j."job_run_id" LIKE '%.%' AND j."job_billed_credits_used" IS NOT NULL {date_filter}
            GROUP BY 1
        ),
        flow_configs AS (
            SELECT "kbc_component_configuration_id", "kbc_component_configuration" as "flow_name", "configuration_json"
            FROM {CONFIGS_FQN}
            WHERE "kbc_component_id" LIKE '%orchestrator%' OR "kbc_component_id" LIKE '%flow%'
        )
        SELECT fc."flow_name", fc."configuration_json",
            SUM(cj."credits") as "total_credits", COUNT(DISTINCT cj."parent_job_id") as "run_count",
            SUM(cj."data_transferred_mb") as "total_data_mb", SUM(cj."task_count") as "total_tasks",
            SUM(cj."success_count") as "successful_tasks", SUM(cj."error_count") as "failed_tasks",
            SUM(CASE WHEN cj."data_transferred_mb" > 0 THEN 1 ELSE 0 END) as "runs_with_data_change"
        FROM child_jobs cj
        JOIN flow_jobs fj ON cj."parent_job_id" = SPLIT_PART(fj."kbc_job_id", '_', 1)
        {org_join}
        JOIN flow_configs fc ON fj."kbc_component_configuration_id" = fc."kbc_component_configuration_id"
        WHERE 1=1 {org_where}
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 30
    """)
    if not df.empty:
        df["total_credits"] = pd.to_numeric(df["total_credits"], errors="coerce").fillna(0)
        df["run_count"] = pd.to_numeric(df["run_count"], errors="coerce").fillna(0).astype(int)
        df["total_data_mb"] = pd.to_numeric(df["total_data_mb"], errors="coerce").fillna(0)
        df["total_tasks"] = pd.to_numeric(df["total_tasks"], errors="coerce").fillna(0).astype(int)
        df["successful_tasks"] = pd.to_numeric(df["successful_tasks"], errors="coerce").fillna(0).astype(int)
        df["failed_tasks"] = pd.to_numeric(df["failed_tasks"], errors="coerce").fillna(0).astype(int)
        df["runs_with_data_change"] = pd.to_numeric(df["runs_with_data_change"], errors="coerce").fillna(0).astype(int)
        df["avg_credits_per_run"] = (df["total_credits"] / df["run_count"].replace(0, 1)).round(4)
        df["avg_data_per_run_mb"] = (df["total_data_mb"] / df["run_count"].replace(0, 1)).round(2)
        df["data_change_rate"] = ((df["runs_with_data_change"] / df["run_count"].replace(0, 1)) * 100).round(1)
        df["use_case"] = df["configuration_json"].apply(generate_use_case_summary)
    return df

@st.cache_data(ttl=300)
def build_lineage_index(org_filter=None):
    configs_df = get_configurations_with_mappings(org_filter)
    table_to_configs = {}
    for _, row in configs_df.iterrows():
        config_json = row.get("configuration_json", "")
        if not config_json or pd.isna(config_json):
            continue
        try:
            config = json.loads(config_json)
            storage = config.get("storage", {})
            input_tables = [t.get("source", "") for t in storage.get("input", {}).get("tables", []) if t.get("source")]
            output_tables = [t.get("destination", "") for t in storage.get("output", {}).get("tables", []) if t.get("destination")]
            config_info = {
                "config_id": row.get("kbc_component_configuration_id", ""),
                "config_name": row.get("config_name", "Unknown"),
                "component_id": row.get("kbc_component_id", ""),
                "component_name": row.get("component_name", "Unknown"),
                "component_type": row.get("kbc_component_type", "other"),
                "project_id": row.get("kbc_project_id", ""),
                "input_tables": input_tables,
                "output_tables": output_tables,
            }
            for source in input_tables:
                if source not in table_to_configs:
                    table_to_configs[source] = []
                table_to_configs[source].append({**config_info, "direction": "input"})
            for dest in output_tables:
                if dest not in table_to_configs:
                    table_to_configs[dest] = []
                table_to_configs[dest].append({**config_info, "direction": "output"})
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
    return table_to_configs

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🛡️ SENTINEL")
    st.caption("Data Governance Suite")
    st.divider()
    st.markdown("### 🏢 Organization")
    orgs_df = get_organizations()
    org_options = ["All Organizations"] + sorted(orgs_df["kbc_organization"].dropna().unique().tolist()) if not orgs_df.empty else ["All Organizations"]
    try:
        org_index = org_options.index(st.session_state.selected_org)
    except ValueError:
        org_index = 0
    selected_org = st.selectbox("Filter by Organization", org_options, index=org_index, key="org_selector", label_visibility="collapsed")
    st.session_state.selected_org = selected_org
    st.markdown(f"""
        <div class="org-selection-box">
            <div class="org-selection-label">Currently Selected</div>
            <div class="org-selection-value">{selected_org}</div>
        </div>
    """, unsafe_allow_html=True)
    st.caption("ℹ️ Only one organization can be selected at a time")
    st.divider()
    page = st.radio("Navigation", ["💰 ROI", "📊 Asset Inventory", "🧪 Impact Analysis"], label_visibility="collapsed")
    st.divider()
    st.caption("Powered by Keboola Telemetry")

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════

reg = get_governance_data(selected_org)
project_names = get_project_names(selected_org)
project_id_mapping = get_project_id_mapping()
if not reg.empty:
    reg["project_name"] = reg["project_id"].astype(str).map(project_names).fillna(reg["project_id"])
    reg["kbc_project_id"] = reg["project_id"].astype(str).map(project_id_mapping)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ROI
# ══════════════════════════════════════════════════════════════════════════════

if page == "💰 ROI":
    st.title("💰 ROI Analysis")
    if selected_org != "All Organizations":
        st.caption(f"Cost attribution and return on investment analysis by flow • **{selected_org}**")
    else:
        st.caption("Cost attribution and return on investment analysis by flow")

    st.markdown("### ⚙️ Settings")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        date_range = st.date_input("Date Range", value=(st.session_state.date_range_start, st.session_state.date_range_end), key="date_range_input")
        if isinstance(date_range, tuple) and len(date_range) == 2:
            st.session_state.date_range_start = date_range[0]
            st.session_state.date_range_end = date_range[1]
    with col2:
        cost_per_ppu = st.number_input("Cost per PPU ($)", min_value=0.0, value=st.session_state.cost_per_ppu, step=0.01, format="%.2f", key="ppu_input")
        st.session_state.cost_per_ppu = cost_per_ppu
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh_btn = st.button("🔄 Refresh")

    st.divider()

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date = date_range[0].strftime("%Y-%m-%d")
        end_date = date_range[1].strftime("%Y-%m-%d")
        days_in_range = max((date_range[1] - date_range[0]).days, 1)
        weeks_in_range = days_in_range / 7
        months_in_range = days_in_range / 30.44
    else:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        days_in_range, weeks_in_range, months_in_range = 90, 90/7, 90/30.44

    flow_data = get_cost_per_flow(start_date, end_date, selected_org)

    if not flow_data.empty and flow_data["total_credits"].sum() > 0:
        flow_data["total_cost_usd"] = flow_data["total_credits"] * cost_per_ppu
        flow_data["cost_per_run_usd"] = flow_data["avg_credits_per_run"] * cost_per_ppu
        flow_data["runs_per_week"] = (flow_data["run_count"] / weeks_in_range).round(1)
        flow_data["runs_per_month"] = (flow_data["run_count"] / months_in_range).round(1)

        total_credits = flow_data["total_credits"].sum()
        total_cost = total_credits * cost_per_ppu
        total_runs = flow_data["run_count"].sum()
        avg_cost_per_run = total_cost / total_runs if total_runs > 0 else 0
        total_data_mb = flow_data["total_data_mb"].sum()
        total_tasks = flow_data["total_tasks"].sum()
        success_rate = (flow_data["successful_tasks"].sum() / total_tasks * 100) if total_tasks > 0 else 0

        st.markdown(f"### 📊 Key Metrics")
        st.caption(f"Statistics for {start_date} to {end_date}")
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_kpi("Avg $ per Flow Run", f"${avg_cost_per_run:.2f}", "#dc2626")
        with c2: render_kpi("Total Cost", f"${total_cost:,.2f}", "#3b82f6")
        with c3: render_kpi("Total Runs", f"{total_runs:,}", "#16a34a")
        with c4: render_kpi("Total PPU", f"{total_credits:,.1f}", "#8b5cf6")
        st.markdown("")
        c5, c6, c7, c8 = st.columns(4)
        with c5: render_kpi("Unique Flows", len(flow_data), "#3b82f6")
        with c6: render_kpi("Total Tasks", f"{total_tasks:,}", "#16a34a")
        with c7: render_kpi("Success Rate", f"{success_rate:.1f}%", "#16a34a" if success_rate > 90 else "#ca8a04")
        with c8: render_kpi("Data Moved", format_data_size(total_data_mb), "#8b5cf6")

        st.divider()
        st.markdown("### 💵 Top 10 Flows by Cost")
        st.caption("Flows ranked by total dollar cost. Hover over bars for details.")

        chart_data = flow_data.head(10).copy().sort_values("total_cost_usd", ascending=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data["total_cost_usd"].tolist(), y=chart_data["flow_name"].tolist(), orientation='h',
            marker=dict(color=chart_data["total_cost_usd"].tolist(), colorscale='Reds', line=dict(color='#991b1b', width=1)),
            text=[f"${v:,.2f}" for v in chart_data["total_cost_usd"]], textposition='outside', textfont=dict(color='#1e293b', size=12),
            customdata=chart_data[["cost_per_run_usd", "run_count", "use_case"]].values,
            hovertemplate="<b>%{y}</b><br>Total Cost: $%{x:,.2f}<br>Avg Cost/Run: $%{customdata[0]:,.2f}<br>Runs: %{customdata[1]:,}<br>Use Case: %{customdata[2]}<extra></extra>"
        ))
        fig.update_layout(height=450, margin=dict(l=20, r=80, t=20, b=20), paper_bgcolor='#f8fafc', plot_bgcolor='#ffffff', font=dict(color='#1e293b', size=12), showlegend=False)
        fig.update_xaxes(title_text="Total Cost ($)", title_font=dict(color='#1e293b'), tickfont=dict(color='#475569'), tickprefix="$", gridcolor='#e2e8f0')
        fig.update_yaxes(title_text="", tickfont=dict(color='#1e293b', size=10), gridcolor='#e2e8f0')
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("### 📋 Flow Cost Details")
        st.caption("Detailed breakdown of cost per flow with use case summary.")

        display_flow = flow_data[["flow_name", "use_case", "total_cost_usd", "cost_per_run_usd", "run_count", "runs_per_week", "runs_per_month", "avg_data_per_run_mb", "total_credits"]].copy()
        display_flow["total_cost_usd"] = display_flow["total_cost_usd"].round(2)
        display_flow["cost_per_run_usd"] = display_flow["cost_per_run_usd"].round(4)
        display_flow["total_credits"] = display_flow["total_credits"].round(2)
        display_flow.columns = ["Flow Name", "Use Case", "Total Cost ($)", "Cost/Run ($)", "Runs", "Runs/Week", "Runs/Month", "Avg Data/Run (MB)", "PPU Credits"]

        st.dataframe(display_flow, use_container_width=True, hide_index=True,
            column_config={
                "Use Case": st.column_config.TextColumn(help="Auto-generated summary based on flow components", width="medium"),
                "Total Cost ($)": st.column_config.NumberColumn(format="$%.2f"),
                "Cost/Run ($)": st.column_config.NumberColumn(format="$%.4f"),
                "Runs/Week": st.column_config.NumberColumn(format="%.1f"),
                "Runs/Month": st.column_config.NumberColumn(format="%.1f"),
                "Avg Data/Run (MB)": st.column_config.NumberColumn(format="%.2f"),
                "PPU Credits": st.column_config.NumberColumn(format="%.2f"),
            })

        st.divider()
        st.markdown("### 🔄 Data Change Insights")
        no_data_flows = flow_data[flow_data["data_change_rate"] == 0]
        low_data_flows = flow_data[(flow_data["data_change_rate"] > 0) & (flow_data["data_change_rate"] < 50)]
        col1, col2 = st.columns(2)
        with col1:
            if not no_data_flows.empty:
                st.warning(f"⚠️ **{len(no_data_flows)} flow(s)** ran without transferring any data:")
                for _, row in no_data_flows.head(5).iterrows():
                    st.markdown(f"- **{row['flow_name']}**: {row['run_count']} runs, ${row['total_cost_usd']:.2f} spent")
            else:
                st.success("✅ All flows transferred data during their runs!")
        with col2:
            if not low_data_flows.empty:
                st.info(f"💡 **{len(low_data_flows)} flow(s)** have <50% data change rate:")
                for _, row in low_data_flows.head(5).iterrows():
                    st.markdown(f"- **{row['flow_name']}**: {row['data_change_rate']:.1f}% of runs had data changes")
    else:
        st.info("No flow cost data available for the selected date range and organization.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ASSET INVENTORY
# ══════════════════════════════════════════════════════════════════════════════

elif page == "📊 Asset Inventory":
    st.title("📊 Asset Inventory & Cleanup")
    st.caption(f"Centralized registry of data assets • **{selected_org}**" if selected_org != "All Organizations" else "Centralized registry of data assets")

    if not reg.empty:
        c1, c2, c3, c4 = st.columns(4)
        with c1: render_kpi("Total Assets", len(reg), "#3b82f6")
        with c2: render_kpi("SLA Compliance", f"{(reg['health'] == '🟢 Healthy').mean():.0%}", "#16a34a")
        with c3: render_kpi("Stale Assets", len(reg[reg['health'] == '🔴 Stale']), "#dc2626")
        with c4: render_kpi("Shared Tables", int(reg['is_shared'].sum()), "#ca8a04")

        st.divider()
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: search = st.text_input("🔍 Search tables", placeholder="Filter by name...")
        with col2: health_filter = st.selectbox("Filter by Health", ["All", "🟢 Healthy", "🟡 Warning", "🔴 Stale"])
        with col3: shared_filter = st.selectbox("Shared Status", ["All", "Shared Only", "Non-shared Only"])

        filtered = reg.copy()
        if search: filtered = filtered[filtered['table_name'].str.contains(search, case=False, na=False)]
        if health_filter != "All": filtered = filtered[filtered['health'] == health_filter]
        if shared_filter == "Shared Only": filtered = filtered[filtered['is_shared'] == True]
        elif shared_filter == "Non-shared Only": filtered = filtered[filtered['is_shared'] == False]

        st.divider()
        st.markdown(f"### Showing {len(filtered)} assets")
        for _, row in filtered.head(100).iterrows():
            table_url = get_table_url(row['id'], row.get('kbc_project_id'))
            with st.container(border=True):
                cols = st.columns([3, 2, 1, 1, 1])
                table_label = f"🔗 {row['table_name']}" if row.get('is_shared') else row['table_name']
                cols[0].markdown(f"**[{table_label}]({table_url})**" if table_url else f"**{table_label}**")
                cols[1].write(row.get('project_name', row['project_id']))
                cols[2].write(row['health'])
                cols[3].write(f"{row['hours_stale']} h")
                cols[4].write(f"{row.get('rows', 0):,} rows")
        if len(filtered) > 100: st.info(f"Showing first 100 of {len(filtered)} tables.")
    else:
        st.info("No tables found. Try selecting 'All Organizations'.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IMPACT ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🧪 Impact Analysis":
    st.title("🧪 Schema Impact Analysis")
    st.caption(f"Analyze dependencies before schema changes • **{selected_org}**" if selected_org != "All Organizations" else "Analyze dependencies before schema changes")

    with st.spinner("Building lineage index..."):
        lineage_index = build_lineage_index(selected_org)
        all_tables = get_all_tables(selected_org)

    if all_tables.empty:
        st.warning("No tables found. Try a different organization.")
    else:
        table_options = sorted(all_tables["name"].dropna().unique().tolist())
        selected_table = st.selectbox("Select a table to analyze impact", table_options)

        if selected_table:
            matching_configs = []
            for table_key, configs in lineage_index.items():
                if selected_table in table_key or table_key.endswith(f".{selected_table}"):
                    matching_configs.extend(configs)
            seen = set()
            unique_configs = []
            for c in matching_configs:
                key = (c["config_id"], c["direction"])
                if key not in seen:
                    seen.add(key)
                    unique_configs.append(c)
            readers = [c for c in unique_configs if c["direction"] == "input"]
            writers = [c for c in unique_configs if c["direction"] == "output"]
            affected_tables = set()
            for r in readers:
                for t in r.get("output_tables", []):
                    if t and t != selected_table:
                        affected_tables.add(t)

            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            with c1: render_kpi("Downstream Configs", len(readers), "#dc2626")
            with c2: render_kpi("Upstream Configs", len(writers), "#16a34a")
            with c3: render_kpi("Affected Tables", len(affected_tables), "#8b5cf6")
            with c4: render_kpi("Total Dependencies", len(unique_configs), "#3b82f6")

            st.divider()
            st.markdown("### Dependency Graph")
            dot = graphviz.Digraph(comment="Table Lineage")
            dot.attr(rankdir='LR', bgcolor='#f8fafc')
            dot.node('selected', selected_table, shape='box', style='filled', fillcolor='#3b82f6', fontcolor='white')
            for i, w in enumerate(writers[:8]):
                dot.node(f"w{i}", f"{w['config_name'][:25]}\\n({w['component_name'][:20]})", shape='box', style='filled', fillcolor='#16a34a', fontcolor='white')
                dot.edge(f"w{i}", 'selected', color='#16a34a')
            for i, r in enumerate(readers[:8]):
                fillcolor = '#ca8a04' if "transformation" in r.get("component_type", "").lower() else '#dc2626' if "writer" in r.get("component_type", "").lower() else '#64748b'
                dot.node(f"r{i}", f"{r['config_name'][:25]}\\n({r['component_name'][:20]})", shape='box', style='filled', fillcolor=fillcolor, fontcolor='white')
                dot.edge('selected', f"r{i}", color='#dc2626')
            if not readers and not writers:
                dot.node('none', 'No dependencies found', shape='plaintext')
            st.graphviz_chart(dot)

            if readers or affected_tables:
                st.divider()
                st.warning(f"⚠️ Modifying `{selected_table}` will affect **{len(readers)} config(s)** and **{len(affected_tables)} table(s)**.")

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.caption("🛡️ Sentinel | Data Governance Suite | Refreshes every 5 minutes")
