# core/output_processor.py
import re
from typing import List

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