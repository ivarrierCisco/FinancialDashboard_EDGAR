# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.cache import get_resource, cached_data
from services.sec_api import SECDataFetcher
from services.transforms import build_financial_table, compute_changes
from ui.company_picker import render as pick_company
from ui.summary_table import format_for_display, editable_table
from ui.charts import plot_metric
from ui.exports import render_downloads_combined 
from ui.segments_manual import render_manual_segments
from ui.segments_freeform import render_freeform_segments
from config import COMMON_TAGS

st.set_page_config(page_title="SEC Financial Dashboard", layout="wide")
st.title("📊 SEC Financial Dashboard (EDGAR)")

# 1) Resource (cached)
fetcher = get_resource(lambda: SECDataFetcher())

# 2) Company picker
company = pick_company(fetcher)
if not company:
    st.info("Select a company to begin.")
    st.stop()

# 3) Resolve CIK + revenue tag
cik = fetcher.get_company_cik(company)
if not cik:
    st.error(f"Could not find CIK for {company}.")
    st.stop()

revenue_tag = fetcher.best_revenue_tag(company, cik)
st.info(f"**Selected Company:** {company} | **CIK:** {cik} | **Revenue Tag:** {revenue_tag}")

# 4) Load & cache data
@cached_data(ttl=3600)
def load(cik: str, revenue_tag: str, company_name: str):
    return build_financial_table(cik, revenue_tag, fetcher)

with st.spinner(f"Loading financial data for {company}..."):
    df = load(cik, revenue_tag, company)

if df.empty:
    st.warning(f"No financial data available for {company}.")
    st.write("- The company may not file standard XBRL")
    st.write("- The revenue tag mapping may need adjustment")
    st.write("- The company could be newly public with limited data")
    st.stop()

# 5) Current metrics
available_q = sorted(df["Quarter"].unique().tolist(), reverse=True)
selected_q = st.selectbox("Select Quarter", options=available_q)

try:
    current, qoq, yoy = compute_changes(df.copy(), selected_q)
    formatted = format_for_display(current, qoq, yoy)
    st.subheader(f"📈 Financial Summary for {company} – {selected_q}")
    st.table(formatted)
except Exception as e:
    st.error(f"Error computing financial changes: {e}")

# 6) Historical charts filters
st.subheader(f"📉 Financial Trends for {company}")
df["Year"] = df["date"].dt.year
if df["Year"].empty:
    st.warning("No historical data available for charting.")
else:
    years = sorted(df["Year"].unique())
    yr_min, yr_max = min(years), max(years)
    year_range = st.slider("Select Year Range", min_value=yr_min, max_value=yr_max, value=(yr_min, yr_max))
    quarters = sorted(df["Quarter"].str[-2:].unique())
    selected_quarters = st.multiselect("Select Quarters", options=quarters, default=quarters)

    filtered = df[(df["Year"]>=year_range[0]) & (df["Year"]<=year_range[1]) & (df["Quarter"].str[-2:].isin(selected_quarters))].sort_values("date")

    c1, c2 = st.columns(2)
    with c1:
        plot_metric(filtered, "Revenue", "Revenue Over Time")
        plot_metric(filtered, "Net Income", "Net Income Over Time")
        if "Gross Margin" in filtered.columns:
            plot_metric(filtered, "Gross Margin", "Gross Margin Over Time")
    with c2:
        if "Gross Profit" in filtered.columns:
            plot_metric(filtered, "Gross Profit", "Gross Profit Over Time")
        plot_metric(filtered, "Cash Flow", "Cash Flow Over Time")

# 7) Manual segments
# Derive defaults
fy_default = None
if selected_q.startswith("CY") and "Q" in selected_q:
    try:
        fy_default = int(selected_q[2:6])
    except Exception:
        pass

# Try to get a numeric "Revenue" for auto-calc
product_revenue_default = None
try:
    # 'current' is a Series with raw numbers if from compute_changes
    product_revenue_default = float(current.get("Revenue"))
except Exception:
    pass

# Manual Markets/Sectors section (returns tidy dataframe)
# Derive defaults
fy_default = None
if selected_q.startswith("CY") and "Q" in selected_q:
    try:
        fy_default = int(selected_q[2:6])
    except Exception:
        pass

# Try to get a numeric "Revenue" for auto-calc
product_revenue_default = None
try:
    # 'current' is a Series with raw numbers if from compute_changes
    product_revenue_default = float(current.get("Revenue"))
except Exception:
    pass


# 7) Editable summary + exports
st.subheader(f"📈 Financial Summary for {company} – {selected_q}")
editable_df, include_row_notes = editable_table(formatted, f"{company} — Financial Summary ({selected_q})")
include_notes = st.checkbox("Include a section-level Notes box", value=False, key="fin_notes_toggle")
notes_text = st.text_area("Notes", placeholder="Add context or takeaways…", height=140, key="fin_notes_text") if include_notes else ""

# --- Freeform segments table (prefilled & editable) ---
segments_df = render_freeform_segments()

# --- One set of buttons that download BOTH sections together ---
render_downloads_combined(
    editable_summary_df=editable_df,
    title=f"{company} — Financial Summary ({selected_q})",
    notes_text=notes_text,
    include_notes=include_notes,
    segments_df=segments_df,
)