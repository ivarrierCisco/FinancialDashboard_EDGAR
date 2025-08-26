# ui/charts.py
#This file contains functions to create and display charts for financial metrics using Streamlit.
import streamlit as st

def plot_metric(df, metric: str, title: str):
    if metric not in df.columns:
        st.warning(f"Metric '{metric}' not found.")
        return
    chart_df = df[["date", metric]].dropna()
    if chart_df.empty:
        st.info(f"No data for {title} in the selected range.")
        return
    st.subheader(title)
    st.line_chart(chart_df.set_index("date"), use_container_width=True)
