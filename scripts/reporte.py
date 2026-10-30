"""Une intervenciones y clasificaciones de una sesión y genera el resumen (JSON) y el reporte (HTML).

Uso:
  python scripts/reporte.py <prefijo>
  p. ej. python scripts/reporte.py camara_2026-07-28

Lee  data/processed/<prefijo>_sesion.json, data/processed/<prefijo>_turnos.jsonl y
     data/processed/clasif/<prefijo>_parte*.jsonl
Escribe data/processed/<prefijo>_resumen.json y reportes/<prefijo>.html
"""
import glob
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PALABRAS_POR_MINUTO = 140
MIN_INTERVENCIONES_PCT = 3  # por debajo no se publica porcentaje individual (rúbrica)

BLOQUES = ["misional", "procedimiento", "no_pertinente", "tiempo_muerto"]
FUNCIONES = ["legislativa", "constituyente", "control_politico", "judicial", "electoral",
             "administrativa", "control_publico", "protocolo"]
SUBTIPOS = ["fuera_de_tema", "alusiones_replicas", "confrontacion", "cortesias", "desorden"]


def minutos_entre(a: str, b: str) -> int:
    fa, fb = datetime.strptime(a, "%H:%M"), datetime.strptime(b, "%H:%M")
    return int((fb - fa).total_seconds() // 60)


def clave_nombre(nombre: str) -> frozenset:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return frozenset(t for t in sin_tildes.split() if t not in {"de", "del", "la", "las", "los", "y"})


def unificar_nombres(nombres):
    """Agrupa variantes del mismo nombre ('José Welfran Mendoza' ⊂ 'Welfran Junior Mendoza Torres')."""
    canonico = {}
    frecuencia = Counter(nombres)
    # la variante más completa y, entre iguales, la más frecuente queda como nombre canónico
    por_largo = sorted(frecuencia, key=lambda n: (-len(clave_nombre(n)), -frecuencia[n]))
    for n in por_largo:
        k = clave_nombre(n)
        destino = next((c for c in canonico.values() if c != n and len(k) >= 2
                        and k <= clave_nombre(c)), None)
        canonico[n] = destino or n
    return canonico


def validar(turnos, clasif):
    ids = {t["id"] for t in turnos if t["rol"] != "acta"}
    faltan = sorted(ids - clasif.keys())
    errores = []
    for i, c in clasif.items():
        if c.get("bloque") not in BLOQUES:
            errores.append((i, "bloque", c.get("bloque")))
        if c.get("bloque") == "misional" and c.get("funcion") not in FUNCIONES:
            errores.append((i, "funcion", c.get("funcion")))
        if c.get("bloque") == "no_pertinente" and c.get("subtipo") not in SUBTIPOS:
            errores.append((i, "subtipo", c.get("subtipo")))
    return faltan, errores


def main():
    prefijo = sys.argv[1]
    base = Path("data/processed")
    sesion = json.loads((base / f"{prefijo}_sesion.json").read_text())
    turnos = [json.loads(l) for l in open(base / f"{prefijo}_turnos.jsonl")]
    clasif = {}
    for ruta in sorted(glob.glob(str(base / "clasif" / f"{prefijo}_parte*.jsonl"))):
        for l in open(ruta):
            if l.strip():
                c = json.loads(l)
                clasif[c["id"]] = c

    faltan, errores = validar(turnos, clasif)
    if faltan or errores:
        print("faltan:", faltan[:20], "errores:", errores[:20])
        sys.exit(1)

    h = sesion["horas"]
    convocatoria = minutos_entre(h["citacion"], h["cierre"])
    espera = minutos_entre(h["citacion"], h["apertura_registro"])
    en_sesion = minutos_entre(h["apertura_registro"], h["cierre"])

    habla = [t for t in turnos if t["rol"] != "acta"]
    canon = unificar_nombres([t["orador"] for t in habla])
    por_bloque, por_funcion, por_subtipo = Counter(), Counter(), Counter()
    secuencia, no_pertinentes = [], []
    # solo turnos hablados como congresista: quien preside un tramo no suma esos turnos a su ficha
    personas = defaultdict(lambda: {"intervenciones": 0, "palabras": 0,
                                    "palabras_no_pertinentes": 0, "funciones": Counter()})
    for t in habla:
        c = clasif[t["id"]]
        m = t["palabras"] / PALABRAS_POR_MINUTO
        por_bloque[c["bloque"]] += m
        if c["bloque"] == "misional":
            por_funcion[c["funcion"]] += m
        if c["bloque"] == "no_pertinente":
            por_subtipo[c["subtipo"]] += m
        orador = canon[t["orador"]]
        secuencia.append({"id": t["id"], "orador": orador, "rol": t["rol"], "bloque": c["bloque"],
                          "funcion": c.get("funcion"), "subtipo": c.get("subtipo"),
                          "min": round(m, 2), "pagina": t["pagina"], "evidencia": c.get("evidencia", ""),
                          "asunto": c.get("asunto", ""), "confianza": c.get("confianza", "")})
        if c["bloque"] == "no_pertinente":
            no_pertinentes.append(secuencia[-1])
        if t["rol"] != "congresista":
            continue
        p = personas[orador]
        p["intervenciones"] += 1
        p["palabras"] += t["palabras"]
        if c["bloque"] == "no_pertinente":
            p["palabras_no_pertinentes"] += t["palabras"]
        if c["bloque"] == "misional":
            p["funciones"][c["funcion"]] += t["palabras"]

    min_habla = sum(por_bloque.values())
    sin_habla = max(en_sesion - min_habla, 0)
    congresistas = []
    for nombre, p in personas.items():
        pct = (100 * p["palabras_no_pertinentes"] / p["palabras"]
               if p["intervenciones"] >= MIN_INTERVENCIONES_PCT else None)
        congresistas.append({"nombre": nombre, "intervenciones": p["intervenciones"],
                             "min": round(p["palabras"] / PALABRAS_POR_MINUTO, 1),
                             "pct_no_pertinente": None if pct is None else round(pct),
                             "funcion_principal": p["funciones"].most_common(1)[0][0] if p["funciones"] else None})
    congresistas.sort(key=lambda x: -x["min"])

    resumen = {
        "sesion": sesion,
        "metodo": {"palabras_por_minuto": PALABRAS_POR_MINUTO, "rubrica": "v0.1",
                   "fuente_tiempos": "acta (estimación por palabras)"},
        "minutos": {"convocatoria": convocatoria, "espera_antes_del_registro": espera,
                    "retraso_inicio": minutos_entre(h["citacion"], h["inicio_sesion"]),
                    "en_sesion": en_sesion, "habla_estimada": round(min_habla),
                    "sin_habla_registrada": round(sin_habla),
                    "por_bloque": {b: round(por_bloque[b], 1) for b in BLOQUES},
                    "por_funcion": {f: round(por_funcion[f], 1) for f in FUNCIONES if por_funcion[f]},
                    "por_subtipo": {s: round(por_subtipo[s], 1) for s in SUBTIPOS if por_subtipo[s]}},
        "conteos": {"intervenciones": len(habla), "congresistas_que_hablaron": len(congresistas),
                    "no_pertinentes": len(no_pertinentes),
                    "confianza_baja": sum(1 for s in secuencia if s["confianza"] == "baja")},
        "nombres_unificados": {k: v for k, v in canon.items() if k != v},
        "congresistas": congresistas,
        "secuencia": secuencia,
    }
    (base / f"{prefijo}_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))

    plantilla = Path("scripts/plantilla_reporte.html").read_text()
    datos = json.dumps(resumen, ensure_ascii=False).replace("</", "<\\/")
    Path("reportes").mkdir(exist_ok=True)
    salida = Path("reportes") / f"{prefijo}.html"
    salida.write_text(plantilla.replace("/*__DATOS__*/null", datos))
    print(json.dumps({k: resumen[k] for k in ("minutos", "conteos", "nombres_unificados")},
                     ensure_ascii=False, indent=1))
    print("->", salida)


if __name__ == "__main__":
    main()
