"""Rutina semanal (lunes): pone al día el diagnóstico público.

1. Busca actas nuevas en la Gaceta desde el último número leído y reintenta los números que faltaban.
2. Clasifica las sesiones transcritas, solo si está activado en data/rutinas/config.json.
3. Regenera los datos del informe y verifica que no se haya perdido nada.
4. Copia los datos al sitio y lo despliega en Vercel.
5. Escribe el resumen de la semana en reportes/semanal/ y sube todo a GitHub.

Uso: python scripts/corte_semanal.py [--sin-publicar]
"""
import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogo  # noqa: E402
import descargador_lento as dl  # noqa: E402
from subir_github import subir  # noqa: E402

RAIZ = catalogo.RAIZ
PY = sys.executable
INVENTARIO = RAIZ / "data" / "catalogo" / "gacetas_2026.jsonl"
CONFIG = RAIZ / "data" / "rutinas" / "config.json"
PUBLICACION = RAIZ / "publicacion"
SITIO = RAIZ / "sitio"
VERCEL = Path.home() / ".npm-global" / "bin" / "vercel"
ARCHIVOS_SITIO = ["sesiones.csv", "agenda_senado.csv", "piloto_camara_2026-07-28.csv", "corte.csv"]


def correr(*args, cwd=RAIZ, timeout=None):
    return subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True, timeout=timeout)


def actas_conocidas() -> set:
    return {(g["entidad"], a["fecha_sesion"], g["gaceta"]) for g in map(json.loads, open(INVENTARIO))
            if "error" not in g for a in g["actas"] if a["plenaria"] and (a["fecha_sesion"] or "") >= catalogo.INICIO}


def buscar_actas() -> list:
    antes = actas_conocidas()
    filas = [json.loads(l) for l in open(INVENTARIO)]
    # los números que antes fallaron se vuelven a intentar
    INVENTARIO.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas if "error" not in f))
    ultimo = max(f["gaceta"] for f in filas if "error" not in f)
    correr(PY, "-E", "-P", RAIZ / "scripts" / "inventario_gacetas.py", 860, ultimo + 300, INVENTARIO, 15, timeout=6 * 3600)
    return sorted(actas_conocidas() - antes)


def clasificar() -> str:
    config = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    if not config.get("clasificar"):
        return "pendiente: falta decidir con qué se paga la clasificación"
    return "activada, pero el clasificador automático todavía no está implementado"


def contar_sesiones() -> dict:
    ruta = PUBLICACION / "sesiones.csv"
    filas = list(csv.DictReader(open(ruta))) if ruta.exists() else []
    hechas = [f for f in filas if f["estado"] == "realizada"]
    return {"filas": len(filas), "transmitidas": len(hechas), "con_acta": sum(f["acta"] == "sí" for f in hechas)}


def regenerar_datos() -> tuple[bool, str]:
    antes = contar_sesiones()
    r = correr(PY, "-E", "-P", RAIZ / "scripts" / "datos_publicacion.py")
    if r.returncode != 0:
        return False, "falló la generación de datos: " + r.stderr.strip()[-300:]
    despues = contar_sesiones()
    # los datos solo crecen: si algo baja, hay un error de lectura y no se publica
    caidas = [k for k in antes if despues[k] < antes[k]]
    if caidas:
        return False, f"los datos bajaron en {caidas} ({antes} → {despues}); no se publica"
    return True, f"{despues['transmitidas']} plenarias transmitidas, {despues['con_acta']} con acta"


def publicar_sitio() -> str:
    for nombre in ARCHIVOS_SITIO:
        shutil.copy(PUBLICACION / nombre, SITIO / "datos" / nombre)
    r = correr(VERCEL, "deploy", "--prod", "--yes", cwd=SITIO, timeout=900)
    return "desplegado en tiempo-en-plenaria.vercel.app" if r.returncode == 0 else "Vercel falló: " + (r.stderr or r.stdout).strip()[-300:]


def documentos_senado_de_la_semana() -> list[str]:
    """Documentos cuya sesión (fecha en el nombre del archivo) cae en los últimos 7 días o después."""
    desde = (date.today() - timedelta(days=7)).isoformat()
    docs = []
    for p in (RAIZ / "data" / "raw" / "orden_del_dia_senado").glob("*.pdf"):
        m = re.search(r"(\d{1,2})-de-([a-z]+)-(20\d\d)", p.stem)
        if m and m.group(2) in catalogo.MESES and f"{m.group(3)}-{catalogo.MESES[m.group(2)]:02d}-{int(m.group(1)):02d}" >= desde:
            docs.append(p.stem)
    return sorted(docs)


def escribir_resumen(actas: list, clasificacion: str, datos: str, sitio: str) -> Path:
    hoy = date.today()
    nuevas = [f for f in catalogo.leer() if f["fecha"] >= (hoy - timedelta(days=7)).isoformat()]
    cola = dl.cola()
    estado = dl.cargar_estado()
    docs = documentos_senado_de_la_semana()
    lineas = [
        f"# Corte semanal del {hoy.isoformat()}", "",
        f"**Plenarias de la última semana en el canal:** {len(nuevas)}",
        *[f"- {f['camara']} {f['fecha']} ({f['duracion_min']} min) · https://www.youtube.com/watch?v={f['video_id']}" for f in nuevas],
        "", "**Video y transcripción:** " + ", ".join(f"{k} {sum(f['estado'] == k for f in cola)}"
                                                    for k in ("pendiente", "descargado", "transcrito", "error")),
        f"Descargador: {'detenido por bloqueos, requiere revisión' if estado['detenido'] else 'activo'}"
        f" · bloqueos seguidos: {estado['bloqueos_seguidos']}",
        "", f"**Actas de plenaria nuevas en la Gaceta:** {len(actas)}",
        *[f"- {c} sesión del {f} · Gaceta {g}" for c, f, g in actas],
        "", f"**Documentos nuevos del Senado esta semana:** {len(docs)}",
        *[f"- {d}" + (" · revisar si anuncia un aplazamiento" if d.startswith("comunicado") else "") for d in docs],
        "", f"**Clasificación:** {clasificacion}",
        f"**Datos del informe:** {datos}",
        f"**Sitio:** {sitio}", "",
    ]
    ruta = RAIZ / "reportes" / "semanal" / f"{hoy.isoformat()}.md"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(lineas))
    return ruta


def main():
    publicar = "--sin-publicar" not in sys.argv
    dl.log("semanal: inicio")
    try:
        actas = buscar_actas()
    except Exception as e:
        actas = []
        dl.log(f"semanal: error buscando actas: {e}")
    clasificacion = clasificar()
    ok, datos = regenerar_datos()
    sitio = publicar_sitio() if ok and publicar else "no se publicó" + ("" if ok else " por el error en los datos")
    ruta = escribir_resumen(actas, clasificacion, datos, sitio)
    github = subir(f"Corte semanal {date.today().isoformat()}: {len(actas)} actas nuevas; {datos}") if publicar else "no se subió (prueba)"
    dl.log(f"semanal: {datos} · {sitio} · GitHub {github}")
    dl.avisar(f"Corte semanal listo: {len(actas)} actas nuevas. {sitio}. GitHub: {github}")
    print(ruta.read_text())


if __name__ == "__main__":
    main()
