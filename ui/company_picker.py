# ui/company_picker.py
import streamlit as st
from config import DEFAULT_COMPANIES

def render(fetcher) -> str | None:
    st.subheader("🏢 Company Selection")
    tab1, tab2 = st.tabs(["Quick Select", "Search All Companies"])

    def picked_quick(): st.session_state["full_search"] = ""
    def picked_full():  st.session_state["quick_select"] = None

    with tab1:
        st.selectbox(
            "Choose from popular companies:",
            options=DEFAULT_COMPANIES,
            key="quick_select",
            on_change=picked_quick
        )

    with tab2:
        with st.spinner("Loading company database..."):
            all_companies = fetcher.get_company_list()
        if not all_companies:
            st.error("Unable to load company database. Please try again later.")
            return None
        names = [c["name"] for c in all_companies]
        st.selectbox(
            "Search and select any public company:",
            options=[""] + names,
            key="full_search",
            help="Type to search through all SEC-registered companies",
            on_change=picked_full
        )

    return st.session_state.get("full_search") or st.session_state.get("quick_select")
