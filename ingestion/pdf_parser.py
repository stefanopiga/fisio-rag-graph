import fitz  # PyMuPDF
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

def _clean_page_text(text: str) -> str:
    """
    Pulisce il testo di una pagina rimuovendo i numeri di pagina e altri artefatti comuni.
    """
    # Rimuove pattern come "Pagina X di Y" o "Page X" (case-insensitive)
    text = re.sub(r'pagina\s+\d+\s*(di\s*\d+)?', '', text, flags=re.IGNORECASE)
    
    # Rimuove pattern come "X / Y" che sono spesso usati per i numeri di pagina
    cleaned_lines = []
    for line in text.split('\n'):
        # Rimuove le linee che sembrano essere solo un numero di pagina
        # (es. una linea che contiene solo un numero, eventualmente con spazi)
        if re.fullmatch(r'\s*\d+\s*', line):
            continue
        
        # Rimuove i numeri di pagina alla fine di una linea
        line = re.sub(r'\s+\d+\s*$', '', line)
        
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines)

def extract_text_from_pdf(file_path: Path) -> str:
    """
    Estrae il testo completo da un file PDF, pulendolo dai numeri di pagina.

    Args:
        file_path: Il percorso del file PDF.

    Returns:
        Una stringa contenente il testo estratto e pulito dal PDF.
        Restituisce una stringa vuota se il file non può essere elaborato.
    """
    try:
        logger.info(f"Inizio estrazione testo dal PDF: {file_path}")
        doc = fitz.open(file_path)
        full_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            cleaned_text = _clean_page_text(page_text)
            full_text += cleaned_text + "\n"  # Aggiunge un newline per separare le pagine
        
        logger.info(f"Estrazione completata per {file_path}. Estratti {len(full_text)} caratteri puliti.")
        return full_text
    except Exception as e:
        logger.error(f"Errore durante l'estrazione del testo dal PDF {file_path}: {e}")
        return "" 