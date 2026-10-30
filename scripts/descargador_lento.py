"""Descarga el audio de las plenarias de a un video por turno, respetando los límites de YouTube.

Salvaguardas (no negociables):
- Un solo video por ejecución y al menos INTERVALO_H horas entre descargas exitosas.
- Solo audio, en la calidad mínima suficiente para transcribir (m4a 48 kbps), con límite de velocidad.
- Sin cookies ni cuenta, sin cambiar de cliente, sin proxies: la misma petición que haría cualquier
  usuario. Si YouTube pide verificación o responde 429, no se insiste.
- Ante bloqueo, espera creciente (2, 4, 8, 16, 24 h). Tras MAX_BLOQUEOS seguidos se detiene del todo y
  avisa; solo se reanuda a mano con --reanudar.

Uso:
  python scripts/descargador_lento.py            # un turno: descarga y transcribe el siguiente video si toca
  python scripts/descargador_lento.py --estado   # muestra la cola y el estado
  python scripts/descargador_lento.py --reanudar # quita la detención después de revisar
"""
import csv
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "descargas"
COLA = DIR / "cola.csv"
ESTADO = DIR / "estado.json"
BITACORA = DIR / "bitacora.log"
YTDLP = RAIZ / ".venv" / "bin" / "yt-dlp"

INTERVALO_H = 3
ESPERAS_BLOQUEO_H = [2, 4, 8, 16, 24]
MAX_BLOQUEOS = len(ESPERAS_BLOQUEO_H)
SENALES_BLOQUEO = ("429", "confirm you’re not a bot", "confirm you're not a bot", "Sign in to confirm")


def log(msg: str):
    linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linea)
    with open(BITACORA, "a") as f:
        f.write(linea + "\n")


def avisar(msg: str):
    subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "Auditoría plenarias"'],
                   check=False, capture_output=True)


def cargar_estado() -> dict:
    if ESTADO.exists():
        return json.loads(ESTADO.read_text())
    return {"proximo_intento": None, "bloqueos_seguidos": 0, "detenido": False}


def guardar_estado(e: dict):
    ESTADO.write_text(json.dumps(e, ensure_ascii=False, indent=1))


def cola() -> list[dict]:
    return list(csv.DictReader(open(COLA)))


def guardar_cola(filas: list[dict]):
    with open(COLA, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


def descargar(fila: dict) -> str:
    destino = DIR / fila["video_id"]
    destino.mkdir(parents=True, exist_ok=True)
    cmd = [str(YTDLP), "--js-runtimes", "node", "--no-playlist",
           "-f", "139/bestaudio[ext=m4a]/bestaudio", "--limit-rate", "1M", "--sleep-requests", "3",
           "--write-info-json", "--write-auto-subs", "--sub-langs", "es", "--sub-format", "vtt",
           "-o", str(destino / "audio.%(ext)s"), "--", fila["video_id"]]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=4 * 3600)
    salida = r.stdout + r.stderr
    if r.returncode == 0:
        return "ok"
    return "bloqueo" if any(s in salida for s in SENALES_BLOQUEO) else "error: " + salida.strip()[-300:]


def turno():
    estado = cargar_estado()
    ahora = datetime.now()
    if estado["detenido"]:
        log("detenido por bloqueos repetidos; revisar y usar --reanudar")
        return
    if estado["proximo_intento"] and ahora < datetime.fromisoformat(estado["proximo_intento"]):
        return
    filas = cola()
    pendiente = next((f for f in filas if f["estado"] in ("pendiente", "error")), None)
    if not pendiente:
        log("cola terminada")
        return

    log(f"intentando {pendiente['video_id']} ({pendiente['camara']} {pendiente['fecha']})")
    resultado = descargar(pendiente)
    if resultado == "ok":
        pendiente["estado"] = "descargado"
        estado.update(bloqueos_seguidos=0, proximo_intento=(ahora + timedelta(hours=INTERVALO_H)).isoformat())
        log(f"descargado {pendiente['video_id']}; próximo intento en {INTERVALO_H} h")
        guardar_cola(filas)
        guardar_estado(estado)
        transcribir = subprocess.run([sys.executable, "-E", "-P", str(RAIZ / "scripts" / "transcribir.py"),
                                      pendiente["video_id"]], capture_output=True, text=True)
        pendiente["estado"] = "transcrito" if transcribir.returncode == 0 else "descargado"
        log(f"transcripción {pendiente['video_id']}: {'ok' if transcribir.returncode == 0 else transcribir.stderr[-300:]}")
    elif resultado == "bloqueo":
        n = estado["bloqueos_seguidos"] + 1
        estado["bloqueos_seguidos"] = n
        if n >= MAX_BLOQUEOS:
            estado["detenido"] = True
            log(f"bloqueo {n} seguido: detenido")
            avisar("YouTube sigue bloqueando. Descargas detenidas hasta revisión.")
        else:
            espera = ESPERAS_BLOQUEO_H[n - 1]
            estado["proximo_intento"] = (ahora + timedelta(hours=espera)).isoformat()
            log(f"bloqueo {n}: se reintenta en {espera} h")
    else:
        pendiente["estado"] = "error"
        estado["proximo_intento"] = (ahora + timedelta(hours=INTERVALO_H)).isoformat()
        log(f"{pendiente['video_id']} {resultado}")
    guardar_cola(filas)
    guardar_estado(estado)


def main():
    DIR.mkdir(parents=True, exist_ok=True)
    if "--reanudar" in sys.argv:
        e = cargar_estado()
        e.update(detenido=False, bloqueos_seguidos=0, proximo_intento=None)
        guardar_estado(e)
        log("reanudado a mano")
    elif "--estado" in sys.argv:
        filas = cola()
        print(json.dumps(cargar_estado(), ensure_ascii=False, indent=1))
        for k in ("pendiente", "descargado", "transcrito", "error"):
            print(k, sum(f["estado"] == k for f in filas))
        print("siguiente:", next((f"{f['camara']} {f['fecha']} {f['video_id']}" for f in filas
                                  if f["estado"] in ("pendiente", "error")), "—"))
    else:
        turno()


if __name__ == "__main__":
    main()
