# core/processor.py
import os
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Set
import logging

from .parser import parse_articles_from_text  # Nutzen für verbleibende raw
from .utils import build_frontmatter, slugify  # Nicht für Raw-Output

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def create_working_copy(src_text: str, file_name: str, base_dir: str) -> str:
    """RAW: Entferne Frontmatter + alles vor erstem ###### (für 'nur Artikel'), behalte Whitespace danach 1:1."""
    # Entferne Frontmatter
    cleaned = re.sub(r'^---\n(.*?)\n---\n', '', src_text, flags=re.M | re.S)
    # Cut vor erstem ###### (behält \n davor, falls vorhanden)
    first_heading_match = re.search(r'######', cleaned)
    if first_heading_match:
        cleaned = cleaned[first_heading_match.start():]
    # KEIN Strip, KEINE anderen Änderungen – roh!
    
    hash_part = hashlib.md5(file_name.encode()).hexdigest()[:8]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(base_dir, f"working_{hash_part}_{ts}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    return path

def extract_year_month(text: str) -> tuple[int, int]:
    """Unverändert."""
    fm = re.search(r'^---\n(.*?)\n---', text, flags=re.M | re.S)
    if not fm:
        return 2025, 10
    path_match = re.search(r'media:\s*path:\s*"[^"]*/(\d{4})/(\d{2})/"', fm.group(1))
    return (int(path_match.group(1)), int(path_match.group(2))) if path_match else (2025, 10)

def generate_output(selected: List[Dict], title: str, year: int, month: int, base_dir: str) -> str:
    """RAW: Concat raw-Blöcke aus selected mit <!--split--> dazwischen – KEIN FM, KEINE Änderung!"""
    if not selected:
        return None
    
    # Sammle raw-Blöcke
    raw_blocks = [a["raw"] for a in selected]
    
    # Join mit Split-Marker für Trennung (inkl. Leerzeilen)
    raw_content = "\n\n<!--split-->\n\n".join(raw_blocks)
    
    slug = slugify(title)
    base_path = os.path.join(base_dir, f"{slug}.md")
    
    # FIX: Counter mit führenden Nullen (z.B. _01, _02) für Sortierung, wenn existiert
    counter = 1
    while os.path.exists(base_path):
        counter += 1
        formatted_counter = f"{counter:02d}"  # Führende Null: 01, 02, ...
        base_path = os.path.join(base_dir, f"{slug}_{formatted_counter}.md")
    
    path = base_path
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw_content)
    logger.info(f"Output-Datei erstellt (Counter: {formatted_counter if counter > 1 else 'kein'}): {os.path.basename(path)}")
    return path

# core/processor.py
# ... (create_working_copy, extract_year_month, generate_output unverändert)

def update_working_copy(working_path: str, selected_titles: Set[str]) -> None:
    """PRAGMATISCH: Parse WC, filter verbleibende, concat raw mit \n\n dazwischen."""
    with open(working_path, "r", encoding="utf-8") as f:
        wc_text = f.read()
    
    articles = parse_articles_from_text(wc_text)
    
    remaining = [a for a in articles if a["title"] not in selected_titles]
    
    if not remaining:
        open(working_path, "w").close()  # Leere WC
        return
    
    # FIX: Concat mit \n\n zwischen Blöcken für Leerzeile
    raw_blocks = [a["raw"] for a in remaining]
    new_content = "\n\n<!--split-->\n\n".join(raw_blocks)
    
    with open(working_path, "w", encoding="utf-8") as f:
        f.write(new_content)
