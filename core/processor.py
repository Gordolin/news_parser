# core/processor.py
import os
import re
import datetime
import hashlib
from typing import List, Dict, Tuple
from .parser import parse_articles_from_text
from .utils import build_frontmatter, slugify

def create_working_copy(src_text: str, file_name: str, base_dir: str) -> str:
    hash_part = hashlib.md5(file_name.encode()).hexdigest()[:8]
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(base_dir, f"working_{hash_part}_{ts}.md")

    cleaned = re.sub(r'^---\n(.*?)\n---\n', '', src_text, flags=re.M | re.S)
    first_heading = re.search(r'\n?######\s', cleaned)
    if first_heading:
        cleaned = cleaned[first_heading.start():]
    cleaned = re.sub(r'^\n+', '', cleaned)
    cleaned = re.sub(r'\n+$', '\n', cleaned)

    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    return path

def extract_year_month(text: str) -> Tuple[int, int]:
    fm = re.search(r'^---\n(.*?)\n---', text, flags=re.M | re.S)
    if not fm:
        return 2025, 10
    path = re.search(r'media:\s*path:\s*"[^"]*/(\d{4})/(\d{2})/"', fm.group(1))
    return (int(path.group(1)), int(path.group(2))) if path else (2025, 10)

def post_process_content(content: str) -> str:
    content = re.sub(r'\n{3,}', '\n\n', content)
    blocks = re.split(r'\n######', content)
    if len(blocks) > 1:
        first = blocks[0].rstrip() + ("\n\n" if not blocks[0].endswith('\n\n') else "")
        processed = first + "".join(f"\n\n<!--split-->\n\n######{b}" for b in blocks[1:])
    else:
        processed = content.rstrip() + '\n\n'
    content = re.sub(r'-->(?!\s*<!--split-->\s*)', '-->\n\n', processed)
    content = re.sub(r'<!--split-->', '\n<!--split-->\n', content)
    return re.sub(r'\n{3,}', '\n\n', content).rstrip() + '\n'

def generate_output(selected: List[Dict], title: str, year: int, month: int, base_dir: str) -> str:
    all_cats = [c for a in selected for c in a["categories"]]
    all_tags = [t for a in selected for t in a["tags"]]
    all_orte = [o for a in selected for o in a["orte"]]
    fm = build_frontmatter(title, year, month, all_cats, all_tags, all_orte)
    raw = "".join(a["raw"] for a in selected)
    content = fm + "\n" + post_process_content(raw)

    slug = slugify(title)
    counter = 1
    while os.path.exists(os.path.join(base_dir, f"{slug}_{counter}.md")):
        counter += 1
    path = os.path.join(base_dir, f"{slug}_{counter}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def update_working_copy(working_path: str, selected_titles: set):
    articles = parse_articles_from_text(open(working_path, "r", encoding="utf-8").read())
    remaining = [a for a in articles if a["title"] not in selected_titles]
    if not remaining:
        open(working_path, "w").close()
        return
    raw = "".join(a["raw"] for a in remaining)
    with open(working_path, "w", encoding="utf-8") as f:
        f.write(post_process_content(raw))