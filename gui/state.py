# gui/state.py
import streamlit as st
def init_state():
    defaults = {
        "src_text": None, "file_name": None, "working_path": None,
        "grouped": {}, "corrections_str": "", "year": 2025, "month": 10
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v