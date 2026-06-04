from pathlib import Path
from bs4 import BeautifulSoup

def load_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in [".md", ".txt"]:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix in [".htm", ".html"]:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "lxml")

        # Quita ruido
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # Limpieza básica
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]  # remove empty
        return "\n".join(lines)

    # fallback
    return path.read_text(encoding="utf-8", errors="ignore")
