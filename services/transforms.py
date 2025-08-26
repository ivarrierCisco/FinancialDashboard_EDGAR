# services/transforms.py
#This file contains functions to transform and analyze financial data fetched from the SEC EDGAR API.
import pandas as pd
from typing import Dict, Optional
from config import COMMON_TAGS

def parse_data(json_data: Dict) -> pd.DataFrame:
    records = []
    for entry in json_data.get("units", {}).get("USD", []):
        frame = entry.get("frame", "")
        if "end" in entry and frame and "Q" in frame:
            records.append({
                "date": entry["end"],
                "val": entry["val"],
                "form": entry.get("form",""),
                "fy": entry.get("fy",""),
                "fp": entry.get("fp",""),
                "frame": frame
            })
    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False)
    return df

def build_financial_table(cik: str, revenue_tag: str, fetcher) -> pd.DataFrame:
    all_data = pd.DataFrame()
    tags = {"Revenue": revenue_tag, **COMMON_TAGS}

    for label, tag in tags.items():
        js = fetcher.fetch_concept(cik, tag)
        if js:
            df = parse_data(js)
            if not df.empty:
                df = df.rename(columns={"val": label})
                df = df[["date","frame",label]]
                all_data = df if all_data.empty else all_data.merge(df, on=["date","frame"], how="outer")

    if all_data.empty:
        return all_data

    all_data = all_data.sort_values("date", ascending=False)
    all_data["Quarter"] = all_data["frame"]
    all_data = all_data.dropna(subset=["Revenue"])

    if "Gross Profit" in all_data.columns:
        all_data = all_data.dropna(subset=["Gross Profit"])
        all_data["Gross Margin"] = all_data["Gross Profit"] / all_data["Revenue"]

    all_data = all_data.drop_duplicates(subset=["Quarter"], keep="first").reset_index(drop=True)
    return all_data

def compute_changes(df: pd.DataFrame, selected_quarter: str):
    metric_cols = [c for c in ["Revenue","Gross Profit","Net Income","Cash Flow","Gross Margin"] if c in df.columns]
    row = df[df["Quarter"] == selected_quarter]
    if row.empty:
        raise ValueError(f"Selected quarter {selected_quarter} not found.")
    current = row[metric_cols].iloc[0]
    qoq = pd.Series("N/A", index=metric_cols)
    yoy = pd.Series("N/A", index=metric_cols)

    if selected_quarter.startswith("CY") and "Q" in selected_quarter:
        year = int(selected_quarter[2:6])
        q = int(selected_quarter[-1])
        prev_q = f"CY{year}Q{q-1}" if q > 1 else f"CY{year-1}Q4"
        prev_y = f"CY{year-1}Q{q}"

        for label, ref in [("qoq", prev_q), ("yoy", prev_y)]:
            ref_row = df[df["Quarter"] == ref]
            if not ref_row.empty:
                ref_vals = ref_row[metric_cols].iloc[0]
                for col in metric_cols:
                    if pd.notna(current[col]) and pd.notna(ref_vals[col]) and ref_vals[col] != 0:
                        pct = (current[col] - ref_vals[col]) / ref_vals[col]
                        (qoq if label=="qoq" else yoy)[col] = pct

    return current, qoq, yoy
