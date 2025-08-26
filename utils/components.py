# utils/components.py
from streamlit.components.v1 import html as html_component

def copy_button(label: str, text: str):
    code = f"""
    <button onclick="navigator.clipboard.writeText(decodeURIComponent('{text}'));">
      📋 {label}
    </button>
    """
    html_component(code, height=40)
