"""Catálogo maestro de plenarias (data/catalogo/plenarias.csv): lectura de títulos de Canal Congreso y altas nuevas."""
import csv
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "data" / "catalogo" / "plenarias.csv"
INICIO = "2026-07-20"  # instalación del Congreso 2026-2030
CAMPOS = ["camara", "fecha", "video_id", "duracion_min", "titulo"]
MESES = {m: i for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1)}


def leer_titulo(titulo: str):
    """Devuelve (cámara, fecha ISO) si el título es de una plenaria del Senado o de la Cámara; si no, None."""
    t = titulo.lower()
    if "plenaria" not in t:
        return None
    m = re.search(r"(\d{1,2})\s*de\s*([a-záéíóú]+)\s*(?:de\s*)?(20\d\d)", t) or re.search(r"([a-záéíóú]+)\s+(\d{1,2})\s+de\s+(20\d\d)", t)
    if not m:
        return None
    a, b, anio = m.groups()
    dia, mes = (int(a), MESES.get(b)) if a.isdigit() else (int(b), MESES.get(a))
    if not mes:
        return None
    camara = "Senado" if "senado" in t else "Cámara" if ("cámara" in t or "camara" in t) else None
    return (camara, f"{anio}-{mes:02d}-{dia:02d}") if camara else None


def leer():
    return list(csv.DictReader(open(CATALOGO))) if CATALOGO.exists() else []


def agregar(nuevas: list[dict]) -> list[dict]:
    """Agrega al catálogo los videos que no estén; devuelve los que entraron."""
    filas = leer()
    vistos = {f["video_id"] for f in filas}
    altas = [n for n in nuevas if n["video_id"] not in vistos and n["fecha"] >= INICIO]
    if altas:
        filas += altas
        filas.sort(key=lambda f: (f["camara"], f["fecha"], f["video_id"]))
        with open(CATALOGO, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(filas)
    return altas
