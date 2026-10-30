"""Inventario de la Gaceta del Congreso: lee solo la primera página (índice) de cada número.

Los PDF de la Imprenta están linearizados: la primera página y sus recursos van al inicio del archivo.
Con dos consultas de rango (2 KB para leer el diccionario /Linearized y luego hasta /E) se obtiene el
índice sin descargar el PDF completo.

Uso:
  python scripts/inventario_gacetas.py 860 1612 data/catalogo/gacetas_2026.jsonl
Reanuda si el archivo de salida ya tiene números procesados.
"""
import io
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request

from pypdf import PdfReader
from pypdf._page import PageObject
from pypdf.generic import IndirectObject

URL = "https://www.redjurista.com/Compilaciones2018/gacetasCongreso/2026/gc_{n:04d}_2026.pdf"
PAUSA_S = 1.0
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()

logging.disable(logging.CRITICAL)


def rango(url: str, fin: int) -> bytes:
    req = urllib.request.Request(url, headers={"Range": f"bytes=0-{fin}",
                                               "User-Agent": "auditoria-plenarias/0.1 (investigacion ciudadana)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def primera_pagina(n: int) -> str:
    url = URL.format(n=n)
    cabeza = rango(url, 2047).decode("latin-1")
    lin = re.search(r"/Linearized.*?/E (\d+).*?>>", cabeza, re.S) or re.search(r"/E (\d+)", cabeza)
    obj = re.search(r"/O (\d+)", cabeza)
    if not (lin and obj):
        raise ValueError("no linearizado")
    datos = rango(url, int(lin.group(1)) + 4096)
    lector = PdfReader(io.BytesIO(datos), strict=False)
    ref = IndirectObject(int(obj.group(1)), 0, lector)
    pagina = PageObject(lector, ref)
    pagina.update(ref.get_object())
    return pagina.extract_text()


def analizar(n: int, texto: str) -> dict:
    plano = re.sub(r"\s+", " ", texto)
    compacto = re.sub(r"\s+", "", texto).upper()
    fecha = re.search(r"Bogotá, D\. ?C\., \w+, (\d{1,2}) de (\w+) de (20\d\d)", plano)
    entidad = ("Senado" if "SENADODELAREPÚBLICA" in compacto else
               "Cámara" if "CÁMARADEREPRESENTANTES" in compacto else "?")
    actas = []
    for m in re.finditer(r"Acta[^.]{0,40}?(?:número|No\.?|N[º°o]\.?)\s*(\d+)(.{0,160}?)(\d{1,2}) de (\w+) de[l]? (20\d\d)", plano):
        actas.append({"numero": int(m.group(1)), "contexto": m.group(0)[:220],
                      "plenaria": bool(re.search(r"plenari|congreso pleno", m.group(0), re.I)),
                      "fecha_sesion": f"{m.group(5)}-{MESES.index(m.group(4).lower()) + 1:02d}-{int(m.group(3)):02d}"
                      if m.group(4).lower() in MESES else None})
    return {"gaceta": n, "entidad": entidad,
            "fecha_publicacion": f"{fecha.group(3)}-{MESES.index(fecha.group(2).lower()) + 1:02d}-{int(fecha.group(1)):02d}"
            if fecha and fecha.group(2).lower() in MESES else None,
            "tiene_actas_de_plenaria": "ACTASDEPLENARIA" in compacto or any(a["plenaria"] for a in actas),
            "actas": actas, "indice": plano[:1500]}


def main():
    desde, hasta, salida = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    hechos = set()
    try:
        hechos = {json.loads(l)["gaceta"] for l in open(salida)}
    except FileNotFoundError:
        pass
    with open(salida, "a", encoding="utf-8") as f:
        for n in range(desde, hasta + 1):
            if n in hechos:
                continue
            try:
                fila = analizar(n, primera_pagina(n))
            except urllib.error.HTTPError as e:
                fila = {"gaceta": n, "error": f"HTTP {e.code}"}
            except Exception as e:  # PDF raro: se registra y se revisa a mano
                fila = {"gaceta": n, "error": str(e)[:120]}
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
            f.flush()
            time.sleep(PAUSA_S)


if __name__ == "__main__":
    main()
