import requests
import tempfile
import os
import pdfplumber


def extract_text_from_url(pdf_url: str) -> list:
    response = requests.get(pdf_url, timeout=60)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    try:
        paragraphs = []
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                current = []
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        if current:
                            paragraphs.append(' '.join(current))
                            current = []
                    else:
                        current.append(stripped)
                if current:
                    paragraphs.append(' '.join(current))

        merged = []
        for p in paragraphs:
            if len(p) < 40 and merged:
                merged[-1] += ' ' + p
            elif len(p) < 40:
                merged.append(p)
            else:
                merged.append(p)

        return merged if merged else ["[PDF text extraction failed]"]
    finally:
        os.unlink(tmp_path)
