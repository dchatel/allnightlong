"""Lecture des en-têtes FITS du Seestar (sans bibliothèque externe).

Utilisé par le rapport (« Depuis un FITS… ») et par l'outil de reprise des données.
Seul l'en-tête est lu : quelques kilo-octets, même pour une capture de plusieurs gigaoctets.
"""
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

FITS_SUFFIXES = (".fit", ".fits", ".fts")


def fits_header(path: Path) -> dict:
    """Mots-clés de l'en-tête FITS (blocs de 2880 octets, cartes de 80 caractères)."""
    cards = {}
    with open(path, "rb") as f:
        while True:
            block = f.read(2880)
            if len(block) < 2880:
                return cards
            for i in range(0, 2880, 80):
                card = block[i:i + 80].decode("ascii", "replace")
                key = card[:8].strip()
                if key == "END":
                    return cards
                if card[8:10] == "= ":
                    cards[key] = card[10:].split(" /")[0].strip().strip("'").strip()


def parse_fits_date(value: str) -> datetime:
    return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")


def number(value: Optional[str]) -> Optional[float]:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def light_frames(sub_dir: Path) -> list:
    """Poses « Light_… » d'un dossier de capture, dans l'ordre de prise de vue (horodatage du nom)."""
    return sorted(
        (p for p in sub_dir.rglob("Light*") if p.suffix.lower() in FITS_SUFFIXES),
        key=lambda p: p.stem.rsplit("_", 1)[-1],
    )


def capture_summary(path: Path) -> dict:
    """Ce qu'un FITS du Seestar dit de sa capture.

    Pour un FITS empilé (« Stacked_… »), DATE-OBS est l'heure de la dernière pose : le début exact vient de
    la première pose du dossier « <cible>_sub » voisin quand il existe, sinon il est estimé à partir du
    nombre de poses empilées. Pour une pose isolée, début et fin viennent du dossier qui la contient.
    """
    header = fits_header(path)
    if "DATE-OBS" not in header:
        raise ValueError("Ce fichier ne contient pas de date d'observation (DATE-OBS).")
    exposure = number(header.get("EXPTIME")) or number(header.get("EXPOSURE")) or 0.0
    stacked = int(number(header.get("STACKCNT")) or 0)
    observed = parse_fits_date(header["DATE-OBS"])

    lights = []
    if path.name.startswith("Stacked"):
        sub_dir = path.parent.with_name(path.parent.name + "_sub")
        lights = light_frames(sub_dir) if sub_dir.is_dir() else []
    elif path.name.startswith("Light"):
        lights = light_frames(path.parent)

    if lights:
        first, last = fits_header(lights[0]), fits_header(lights[-1])
        start = parse_fits_date(first["DATE-OBS"])
        end = parse_fits_date(last["DATE-OBS"]) + timedelta(seconds=exposure)
        exact = True
    else:
        end = observed + timedelta(seconds=exposure)
        start = end - timedelta(seconds=exposure * max(stacked, 1))
        exact = False

    # Aperçu JPEG enregistré par le Seestar à côté du FITS empilé
    preview = path.with_suffix(".jpg")
    return {
        "start": f"{start:%Y-%m-%d %H:%M}",
        "end": f"{end:%Y-%m-%d %H:%M}",
        "startExact": exact,
        "object": header.get("OBJECT", ""),
        # Dossiers parents (capture, nuit…) : leur nom cite souvent les cibles
        "folder": " ".join(p.name for p in list(path.parents)[:3]),
        "filter": header.get("FILTER", ""),
        "instrument": header.get("INSTRUME", ""),
        "sensorTemp": number(header.get("CCD-TEMP")),
        "exposure": exposure,
        "frames": len(lights) or stacked or None,
        "stacked": stacked or None,
        "lat": number(header.get("SITELAT")),
        "lon": number(header.get("SITELONG")),
        "preview": str(preview) if preview.is_file() else "",
    }


def name_tokens(text: str) -> set:
    """Désignations de catalogue citées dans un texte : « NGC 6992,6995 IC1340 » → ngc6992, ngc6995, ic1340."""
    # (?<![a-z]) plutôt que \b : « 20261114_IC 1848 » colle la désignation à un tiret bas
    tokens = set()
    for m in re.finditer(r"(?<![a-z])(m|ngc|ic|sh2|c|hip)[\s_]*-?\s*(\d+[a-z]?)", text.lower()):
        tokens.add(m.group(1) + m.group(2))
    for m in re.finditer(r"(?<![a-z])(ngc|ic)[\s_]*(\d+(?:\s*[,/-]\s*\d+)+)", text.lower()):
        for digits in re.findall(r"\d+", m.group(2)):
            tokens.add(m.group(1) + digits)
    return tokens


def normalize_name(name: str) -> str:
    """« M42 », « M 42 », « m_42 » → « m42 »."""
    return re.sub(r"[\s_\-.]", "", name.lower())
