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

# core/output_processor.py
import re
from typing import List

# ... (step1 und step2 unverändert)

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

# Beispiel-Test (entferne nach Implementierung oder teste lokal)
if __name__ == "__main__":
    example_text = """###### Zalando
<!--categories: Wirtschaft
tags: Migration
-->
{{< my_media src="202510-10.avif" / >}}Direkt nach Kommentar-Ende

Text mit Absatz

###### Nachricht 3
Hier Kommentar direkt: <!--tags: Test-->
Satz direkt danach ohne Leerzeile
"""
    step1 = step1_remove_single_empty_line_after_text(example_text)
    step2 = step2_ensure_empty_lines_around_headings(step1)
    step3 = step3_ensure_empty_lines_around_comments(step2)
    print("Nach Schritt 1+2+3 (Leerzeile nach --> hinzugefügt):\n", repr(step3))