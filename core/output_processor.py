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
