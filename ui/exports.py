# ui/exports.py
import io
from typing import Optional, List
from datetime import datetime
import pandas as pd
import streamlit as st
from xlsxwriter.utility import xl_rowcol_to_cell
from utils.components import copy_button
from urllib.parse import quote

# ----------------- helpers: formatting & CSV assembly -----------------

def _clean_df_for_text(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["(empty)"])
    out = df.copy()
    # stringify and remove 'nan'
    for c in out.columns:
        out[c] = out[c].apply(lambda v: "" if pd.isna(v) or str(v).lower() == "nan" else str(v))
    return out

def _is_numeric_cell(s: str) -> bool:
    if not s or s.strip() == "": return False
    # accept plain numbers or currency/percent-looking values
    t = s.replace(",", "").replace("$", "").replace("€", "").replace("%", "")
    try:
        float(t)
        return True
    except ValueError:
        return False

def _render_ascii_table(df: pd.DataFrame) -> str:
    """Pretty monospace ASCII with right-aligned numeric columns."""
    df2 = _clean_df_for_text(df)
    cols = list(df2.columns)

    # decide alignment per column
    right_align = []
    for c in cols:
        sample_vals = df2[c].dropna().astype(str).head(20).tolist()
        right_align.append(any(_is_numeric_cell(v) for v in sample_vals))

    # width calc
    widths = []
    for i, c in enumerate(cols):
        data_lens = [len(v) for v in df2[c].astype(str).tolist()]
        widths.append(max(len(str(c)), *(data_lens or [0])))

    def fmt_cell(txt, i):
        txt = str(txt)
        return txt.rjust(widths[i]) if right_align[i] else txt.ljust(widths[i])

    header = " | ".join(fmt_cell(c, i) for i, c in enumerate(cols))
    sep    = "-+-".join("-" * w for w in widths)
    body   = "\n".join(" | ".join(fmt_cell(df2.iloc[r, i], i) for i in range(len(cols)))
                       for r in range(len(df2)))

    return f"{header}\n{sep}\n{body if body else ''}"

def to_plaintext_combined(
    summary_df: pd.DataFrame,
    segments_df: Optional[pd.DataFrame],
    title: str,
    notes_text: str = ""
) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    parts: List[str] = [f"{title}\nGenerated: {ts}\n"]
    parts.append("Financial Summary")
    parts.append(_render_ascii_table(summary_df))
    if notes_text.strip():
        parts.append("\nNotes\n" + notes_text.strip())
    if segments_df is not None and not segments_df.empty:
        parts.append("\nMarkets / Sectors (Manual)")
        parts.append(_render_ascii_table(segments_df))
    return "\n".join(parts).strip() + "\n"

def _to_csv_block(df: pd.DataFrame) -> str:
    """Return CSV block (header+rows) for a DF."""
    return df.to_csv(index=False, lineterminator="\n")

# ----------------- main: one-click buttons (same-sheet CSV/Excel) -----------------

def render_downloads_combined(
    editable_summary_df: pd.DataFrame,
    title: str,
    notes_text: str,
    include_notes: bool,
    segments_df: Optional[pd.DataFrame] = None,
):
    """
    Buttons that download BOTH sections together:
      • CSV (single file): Financial Summary block, blank line, Segments block (same sheet)
      • Excel (single worksheet "Report"): title/timestamp, Summary, optional Notes, Segments
      • Plaintext: pretty monospace (no 'nan', right-aligned numerics)
    """
    safe_title = title.replace(" ", "_")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ------- CSV (single file with both tables stacked) -------
    csv_blocks = [f"# {title}", f"# Generated: {ts}", ""]
    csv_blocks += ["# Financial Summary", _to_csv_block(editable_summary_df).rstrip()]
    if include_notes and notes_text.strip():
        # Put notes as a small 1-col CSV block
        csv_blocks += ["", "# Notes", '"{}"'.format(notes_text.replace('"', '""').replace("\n", "\\n"))]
    if segments_df is not None and not segments_df.empty:
        csv_blocks += ["", "# Markets / Sectors (Manual)", _to_csv_block(segments_df).rstrip()]
    csv_bytes = ("\n".join(csv_blocks) + "\n").encode("utf-8")

    # ------- Excel (single worksheet) -------
    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine="xlsxwriter") as writer:
        ws_name = "Report"
        start_row = 0

        # Create worksheet up front so we can write headings
        editable_summary_df.head(0).to_excel(writer, index=False, sheet_name=ws_name)
        ws = writer.sheets[ws_name]

        # Title + timestamp
        title_fmt = writer.book.add_format({"bold": True, "font_size": 14})
        meta_fmt  = writer.book.add_format({"font_color": "#666666"})
        ws.write(start_row, 0, title, title_fmt); start_row += 1
        ws.write(start_row, 0, f"Generated: {ts}", meta_fmt); start_row += 2

        # Financial Summary
        section_fmt = writer.book.add_format({"bold": True})
        ws.write(start_row, 0, "Financial Summary", section_fmt); start_row += 1
        editable_summary_df.to_excel(writer, index=False, sheet_name=ws_name, startrow=start_row)
        start_row += len(editable_summary_df) + 2  # header + rows + 1 gap

        # Notes (optional)
        if include_notes and notes_text.strip():
            ws.write(start_row, 0, "Notes", section_fmt); start_row += 1
            wrap = writer.book.add_format({"text_wrap": True})
            ws.write(start_row, 0, notes_text, wrap)
            start_row += 2

        # Segments (optional)
        if segments_df is not None and not segments_df.empty:
            ws.write(start_row, 0, "Markets / Sectors (Manual)", section_fmt); start_row += 1
            segments_df.to_excel(writer, index=False, sheet_name=ws_name, startrow=start_row)
            start_row += len(segments_df) + 1

        # Autofit simple widths for first sheet columns (up to max of both tables)
        max_cols = 0
        if not editable_summary_df.empty:
            max_cols = max(max_cols, len(editable_summary_df.columns))
        if segments_df is not None and not segments_df.empty:
            max_cols = max(max_cols, len(segments_df.columns))
        for col in range(max_cols):
            ws.set_column(col, col, 20)

    xlsx_buf.seek(0)

    # ------- Plaintext (both sections) -------
    plaintext = to_plaintext_combined(
        summary_df=editable_summary_df,
        segments_df=segments_df,
        title=title,
        notes_text=notes_text if include_notes else ""
    )

    # ------- Buttons -------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button(
            "⬇️ Download CSV (both sections)",
            data=csv_bytes,
            file_name=f"{safe_title}.csv",
            mime="text/csv",
        )
    with c2:
        st.download_button(
            "⬇️ Download Excel (both sections)",
            data=xlsx_buf.getvalue(),
            file_name=f"{safe_title}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with c3:
        st.download_button(
            "⬇️ Download Plaintext (both sections)",
            data=plaintext.encode("utf-8"),
            file_name=f"{safe_title}.txt",
            mime="text/plain",
        )
    with c4:
        copy_button("Copy plaintext", quote(plaintext))
