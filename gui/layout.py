# gui/layout.py
import streamlit as st
from core.utils import make_key

def render_article_list(grouped: dict):
    title_to_cats = {}
    for cat, arts in grouped.items():
        for a in arts:
            title_to_cats.setdefault(a["title"], set()).add(cat)

    selected = set()
    for cat in sorted(grouped.keys()):
        with st.expander(f"**{cat}** ({len(grouped[cat])} Artikel)", expanded=True):
            for art in grouped[cat]:
                title = art["title"]
                key = make_key(cat, title)
                col1, col2, col3 = st.columns([5, 2, 2])
                with col1:
                    if st.checkbox(title, key=key):
                        selected.add(title)
                with col2:
                    others = sorted(title_to_cats[title] - {cat})
                    if others:
                        st.caption(f"auch in: {', '.join(others)}")
                with col3:
                    info = " | ".join(filter(None, [", ".join(art["tags"]), ", ".join(art["orte"])]))
                    if info:
                        st.caption(info)
    return selected, len(title_to_cats)