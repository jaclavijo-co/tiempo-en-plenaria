"""Detector diario de plenarias nuevas.

- Canal Congreso: lee los 15 videos más recientes y agrega al catálogo y al inicio de la cola de descargas
  las plenarias terminadas que no estén. Si el descargador está en espera por un bloqueo de YouTube, ese
  día no consulta el canal.
- Secretaría del Senado: baja los órdenes del día y comunicados nuevos, extrae su texto y rehace el
  resumen de proyectos agendados.
Al final sube los cambios a GitHub.
"""
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogo  # noqa: E402
import descargador_lento as dl  # noqa: E402
from subir_github import subir  # noqa: E402

RAIZ = catalogo.RAIZ
CANAL = "https://www.youtube.com/@CanalCongresoColombia/streams"
SENADO = "http://www.secretariasenado.gov.co"
PDFS = RAIZ / "data" / "raw" / "orden_del_dia_senado"
TEXTOS = RAIZ / "data" / "processed" / "orden_del_dia_senado"
AGENTE = {"User-Agent": "auditoria-plenarias/0.1 (investigacion ciudadana)"}


def youtube_en_espera() -> bool:
    e = dl.cargar_estado()
    espera = e["proximo_intento"] and datetime.now() < datetime.fromisoformat(e["proximo_intento"])
    return e["detenido"] or bool(espera and e["bloqueos_seguidos"])


def encolar(altas: list[dict]):
    filas = dl.cola()
    ids = {f["video_id"] for f in filas}
    nuevas = [{"orden": 0, "camara": a["camara"], "fecha": a["fecha"], "video_id": a["video_id"],
               "duracion_min": a["duracion_min"], "estado": "pendiente"}
              for a in sorted(altas, key=lambda a: a["fecha"], reverse=True) if a["video_id"] not in ids]
    filas = nuevas + filas  # lo nuevo se procesa primero
    for i, f in enumerate(filas, 1):
        f["orden"] = i
    dl.guardar_cola(filas)


def revisar_canal() -> list[dict]:
    if youtube_en_espera():
        dl.log("detector: YouTube en espera por bloqueo; hoy no se consulta el canal")
        return []
    r = subprocess.run([str(dl.YTDLP), "--js-runtimes", "node", "--flat-playlist", "--playlist-end", "15",
                        "--print", "%(id)s\t%(duration)s\t%(title)s", CANAL],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or any(s in r.stdout + r.stderr for s in dl.SENALES_BLOQUEO):
        dl.log("detector: el canal no respondió; se intenta mañana")
        return []
    encontradas = []
    for linea in r.stdout.splitlines():
        vid, dur, titulo = (linea.split("\t", 2) + ["", ""])[:3]
        leida = catalogo.leer_titulo(titulo)
        # una transmisión en vivo todavía no tiene duración: entra cuando termine
        if not leida or not re.fullmatch(r"\d+(\.\d+)?", dur):
            continue
        encontradas.append({"camara": leida[0], "fecha": leida[1], "video_id": vid,
                            "duracion_min": round(float(dur) / 60), "titulo": titulo.strip()})
    altas = catalogo.agregar(encontradas)
    if altas:
        encolar(altas)
    dl.log(f"detector: {len(altas)} plenarias nuevas en el canal")
    return altas


def revisar_senado() -> list[str]:
    html = urllib.request.urlopen(urllib.request.Request(SENADO + "/orden-del-dia-senado", headers=AGENTE),
                                  timeout=60).read().decode("utf-8", "ignore")
    nuevos = []
    for ruta in sorted(set(re.findall(r"/orden-del-dia-senado/[0-9]+-[a-z0-9-]+/file", html))):
        nombre = re.sub(r"^.*/[0-9]+-", "", ruta).removesuffix("/file")
        destino = PDFS / f"{nombre}.pdf"
        if destino.exists() or not re.search(r"-20(2[6-9]|3\d)", nombre):
            continue
        time.sleep(1)
        destino.write_bytes(urllib.request.urlopen(urllib.request.Request(SENADO + ruta, headers=AGENTE), timeout=60).read())
        (TEXTOS / f"{nombre}.txt").write_text("\n".join(p.get_text() for p in fitz.open(destino)))
        nuevos.append(nombre)
    if nuevos:
        subprocess.run([sys.executable, "-E", "-P", str(RAIZ / "scripts" / "ordenes_del_dia.py"),
                        str(TEXTOS), str(catalogo.CATALOGO)], cwd=RAIZ, capture_output=True)
    dl.log(f"detector: {len(nuevos)} documentos nuevos del Senado {nuevos}")
    return nuevos


def main():
    altas, docs = [], []
    try:
        altas = revisar_canal()
    except Exception as e:  # una fuente caída no detiene la otra
        dl.log(f"detector: error en el canal: {e}")
    try:
        docs = revisar_senado()
    except Exception as e:
        dl.log(f"detector: error en la Secretaría del Senado: {e}")
    resultado = subir(f"Rutina diaria {datetime.now():%Y-%m-%d}: {len(altas)} plenarias nuevas, "
                      f"{len(docs)} documentos del Senado, transcripciones del día")
    dl.log(f"detector: GitHub {resultado}")


if __name__ == "__main__":
    main()
