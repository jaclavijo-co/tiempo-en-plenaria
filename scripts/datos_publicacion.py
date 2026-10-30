"""Arma los archivos de datos del informe público a partir de las fuentes ya procesadas.

Entradas: catálogo de videos, órdenes del día del Senado, inventario de la Gaceta y resumen del piloto.
Salidas en publicacion/: sesiones.csv, agenda_senado.csv, piloto_camara_2026-07-28.csv, corte.csv
"""
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

INICIO = "2026-07-20"
# el período llega hasta la última plenaria transmitida que está en el catálogo
CORTE = max(f["fecha"] for f in csv.DictReader(open("data/catalogo/plenarias.csv")))
SALIDA = Path("publicacion")
# Motivos tomados de los comunicados de la Secretaría General del Senado
NOTAS_SENADO = {
    "2026-08-05": "Aplazada: la posesión presidencial se hizo el 7 de agosto en Cali (comunicado del 3 de agosto).",
    "2026-08-11": "Aplazada por el desastre natural que afectó varias regiones (comunicado del 10 de agosto).",
    "2026-08-12": "Citada a las 3:00 p. m.; la Secretaría la corrió a las 4:00 p. m. (comunicado del 12 de agosto).",
}


def dias(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def main():
    videos = defaultdict(int)
    for f in csv.DictReader(open("data/catalogo/plenarias.csv")):
        videos[(f["camara"], f["fecha"])] += int(f["duracion_min"])

    ordenes = json.load(open("data/processed/senado_ordenes_del_dia.json"))
    senado = {s["fecha"]: s for s in ordenes["sesiones"]
              if s["tipo"] in ("plenaria", "oposicion") and s["fecha"] and s["fecha"] <= CORTE}

    actas = {}
    gacetas_leidas = []
    for l in open("data/catalogo/gacetas_2026.jsonl"):
        g = json.loads(l)
        if g.get("fecha_publicacion") and "error" not in g:
            gacetas_leidas.append(g)
        for a in g.get("actas", []):
            f = a.get("fecha_sesion")
            if a["plenaria"] and f and INICIO <= f <= CORTE and g.get("fecha_publicacion"):
                clave = (g["entidad"], f)
                # si un acta sale en varias gacetas, cuenta la primera publicación
                if clave not in actas or g["fecha_publicacion"] < actas[clave]["publicada"]:
                    actas[clave] = {"gaceta": g["gaceta"], "publicada": g["fecha_publicacion"], "acta": a["numero"]}

    filas = []
    claves = set(videos) | {("Senado", f) for f in senado}
    for camara, fecha in sorted(claves, key=lambda k: (k[1], k[0])):
        o = senado.get(fecha) if camara == "Senado" else None
        aplazada = camara == "Senado" and NOTAS_SENADO.get(fecha, "").startswith("Aplazada")
        a = actas.get((camara, fecha))
        filas.append({
            "camara": camara, "fecha": fecha, "tipo": o["tipo"] if o else "plenaria",
            "estado": "aplazada" if aplazada else "realizada" if videos.get((camara, fecha)) else "sin_video",
            "hora_citacion": (o["hora_citacion"] or "").replace("a.m.", " a. m.").replace("p.m.", " p. m.") if o else "",
            "proyectos_agendados": len(o["proyectos"]) if o else "",
            "video_min": videos.get((camara, fecha), ""),
            "acta": "sí" if a else "no",
            "gaceta": a["gaceta"] if a else "", "publicada": a["publicada"] if a else "",
            "rezago_dias": dias(fecha, a["publicada"]) if a else "",
            "nota": NOTAS_SENADO.get(fecha, "") if camara == "Senado" else "",
        })

    apariciones = defaultdict(list)
    titulos = {}
    for s in ordenes["sesiones"]:
        if s["tipo"] == "plenaria" and s["fecha"] and s["fecha"] <= CORTE:
            for p in s["proyectos"]:
                apariciones[p["id"]].append(s["fecha"])
                titulos[p["id"]] = p["titulo"]
    agenda = [{"id": k, "titulo": titulos[k], "veces": len(v), "primera": min(v), "ultima": max(v)}
              for k, v in apariciones.items()]

    resumen = json.load(open("data/processed/camara_2026-07-28_resumen.json"))["minutos"]
    piloto = [
        {"tramo": "espera", "minutos": resumen["espera_antes_del_registro"]},
        {"tramo": "misional", "minutos": resumen["por_bloque"]["misional"]},
        {"tramo": "procedimiento", "minutos": resumen["por_bloque"]["procedimiento"]},
        {"tramo": "no_pertinente", "minutos": resumen["por_bloque"]["no_pertinente"]},
        {"tramo": "sin_habla", "minutos": resumen["sin_habla_registrada"]},
        {"tramo": "retraso_inicio", "minutos": resumen["retraso_inicio"]},
    ]

    corte = [{"inicio": INICIO, "fin": CORTE,
              "gaceta_hasta": max(g["fecha_publicacion"] for g in gacetas_leidas if g["fecha_publicacion"] <= date.today().isoformat()),
              "gaceta_num_max": max(g["gaceta"] for g in gacetas_leidas),
              "actualizado": date.today().isoformat()}]

    SALIDA.mkdir(exist_ok=True)
    for nombre, datos in (("sesiones.csv", filas), ("agenda_senado.csv", agenda),
                          ("piloto_camara_2026-07-28.csv", piloto), ("corte.csv", corte)):
        with open(SALIDA / nombre, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(datos[0]))
            w.writeheader()
            w.writerows(datos)

    hechas = [f for f in filas if f["estado"] == "realizada"]
    con = [f for f in hechas if f["acta"] == "sí"]
    print(f"sesiones: {len(filas)} filas | transmitidas {len(hechas)} | con acta {len(con)} | "
          f"aplazadas {sum(f['estado'] == 'aplazada' for f in filas)} | sin video {sum(f['estado'] == 'sin_video' for f in filas)}")
    for f in con:
        print(f"  {f['camara']} {f['fecha']} -> gaceta {f['gaceta']} ({f['publicada']}, {f['rezago_dias']} días)")
    top = sorted(agenda, key=lambda p: -p["veces"])[:5]
    print("agenda:", len(agenda), "proyectos; máximo", top[0]["veces"], "veces:", [p["id"] for p in top if p["veces"] == top[0]["veces"]])


if __name__ == "__main__":
    main()
