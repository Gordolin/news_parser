# core/output_processor.py
import re
from typing import List

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
def step1_remove_single_empty_line_after_text(text: str) -> str:
    """
    Schritt 1: Nach jeder Textzeile (nicht-leer) eine Leerzeile entfernen, wenn vorhanden.
    Wenn mehr als eine Leerzeile folgt, behalte die anderen (z.B. Text\n\n\n -> Text\n\n).
    """
    lines = text.splitlines(keepends=True)  # Erhält \n am Ende jeder Zeile
    result_lines: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip():  # Textzeile (nicht leer)
            result_lines.append(line)
            i += 1
            # Zähle folgende Leerzeilen
            empty_count = 0
            while i < len(lines) and not lines[i].strip():
                empty_count += 1
                i += 1
            # Füge (empty_count - 1) Leerzeilen hinzu (entferne eine, wenn >=1)
            if empty_count >= 1:
                result_lines.extend(lines[i - empty_count : i - 1])  # Alle außer der letzten
            # i ist schon auf nächster Textzeile
        else:
            # Reine Leerzeile: Unverändert anhängen
            result_lines.append(line)
            i += 1
    
    return ''.join(result_lines)

def step2_ensure_empty_lines_around_headings(text: str) -> str:
    """
    Schritt 2: Stelle sicher, dass vor und nach jeder Überschrift (###### Titel) mindestens eine Leerzeile steht.
    - Vor: Füge \n hinzu, nur wenn vorherige Zeile nicht leer (vermeidet Duplizierung nach Split).
    - Nach: Füge genau eine \n hinzu (ergibt Leerzeile nach Header).
    """
    lines = text.splitlines(keepends=True)
    result_lines = []
    for i, line in enumerate(lines):
        if line.strip().startswith('######'):
            # Vor Header: Füge \n hinzu, nur wenn vorherige Zeile nicht leer
            if i > 0 and lines[i-1].strip():
                result_lines.append('\n')
            result_lines.append(line)
            # Nach Header: Immer \n hinzufügen (macht genau eine Leerzeile)
            result_lines.append('\n')
        else:
            result_lines.append(line)
    return ''.join(result_lines)

def step3_ensure_empty_lines_around_comments(text: str) -> str:
    """
    Schritt 3: Stelle sicher, dass vor jedem Kommentar-Beginn (<!-- am Zeilenanfang) und nach jedem Ende (--> am Zeilenanfang) mindestens eine Leerzeile steht.
    - Vor Beginn: Füge \n hinzu, nur wenn vorherige Zeile nicht leer.
    - Nach Ende: Füge \n hinzu, nur wenn nächste Zeile nicht leer (für multiline-Kommentare).
    """
    lines = text.splitlines(keepends=True)
    result_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Vor Kommentar-Beginn: Wenn Zeile mit <!-- startet (nach lstrip, für Indent)
        if line.lstrip().startswith('<!--'):
            if i > 0 and lines[i-1].strip():
                result_lines.append('\n')
            result_lines.append(line)
            i += 1
        # Nach Kommentar-Ende: Wenn Zeile --> enthält, und nächste nicht leer, \n hinzufügen
        elif '-->' in line:
            result_lines.append(line)
            i += 1
            if i < len(lines) and lines[i].strip():
                result_lines.append('\n')
        else:
            result_lines.append(line)
            i += 1
    return ''.join(result_lines)

def step4_add_frontmatter(text: str, title: str, year: int, month: int) -> str:
    """
    Schritt 4: Extrahiere Cats/Tags/Orte aus Kommentar-Blöcken und hänge Frontmatter vorne an.
    - Sammle alle einzigartigen aus <!-- ... -->.
    - Baue YAML mit build_frontmatter und füge vorne an.
    """
    # Extrahiere Cats/Tags/Orte aus allen Kommentar-Blöcken
    all_cats = set()
    all_tags = set()
    all_orte = set()
    
    # Regex für Kommentar-Inhalt (multiline)
    comment_matches = re.findall(r'<!--\s*(.*?)\s*-->', text, re.DOTALL)
    for comment in comment_matches:
        # Parse lines in comment
        for line in comment.splitlines():
            line = line.strip()
            if line.lower().startswith('categories:'):
                cats = [c.strip() for c in line.split(':', 1)[1].split(',') if c.strip()]
                all_cats.update(cats)
            elif line.lower().startswith('tags:'):
                tags = [t.strip() for t in line.split(':', 1)[1].split(',') if t.strip()]
                all_tags.update(tags)
            elif line.lower().startswith('orte:'):
                orte = [o.strip() for o in line.split(':', 1)[1].split(',') if o.strip()]
                all_orte.update(orte)
    
    # Baue Frontmatter
    fm = build_frontmatter(title, year, month, list(all_cats), list(all_tags), list(all_orte))
    
    # Füge vorne an (mit \n\n für Abstand)
    return fm + "\n\n" + text

def step5_remove_date_after_heading(text: str) -> str:
    """
    Entfernt '(*Date*)' wenn es direkt am Ende einer '######' Überschrift steht.
    Beispiel: '###### Nachricht 3 (*Date*)' -> '###### Nachricht 3'
    (case-insensitive, mehrere Whitespace-Varianten unterstützt)
    """
    return re.sub(
        r'(?im)^(######\s*.*?)\s*\(\*date\*\)\s*(?:\r?\n|$)',
        r'\1\n',
        text
    )

def step6_remove_placeholder_link_shortcodes(text: str) -> str:
    """
    Entfernt exakt Zeilen, die nur '{{< my_link url="Link" >}}' (mit beliebigen Spaces/Tabs) enthalten.
    - Löscht die komplette Zeile inkl. Newline.
    - Belässt Zeilen, in denen der Token nur Teil der Zeile ist.
    """
    return re.sub(
        r'(?m)^[ \t]*\{\{<\s*my_link\s+url="Link"\s*>\}\}\s*(?:\r?\n|$)',
        '',
        text
    )

def step7_reduce_multiple_empty_lines(text: str) -> str:
    """
    Letzter Schritt: Prüfe auf mehr als eine Leerzeile hintereinander (\n\n\n+), und ersetze durch genau eine Leerzeile (\n\n).
    - Erhalten Absätze, entferne überflüssige Mehrfach-Leerzeilen.
    """
    # Regex: 3+ \n ersetzen durch 2 \n (eine Leerzeile)
    original_len = len(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    matches = original_len - len(text)
    print(f"DEBUG Step7: {matches} Zeichen Mehrfach-Leerzeilen reduziert (0 = keine)")  # Entferne später
    return text