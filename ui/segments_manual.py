# ui/segments_manual.py
from __future__ import annotations
import re
import pandas as pd
import streamlit as st
from config import DEFAULT_MARKETS

def _parse_percent(x) -> float | None:
    """Accept 0.24, 24, '24%', '0.24' → returns 0..1 or None."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s:
        return None
    m = re.match(r"^\s*([+-]?\d+(\.\d+)?)\s*%?\s*$", s)
    if not m:
        return None
    val = float(m.group(1))
    return val / 100 if val > 1 else val

def _fmt_pct(p) -> str:
    return "" if p is None or (isinstance(p, float) and pd.isna(p)) else f"{p:.1%}"

def render_manual_segments(
    product_revenue_default: float | None,
    fy_default: int | None,
    preset_markets: list[str] = DEFAULT_MARKETS,
    state_key: str = "segments_manual_df",
) -> pd.DataFrame:
    """
    Interactive editor for Markets/Sectors. Returns tidy DF with:
    ['FY','Market','ShareOfProductRevenue','Revenue','Sectors','Notes','ProductRevenueTotal']
    """
    st.subheader("🧮 Markets / Sectors (Manual Input)")
    with st.expander("How this works", expanded=False):
        st.markdown(
            "- Enter **Share %** (e.g., 24 or 24%).\n"
            "- Optionally type **Revenue** directly; otherwise it is computed from Product Revenue × Share %.\n"
            "- Add/remove rows; edit Sectors/Notes freely.\n"
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        fy = st.number_input("Fiscal Year (FY)", value=(fy_default or 0), step=1, format="%d")
        fy = int(fy) if fy else None
    with c2:
        product_rev_text = st.text_input(
            "Product Revenue total (USD)",
            value=("" if product_revenue_default is None else f"{product_revenue_default:.0f}"),
            help="Leave blank to skip auto-calculation."
        )
    with c3:
        auto_calc = st.checkbox("Auto-calc Revenue from Share %", value=True)

    # Session state initialization
    if state_key not in st.session_state:
        st.session_state[state_key] = pd.DataFrame({
            "Market": preset_markets,
            "Share %": [""] * len(preset_markets),
            "Revenue": [""] * len(preset_markets),
            "Sectors": [""] * len(preset_markets),
            "Notes":   [""] * len(preset_markets),
        })

    edited = st.data_editor(
        st.session_state[state_key],
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "Market":  st.column_config.TextColumn(required=True, help="e.g., Industrial"),
            "Share %": st.column_config.TextColumn(help="e.g., 24 or 24%"),
            "Revenue": st.column_config.TextColumn(help="Override computed amount (USD)"),
            "Sectors": st.column_config.TextColumn(help="Comma- or newline-separated list"),
            "Notes":   st.column_config.TextColumn(help="Any commentary"),
        },
        key=f"{state_key}_editor"
    )
    st.session_state[state_key] = edited.copy()

    # Parse product revenue number
    product_rev_num = None
    if product_rev_text.strip():
        try:
            product_rev_num = float(product_rev_text.replace(",", ""))
        except Exception:
            product_rev_num = None

    # Normalize + compute
    shares, revenues = [], []
    for _, row in edited.iterrows():
        p = _parse_percent(row.get("Share %"))
        r_text = str(row.get("Revenue") or "").replace(",", "").strip()
        r = None
        if r_text and re.match(r"^[+-]?\d+(\.\d+)?$", r_text):
            r = float(r_text)
        if auto_calc and r is None and product_rev_num is not None and p is not None:
            r = product_rev_num * p
        shares.append(p)
        revenues.append(r)

    total_pct = sum([x for x in shares if x is not None]) if shares else None
    total_rev = sum([x for x in revenues if x is not None]) if revenues else None

    v1, v2 = st.columns(2)
    with v1:
        st.metric("Sum of Share %", _fmt_pct(total_pct) if total_pct is not None else "—")
    with v2:
        st.metric("Sum of Revenue", f"${total_rev:,.0f}" if total_rev else "—",
                  delta=(f"target ${product_rev_num:,.0f}" if product_rev_num else None))

    if product_rev_num and total_rev and abs(total_rev - product_rev_num) > max(0.005*product_rev_num, 1):
        st.warning("Sum of Revenue does not match Product Revenue total (±0.5% tolerance).")
    if total_pct and abs(total_pct - 1.0) > 0.005:
        st.info("Share % does not sum to ~100% (±0.5%).")

    out = pd.DataFrame({
        "FY": [fy] * len(edited),
        "Market": edited["Market"],
        "ShareOfProductRevenue": [None if p is None else round(p, 6) for p in shares],
        "Revenue": revenues,
        "Sectors": edited["Sectors"],
        "Notes": edited["Notes"],
        "ProductRevenueTotal": [product_rev_num] * len(edited),
    })

    # Pretty on-screen view
    view = out.copy()
    view["ShareOfProductRevenue"] = view["ShareOfProductRevenue"].apply(lambda x: "" if x is None else f"{x*100:.1f}%")
    view["Revenue"] = view["Revenue"].apply(lambda x: "" if x is None else f"${x:,.0f}")
    st.dataframe(view, use_container_width=True)

    return out
