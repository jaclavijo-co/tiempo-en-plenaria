"""Extrae de los órdenes del día oficiales del Senado la hora de citación y los proyectos agendados.

Uso:
  python scripts/ordenes_del_dia.py data/processed/orden_del_dia_senado data/catalogo/plenarias_2026-07-20_a_2026-10-29.csv
Escribe data/processed/senado_ordenes_del_dia.json
"""
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict

MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
PROYECTO = re.compile(
    r"Proyecto de (ley|acto legislativo)( estatutaria| orgánica)? (?:número|No\.?|N°)\s*([0-9]+)\s*de\s*(20\d\d)\s*Senado"
    r"(?:\s*[,–-]?\s*(?:número\s*)?([0-9]+)\s*de\s*(20\d\d)\s*Cámara)?[^“\"]{0,40}[“\"]([^”\"]{5,400})[”\"]",
    re.I,
)


def fecha_de(nombre: str):
    m = re.search(r"(\d{1,2})-de-([a-z]+)-(20\d\d)", nombre)
    if m and m.group(2) in MESES:
        return f"{m.group(3)}-{MESES.index(m.group(2)) + 1:02d}-{int(m.group(1)):02d}"
    return None


def main():
    carpeta, catalogo = sys.argv[1], sys.argv[2]
    videos = defaultdict(list)
    for fila in csv.DictReader(open(catalogo)):
        if fila["camara"] == "Senado":
            videos[fila["fecha"]].append({"video_id": fila["video_id"], "duracion_min": int(fila["duracion_min"])})

    sesiones, aplazadas = {}, {}
    for ruta in sorted(glob.glob(os.path.join(carpeta, "*.txt"))):
        nombre = os.path.basename(ruta)[:-4]
        texto = open(ruta).read()
        plano = re.sub(r"\s+", " ", texto)
        if nombre.startswith("comunicado"):
            for m in re.finditer(r"sesión (?:plenaria )?(?:del Senado de la República, )?(?:convocada|programada) para (?:el (?:día )?)?(?:\w+ )?(\d{1,2}) de (\w+) de (20\d\d)[^.]*?(aplazada|trasladada[^.]*)", plano, re.I):
                if m.group(2).lower() in MESES:
                    f = f"{m.group(3)}-{MESES.index(m.group(2).lower()) + 1:02d}-{int(m.group(1)):02d}"
                    aplazadas[f] = {"motivo_texto": plano[:600], "documento": nombre, "accion": m.group(4)[:60]}
            continue
        fecha = fecha_de(nombre)
        hora = re.search(r"Hora[:\s]*([0-9]{1,2}[:.][0-9]{2}\s*[ap]\.?\s*m\.?)", plano, re.I)
        tipo = "congreso_pleno" if "congreso-pleno" in nombre else "oposicion" if "oposicion" in nombre else "plenaria"
        proyectos = []
        for m in PROYECTO.finditer(plano):
            clave = f"{'PAL' if m.group(1).lower().startswith('acto') else 'PL'} {int(m.group(3)):03d}/{m.group(4)} S"
            if clave not in {p["id"] for p in proyectos}:
                proyectos.append({"id": clave, "camara": f"{m.group(5)}/{m.group(6)} C" if m.group(5) else None,
                                  "titulo": m.group(7).strip()})
        control_politico = len(re.findall(r"debate de control pol[ií]tico|citaci[oó]n", plano, re.I))
        actual = sesiones.get((fecha, tipo))
        # si hay un orden del día "modificado" para la misma fecha, ese es el vigente
        if actual is None or "modificado" in nombre:
            sesiones[(fecha, tipo)] = {"fecha": fecha, "tipo": tipo, "documento": nombre,
                                       "hora_citacion": hora.group(1).replace(" ", "") if hora else None,
                                       "proyectos": proyectos, "menciones_control_politico": control_politico}

    lista = sorted(sesiones.values(), key=lambda s: (s["fecha"] or "", s["tipo"]))
    for s in lista:
        s["video"] = videos.get(s["fecha"], []) if s["tipo"] != "congreso_pleno" else []
        s["aplazada"] = aplazadas.get(s["fecha"]) if s["tipo"] == "plenaria" else None

    apariciones = defaultdict(list)
    for s in lista:
        if s["tipo"] == "plenaria":
            for p in s["proyectos"]:
                apariciones[p["id"]].append(s["fecha"])
    titulos = {p["id"]: p["titulo"] for s in lista for p in s["proyectos"]}
    proyectos = sorted(({"id": k, "titulo": titulos[k], "veces_en_orden_del_dia": len(v),
                         "primera": min(v), "ultima": max(v)} for k, v in apariciones.items()),
                       key=lambda p: (-p["veces_en_orden_del_dia"], p["id"]))
    salida = {"sesiones": lista, "proyectos": proyectos, "fechas_sin_orden_del_dia": sorted(
        f for f in videos if f not in {s["fecha"] for s in lista})}
    json.dump(salida, open("data/processed/senado_ordenes_del_dia.json", "w"), ensure_ascii=False, indent=1)
    for s in lista:
        print(f"{s['fecha']} {s['tipo']:15} cita {s['hora_citacion'] or '?':9} proyectos={len(s['proyectos']):2} "
              f"video={'sí' if s['video'] else 'no'} {'APLAZADA' if s['aplazada'] else ''}")
    print("proyectos distintos:", len(proyectos), "| fechas con video sin orden del día:", salida["fechas_sin_orden_del_dia"])
    for p in proyectos[:8]:
        print(f"  {p['veces_en_orden_del_dia']:2}x {p['id']} ({p['primera']}→{p['ultima']}) {p['titulo'][:70]}")


if __name__ == "__main__":
    main()
