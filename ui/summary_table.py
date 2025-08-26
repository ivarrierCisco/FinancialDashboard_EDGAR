# ui/summary_table.py
import pandas as pd
import streamlit as st

def format_for_display(current, qoq, yoy) -> pd.DataFrame:
    combined = pd.DataFrame({"Current": current, "QoQ Change": qoq, "YoY Change": yoy})
    def _fmt(row):
        out = {}
        for col, val in row.items():
            if isinstance(val, float):
                if "Margin" in row.name:
                    out[col] = f"{val:.1%}"
                elif "Change" in col:
                    out[col] = f"{val:.1%}"
                else:
                    out[col] = f"${val:,.0f}"
            else:
                out[col] = val
        return pd.Series(out)
    return combined.apply(_fmt, axis=1)

def editable_table(df_formatted, title: str):
    st.subheader(title)
    init = df_formatted.copy()
    init.index.name = "Metric"
    init = init.reset_index()

    include_row_notes = st.checkbox("Add a per-row Notes column", value=False, key="fin_row_notes_toggle")
    if include_row_notes and "Notes" not in init.columns:
        init["Notes"] = ""

    col_cfg = {
        "Metric": st.column_config.TextColumn(required=True, width="large"),
        "Current": st.column_config.TextColumn(help="Edit freely (e.g. $3,591,000,000)"),
        "QoQ Change": st.column_config.TextColumn(help="e.g. +5%, -1%, N/A"),
        "YoY Change": st.column_config.TextColumn(help="e.g. +5%, -1%, N/A"),
    }
    if include_row_notes:
        col_cfg["Notes"] = st.column_config.TextColumn(
            help="Multi-line supported (Shift+Enter). Use • or - for bullets.",
            width="large"
        )

    return st.data_editor(
        init, use_container_width=True, hide_index=True, num_rows="dynamic",
        column_config=col_cfg, key="editable_fin_summary"
    ), include_row_notes
