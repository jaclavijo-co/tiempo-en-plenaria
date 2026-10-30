"""Transcribe con marcas de tiempo el audio descargado de una plenaria (mlx-whisper, local).

Uso:
  python scripts/transcribir.py <video_id>
Lee data/descargas/<video_id>/audio.* y escribe data/descargas/<video_id>/transcripcion.json
(segmentos con inicio, fin y texto).
"""
import json
import sys
from pathlib import Path

import mlx_whisper

RAIZ = Path(__file__).resolve().parent.parent
MODELO = "mlx-community/whisper-large-v3-turbo"
# Vocabulario de plenaria para orientar al modelo con nombres propios y fórmulas del Reglamento
CONTEXTO = ("Sesión plenaria del Congreso de la República de Colombia. Señor Presidente, señor Secretario, "
            "llamado a lista, verificación del quórum, orden del día, proposición, constancia, moción de orden, "
            "honorable Senador, honorable Representante, Ley 5ª de 1992.")


def main():
    video_id = sys.argv[1]
    carpeta = RAIZ / "data" / "descargas" / video_id
    audio = next(p for p in carpeta.glob("audio.*") if p.suffix not in (".json", ".vtt"))
    r = mlx_whisper.transcribe(str(audio), path_or_hf_repo=MODELO, language="es",
                               initial_prompt=CONTEXTO, condition_on_previous_text=False)
    segmentos = [{"inicio": round(s["start"], 2), "fin": round(s["end"], 2), "texto": s["text"].strip()}
                 for s in r["segments"]]
    (carpeta / "transcripcion.json").write_text(json.dumps(
        {"video_id": video_id, "modelo": MODELO, "segmentos": segmentos}, ensure_ascii=False, indent=1))
    print(f"{len(segmentos)} segmentos -> {carpeta / 'transcripcion.json'}")


if __name__ == "__main__":
    main()
