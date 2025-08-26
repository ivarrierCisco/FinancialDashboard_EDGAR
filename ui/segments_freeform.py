# ui/segments_freeform.py
from __future__ import annotations
import pandas as pd
import streamlit as st
from config import DEFAULT_MARKETS

DEFAULT_COLUMNS = [
    "Segment (% of Revenue)",
    "Revenue (€M)",
    "QoQ Change",
    "YoY Change",
    "Growth Drivers",
    "Notes",
]

def render_freeform_segments(
    columns: list[str] = DEFAULT_COLUMNS,
    default_rows: list[str] = DEFAULT_MARKETS,   # ← new
    state_key: str = "segments_freeform_df",
    title: str = "🗂️ Segments (Manual Freeform)"
) -> pd.DataFrame:
    """
    Renders an editable table. Prefills the 'Segment (% of Revenue)' column
    with typical industry segments, but everything is editable and rows are dynamic.
    """
    st.subheader(title)

    # Initialize once: prefill first column; other columns empty
    if state_key not in st.session_state:
        init = pd.DataFrame(columns=columns)
        if "Segment (% of Revenue)" in columns and default_rows:
            init["Segment (% of Revenue)"] = default_rows
        st.session_state[state_key] = init

    # Optional quick actions
    a1, a2 = st.columns(2)
    with a1:
        if st.button("➕ Add blank row"):
            st.session_state[state_key] = pd.concat(
                [st.session_state[state_key], pd.DataFrame({c: [""] for c in columns})],
                ignore_index=True
            )
    with a2:
        if st.button("🧹 Clear all rows"):
            st.session_state[state_key] = pd.DataFrame(columns=columns)

    df = st.data_editor(
        st.session_state[state_key],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",  # users can add/remove rows
        column_config={c: st.column_config.TextColumn() for c in columns},
        key=f"{state_key}_editor",
    )

    st.session_state[state_key] = df.copy()
    return df.copy()
