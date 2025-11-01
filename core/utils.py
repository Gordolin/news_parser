# core/utils.py
import os
import re
import hashlib
from typing import List

def get_base_dir() -> str:
    return os.environ.get("NEWS_PARSER_BASE_DIR", r"C:\users\hager\tmp\parse_news")

# NEU: Zentrale Konstante für OUTPUT_DIR (basierend auf get_base_dir)
OUTPUT_DIR = get_base_dir()

# NEU: Debug-Ordner (wird in parser.py verwendet)
DEBUG_DIR = os.path.join(OUTPUT_DIR, "debug")
os.makedirs(DEBUG_DIR, exist_ok=True)  # Erstelle bei Import

def slugify(title: str) -> str:
    s = re.sub(r"\s+", "_", title.strip().lower())
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s[:80] or "output"

def make_key(category: str, title: str) -> str:
    return hashlib.md5(f"{category}::{title}".encode("utf-8")).hexdigest()

def build_frontmatter(title: str, year: int, month: int, categories: List[str], tags: List[str], orte: List[str]) -> str:
    date_str = f"{year}-{month:02d}-20T12:23:04+02:00"
    cats = ", ".join(sorted(set(c for c in categories if c)))
    tags_s = ", ".join(sorted(set(t for t in tags if t)))
    orte_s = ", ".join(sorted(set(o for o in orte if o)))
    return f"""---
title: "{title}"
date: {date_str}
series: [Blog, Kurznachrichten]
categories: [{cats}]
tags: [{tags_s}]
orte: [{orte_s}]
media:
    path: "http://kastl/blog-bf/news/{year}/{month:02d}/"
layout: card-columns
---
"""