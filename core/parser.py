# core/parser.py
import os
import json
import re
import difflib
from typing import List, Dict, Tuple

# FIX: Importiere OUTPUT_DIR / DEBUG_DIR aus utils (zentral und sauber)
from .utils import OUTPUT_DIR, DEBUG_DIR  # DEBUG_DIR wird hier erstellt

ALLOWED_CATEGORIES = [
    "Politik", "Gesellschaft", "Bildung & Erziehung", "Wissenschaft & Forschung",
    "Umwelt & Klima", "Energie & Ressourcen", "Wirtschaft", "Gesundheit",
    "Kultur & Kunst", "Medien & Öffentlichkeit", "Digitales & Technik",
    "Mobilität & Verkehr", "Engagement & Protest", "Recht & Justiz"
]

def load_and_strip_frontmatter(text: str) -> str:
    """Schritt 1: Entferne Frontmatter, schreibe Debug-File."""
    cleaned = re.sub(r'^---\n(.*?)\n---\n', '', text, flags=re.M | re.S)
    debug_path = os.path.join(DEBUG_DIR, "debug_step1_no_frontmatter.txt")
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    print(f"Debug: Step 1 geschrieben nach {debug_path}")  # Oder logger
    return cleaned

def split_into_raw_blocks(text: str) -> List[str]:
    """FIX: Split auf <!--split-->, Fallback auf ###### wenn nur 1 Block."""
    blocks = re.split(r"\s*\n?<!--split-->\s*\n?", text)
    blocks = [b.strip() for b in blocks if len(b.strip()) >= 5]  # Filter leere
    
    # Fallback: Wenn nur 1 Block, split auf \n###### (rekonstruiere mit Header)
    if len(blocks) == 1:
        sub_parts = re.split(r'\n######\s', text)  # Split auf Header
        if len(sub_parts) > 1:
            blocks = [f"###### {sub_parts[i].strip()}" for i in range(1, len(sub_parts))]  # Jeder Part als Block
    
    return blocks

def extract_title_from_block(block: str) -> Tuple[str, bool]:
    """Hilfsfunktion: Extrahiere Titel aus Block."""
    match = re.search(r"######\s*(.+?)\n", block)
    if match:
        return match.group(1).strip(), True
    return "", False

def extract_comment_from_block(block: str) -> str:
    """Hilfsfunktion: Extrahiere Kommentar aus Block."""
    match = re.search(r"<!--(.*?)-->", block, re.DOTALL)
    return match.group(1).strip() if match else ""

def parse_comment_block(comment: str) -> Tuple[List[str], List[str], List[str]]:
    """Unverändert (Stub für Kategorien/Tags)."""
    cats, tags, orte = [], [], []
    for line in [l.strip() for l in comment.splitlines() if l.strip()]:
        if line.lower().startswith("categories:"):
            cats = [p.strip() for p in line.split(":", 1)[1].split(",") if p.strip()]
        elif line.lower().startswith("tags:"):
            tags = [p.strip() for p in line.split(":", 1)[1].split(",") if p.strip()]
        elif line.lower().startswith("orte:"):
            orte = [p.strip() for p in line.split(":", 1)[1].split(",") if p.strip()]
    return cats, tags, orte

def extract_single_article(block: str, block_index: int) -> Dict:
    """Hilfsfunktion: Extrahiere einen Artikel aus Block, mit per-Artikel-Debug."""
    title, has_title = extract_title_from_block(block)
    if not has_title:
        raise ValueError(f"Kein Titel in Block {block_index}")
    comment = extract_comment_from_block(block)
    cats, tags, orte = parse_comment_block(comment)
    article = {
        "title": title, "categories": cats, "tags": tags, "orte": orte,
        "raw": block + "\n"
    }
    # Debug pro Artikel
    debug_path = os.path.join(DEBUG_DIR, f"debug_step3_article_{block_index}.json")
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)
    print(f"Debug: Step 3 Artikel {block_index} geschrieben nach {debug_path}")
    return article

def extract_articles_from_blocks(blocks: List[str]) -> List[Dict]:
    """Schritt 3: Extrahiere Artikel aus Blöcken."""
    articles = []
    for i, block in enumerate(blocks):
        try:
            article = extract_single_article(block, i)
            articles.append(article)
        except ValueError as e:
            print(f"Warnung: Überspringe Block {i}: {e}")
    return articles

# NEU: Interne Funktion für detaillierte Validierung (mit Debug)
def validate_articles(articles: List[Dict]) -> Tuple[List[Dict], str]:
    """Schritt 4: Validiere/Korrigiere Kategorien, schreibe Debug-JSON."""
    all_cats = {c.strip() for a in articles for c in a["categories"] if c != "Unkategorisiert"}
    invalid = [c for c in all_cats if c not in ALLOWED_CATEGORIES]
    corrections = []
    if invalid:
        for inv in invalid:
            match = difflib.get_close_matches(inv, ALLOWED_CATEGORIES, n=1, cutoff=0.8)
            if match:
                corr = match[0]
                corrections.append((inv, corr))
                for a in articles:
                    a["categories"] = [corr if c.strip() == inv else c for c in a["categories"]]
            else:
                raise ValueError(f"Ungültige Kategorie: {inv}")
    # Debug: Vollständige validated Articles
    debug_path = os.path.join(DEBUG_DIR, "debug_step4_validated.json")
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Debug: Step 4 geschrieben nach {debug_path}")
    return articles, " | ".join([f"{old} to {new}" for old, new in corrections])

# FIX: Wrapper-Funktion für Kompatibilität (returnt nur den String, modifiziert Articles in-place)
def validate_and_correct_categories(articles: List[Dict]) -> str:
    """Kompatible API: Validiert und korrigiert (modifiziert Articles), returnt Korrektur-String."""
    _, corrections_str = validate_articles(articles)  # Ruft interne Funktion auf (inkl. Debug)
    return corrections_str

def parse_articles_from_text(text: str) -> List[Dict]:
    """FIX: Nutzt neuen split_into_raw_blocks für korrekte Trennung."""
    articles = []
    blocks = split_into_raw_blocks(text)
    for block in blocks:
        t_m = re.search(r"######\s*(.+?)\n", block)
        if not t_m:
            continue
        title = t_m.group(1).strip()
        com_m = re.search(r"<!--(.*?)-->", block, re.DOTALL)
        comment = com_m.group(1).strip() if com_m else ""
        cats, tags, orte = parse_comment_block(comment)
        articles.append({
            "title": title, "categories": cats, "tags": tags, "orte": orte,
            "raw": block + "\n"  # Vollständiger Block
        })
    return articles