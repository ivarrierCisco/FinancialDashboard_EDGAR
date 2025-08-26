# utils/cache.py
import streamlit as st

@st.cache_resource
def get_resource(_factory):
    return _factory()

def cached_data(ttl=3600):
    return st.cache_data(ttl=ttl)
