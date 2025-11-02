# app.py
import streamlit as st
import os
import sys
import glob
import time
import logging  # NEU: Für Konsolen-Logs

# --- Pfad ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- Logging für Konsole ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Imports ---
from gui.state import init_state
from gui.layout import render_article_list
from core.parser import parse_articles_from_text, validate_and_correct_categories
from core.processor import (
    create_working_copy, extract_year_month, generate_output, update_working_copy
)
from core.output_processor import(
    step1_remove_single_empty_line_after_text,
    step2_ensure_empty_lines_around_headings,
    step3_ensure_empty_lines_around_comments,
    step4_add_frontmatter,
    step5_remove_date_after_heading,
    step6_remove_placeholder_link_shortcodes,
    step7_reduce_multiple_empty_lines
)
from core.utils import OUTPUT_DIR

# --- Init ---
st.set_page_config(page_title="News Parser", layout="wide")
init_state()
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Hilfsfunktionen ---
def reset_session():
    """Lösche Working Copies + Session-Keys (außer src_text/file_name)"""
    for f in glob.glob(os.path.join(OUTPUT_DIR, "working_*.md")):
        try:
            os.remove(f)
            logger.info(f"Gelöscht: Working Copy {f}")
        except Exception as e:
            logger.warning(f"Konnte Working Copy {f} nicht löschen: {e}")
    keys = ["working_path", "grouped", "corrections_str", "year", "month", "last_output"]
    for k in keys:
        st.session_state.pop(k, None)

def get_latest_output():
    """Nur für interne Logik – nicht für UI!"""
    files = [
        f for f in glob.glob(os.path.join(OUTPUT_DIR, "*.md"))
        if not os.path.basename(f).startswith("working_")
    ]
    return max(files, key=os.path.getctime) if files else None

# --- UI: Upload ---
uploaded = st.file_uploader("Markdown-Datei hochladen", type="md", key="uploader")

# --- Datei laden (FIX: Prüfe Dateinamen statt Inhalt) ---
if uploaded is not None:
    current_filename = st.session_state.get("file_name", "")
    if current_filename != uploaded.name:  # FIX: Nur bei neuem Dateinamen
        with st.spinner("Lade und verarbeite neue Datei..."):
            reset_session()  # Working + Session zurücksetzen
            st.session_state.src_text = uploaded.getvalue().decode("utf-8")
            st.session_state.file_name = uploaded.name

            try:
                year, month = extract_year_month(st.session_state.src_text)
                wp = create_working_copy(st.session_state.src_text, st.session_state.file_name, OUTPUT_DIR)
                articles = parse_articles_from_text(open(wp, "r", encoding="utf-8").read())  # Löst Debug-Files aus
                logger.info(f"PARSING ABGESCHLOSSEN: {len(articles)} Artikel, siehe debug/ Ordner.")
                corr = validate_and_correct_categories(articles)

                grouped = {}
                for a in articles:
                    for c in (a["categories"] or ["Unkategorisiert"]):
                        grouped.setdefault(c, []).append(a)

                st.session_state.update({
                    "working_path": wp,
                    "grouped": grouped,
                    "corrections_str": corr,
                    "year": year,
                    "month": month,
                    "last_output": None  # Zurücksetzen!
                })
            except Exception as e:
                st.error(f"Fehler: {e}")
                logger.error(f"Laden fehlgeschlagen: {e}")
                st.stop()

# --- Datei-Info (nur Session-basiert!) ---
if st.session_state.file_name or st.session_state.working_path:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption(f"Eingelesen: {st.session_state.file_name or '—'}")
    with c2:
        wc = os.path.basename(st.session_state.working_path) if st.session_state.working_path else "—"
        st.caption(f"Working Copy: {wc}")
    with c3:
        last_out = st.session_state.get("last_output")
        st.caption(f"Letzte Ausgabe: {last_out or '—'}")

# --- Haupt-UI ---
if st.session_state.grouped:
    st.subheader("Artikel auswählen")
    selected_titles, unique_count = render_article_list(st.session_state.grouped)
    st.info(f"Gesamt: {unique_count} | Ausgewählt: {len(selected_titles)}")
    if st.session_state.corrections_str:
        st.success(f"Korrigiert: {st.session_state.corrections_str}")

    with st.expander("Ausgabe-Einstellungen", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_title = st.text_input("Titel", "Kurznachrichten", key="out_title")
        with c2:
            year = st.number_input("Jahr", value=st.session_state.year, min_value=2000, key="year_in")
        with c3:
            month = st.number_input("Monat", value=st.session_state.month, min_value=1, max_value=12, key="month_in")

    if st.button("Output erzeugen", type="primary"):
        if not selected_titles:
            st.warning("Wähle Artikel aus.")
        else:
            with st.spinner("Generiere..."):
                try:
                    current_articles = parse_articles_from_text(open(st.session_state.working_path, "r", encoding="utf-8").read())
                    selected = [a for a in current_articles if a["title"] in selected_titles]
                    out_path = generate_output(selected, out_title, int(year), int(month), OUTPUT_DIR)  # Params bleiben, aber ignoriert im Raw
                    logger.info(f"Output-Datei erstellt: {os.path.basename(out_path)}")
                    update_working_copy(st.session_state.working_path, selected_titles)

                    ##########################
                    # Parsen des Output Files
                    ##########################

                    # Post-Processing: Schritte 1 + 2 + 3 auf dem Output-File
                    with open(out_path, "r", encoding="utf-8") as f:
                        raw_output = f.read()

                    logger.info(f"Raw Output Länge vor Processing: {len(raw_output)}")

                    # Schritt 1: Frontmatter hinzufügen (extrahiert aus raw)
                    processed_step1 = step4_add_frontmatter(raw_output, out_title, int(year), int(month))
                    logger.info(f"Nach Schritt 4 Länge: {len(processed_step1)} (Frontmatter hinzugefügt)")

                    # Schritt 2: Leerzeilen nach Textzeilen reduzieren
                    processed_step2 = step1_remove_single_empty_line_after_text(processed_step1)
                    logger.info(f"Nach Schritt 1 Länge: {len(processed_step2)}")

                    # Schritt 3: Leerzeilen um Überschriften sicherstellen
                    processed_step3 = step2_ensure_empty_lines_around_headings(processed_step2)
                    logger.info(f"Nach Schritt 2 Länge: {len(processed_step2)}")

                    # Schritt 4: Leerzeilen um Kommentare
                    processed_step4 = step3_ensure_empty_lines_around_comments(processed_step3)
                    logger.info(f"Nach Schritt 3 Länge: {len(processed_step3)}")

                    # NEU: Schritt 5: Date-Zusatz entfernen
                    processed_step5 = step5_remove_date_after_heading(processed_step4)
                    logger.info(f"Nach Schritt 5 Länge: {len(processed_step5)}")

                    # Schritt 6: Date-Zusatz entfernen
                    processed_step6 = step6_remove_placeholder_link_shortcodes(processed_step5)
                    logger.info(f"Nach Schritt 6 Länge: {len(processed_step6)}")

                    # Schritt 7: Mehrfach-Leerzeilen reduzieren
                    processed_step7 = step7_reduce_multiple_empty_lines(processed_step6)
                    logger.info(f"Nach Schritt 7 Länge: {len(processed_step7)} (Mehrfach-Leerzeilen reduziert)")

                    # Final: Überschreibe Output
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(processed_step7)

                    logger.info(f"Output post-prozessiert (Schritte 4+1+2+3): {os.path.basename(out_path)}")

                    st.session_state.last_output = os.path.basename(out_path)

                    time.sleep(1.2)

                    # UI aktualisieren (Parsing nur für UI)
                    new_articles = parse_articles_from_text(open(st.session_state.working_path, "r", encoding="utf-8").read())
                    corr = validate_and_correct_categories(new_articles)

                    new_grouped = {}
                    for a in new_articles:
                        for c in (a["categories"] or ["Unkategorisiert"]):
                            new_grouped.setdefault(c, []).append(a)
                    st.session_state.update({
                        "grouped": new_grouped,
                        "corrections_str": corr
                    })
                    st.rerun()

                except Exception as e:
                    st.error(f"Fehler: {e}")
                    logger.error(f"Generieren fehlgeschlagen: {e}")
else:
    st.info("Lade eine Markdown-Datei hoch, um zu beginnen.")

# --- NEU: Progress Bar unten (fixed) ---
# Zeigt 100% nach Generierung, sonst 0%
if st.session_state.get("grouped"):
    progress_bar = st.progress(1.0, text="Bereit")  # Voll nach Laden
else:
    st.progress(0.0, text="Warte auf Datei...")