# core/parser.py
import re
import difflib
from typing import List, Dict, Tuple
from .utils import make_key

ALLOWED_CATEGORIES = [
    "Politik", "Gesellschaft", "Bildung & Erziehung", "Wissenschaft & Forschung",
    "Umwelt & Klima", "Energie & Ressourcen", "Wirtschaft", "Gesundheit",
    "Kultur & Kunst", "Medien & Öffentlichkeit", "Digitales & Technik",
    "Mobilität & Verkehr", "Engagement & Protest", "Recht & Justiz"
]

def split_commas_preserve(text: str) -> List[str]:
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return [p.strip() for p in text.split(",") if p.strip()]

def parse_comment_block(comment: str) -> Tuple[List[str], List[str], List[str]]:
    cats, tags, orte = [], [], []
    for line in [l.strip() for l in comment.splitlines() if l.strip()]:
        if line.lower().startswith("categories:"):
            cats.extend(split_commas_preserve(line.split(":", 1)[1]))
        elif line.lower().startswith("tags:"):
            parts = split_commas_preserve(line.split(":", 1)[1])
            clean = []
            for p in parts:
                if p.lower().startswith("orte:"):
                    orte.extend(split_commas_preserve(p.split(":", 1)[1]))
                else:
                    clean.append(p)
            tags.extend(clean)
        elif line.lower().startswith("orte:"):
            orte.extend(split_commas_preserve(line.split(":", 1)[1]))
    return cats, tags, orte

def parse_articles_from_text(text: str) -> List[Dict]:
    blocks = re.split(r"\s*\n?<!--split-->\s*\n?", text)
    articles = []
    for block in blocks:
        stripped = block.strip()
        if len(stripped) < 5:
            continue
        t_m = re.search(r"######\s*(.+?)\n", stripped)
        if not t_m:
            continue
        title = t_m.group(1).strip()
        com_m = re.search(r"<!--(.*?)-->", stripped, re.DOTALL)
        comment = com_m.group(1).strip() if com_m else ""
        cats, tags, orte = parse_comment_block(comment)
        articles.append({
            "title": title, "categories": cats, "tags": tags, "orte": orte,
            "raw": stripped + "\n"
        })
    return articles

def validate_and_correct_categories(articles: List[Dict]) -> str:
    all_cats = {c.strip() for a in articles for c in a["categories"] if c != "Unkategorisiert"}
    invalid = [c for c in all_cats if c not in ALLOWED_CATEGORIES]
    if not invalid:
        return ""
    corrections = []
    for inv in invalid:
        match = difflib.get_close_matches(inv, ALLOWED_CATEGORIES, n=1, cutoff=0.8)
        if match:
            corr = match[0]
            corrections.append((inv, corr))
            for a in articles:
                a["categories"] = [corr if c.strip() == inv else c for c in a["categories"]]
        else:
            raise ValueError(f"Ungültige Kategorie: {inv}")
    return " | ".join([f"{old} to {new}" for old, new in corrections])