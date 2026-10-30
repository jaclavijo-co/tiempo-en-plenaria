# Tiempo en plenaria

Auditoría ciudadana y abierta del uso del tiempo en las sesiones plenarias del Congreso de Colombia.
Mide qué parte de cada sesión se dedica a las funciones que la ley le asigna al Congreso
(Art. 6 de la Ley 5 de 1992), qué parte a procedimiento, qué parte a intervenciones que no tratan el
asunto en discusión y qué parte se pierde sin sesionar.

Todo es público: la rúbrica, las instrucciones del clasificador, los datos y el código. Si encuentras
una clasificación equivocada, abre un reporte con el id de la intervención y la página del acta.

Sitio: https://tiempo-en-plenaria.vercel.app · Qué significa cada dato: `DICCIONARIO-DE-DATOS.md` ·
Cómo colaborar: `CONTRIBUTING.md` · Conversación abierta: pestaña *Discussions*.

## Estructura

```
metodologia/
  rubrica.md                 Rúbrica de clasificación (versionada)
  prompt_clasificacion.md    Instrucciones exactas que recibe el clasificador
scripts/
  parse_acta.py              Segmenta un acta de la Gaceta en intervenciones por orador
  reporte.py                 Une intervenciones y clasificaciones; genera resumen y reporte
  plantilla_reporte.html     Plantilla del reporte por sesión
data/
  catalogo/                  Plenarias del período con su video en Canal Congreso
  raw/                       Fuentes descargadas sin modificar (PDF de la Gaceta)
  processed/                 Texto extraído, intervenciones, lotes y clasificaciones
reportes/                    Un HTML por sesión
```

## Cómo procesar una sesión a partir del acta

```bash
python3 -m venv --system-site-packages .venv && .venv/bin/pip install -r requirements.txt
# 1. Extraer el texto del PDF de la Gaceta a data/processed/<gaceta>.txt (PyMuPDF)
# 2. Segmentar por orador
python scripts/parse_acta.py data/processed/gc_1201_2026.txt data/processed/camara_2026-07-28_turnos.jsonl
# 3. Crear data/processed/<prefijo>_sesion.json con horas y orden del día (ver el ejemplo de la Cámara)
# 4. Clasificar cada lote con metodologia/prompt_clasificacion.md -> data/processed/clasif/<prefijo>_parteN.jsonl
# 5. Generar el reporte
python scripts/reporte.py camara_2026-07-28
```

## Fuentes
- **Actas oficiales** en la Gaceta del Congreso: transcripción con nombre de cada orador. Se publican
  semanas después de la sesión.
- **Video completo** de cada plenaria en el canal de YouTube Canal Congreso Colombia: tiempos reales.
- **Orden del día** publicado por cada cámara.

## Rutinas automáticas

Corren en macOS con `launchd` y suben sus resultados a GitHub desde la rama `main`. Las definiciones son
plantillas en `scripts/launchd/`; para instalarlas en tu Mac:

```bash
bash scripts/launchd/instalar.sh            # las tres
bash scripts/launchd/instalar.sh detector   # solo una
```

| Cuándo | Script | Qué hace |
|---|---|---|
| Cada 30 min | `descargador_lento.py` | Baja el audio de un video como máximo cada 3 horas, sesiones nuevas primero, y lo transcribe. Ante un bloqueo de YouTube espera 2, 4, 8, 16 y 24 horas, y se detiene tras cinco bloqueos seguidos. |
| Diario, 7:00 | `detectar_sesiones.py` | Agrega al catálogo y a la cola las plenarias nuevas de Canal Congreso y baja los órdenes del día y comunicados nuevos del Senado. |
| Lunes, 6:30 | `corte_semanal.py` | Busca actas nuevas en la Gaceta, regenera los datos del informe, despliega el sitio y deja el resumen en `reportes/semanal/`. La clasificación se activa en `data/rutinas/config.json`. |

Sitio público: https://tiempo-en-plenaria.vercel.app (carpeta `sitio/`).

## Proyectos de referencia
- [EmpoweredVote/on-the-record](https://github.com/EmpoweredVote/on-the-record): transcripción de
  reuniones públicas con atribución de orador (pyannote + faster-whisper + roster, patrones de llamado a
  lista y de la presidencia, y revisión humana bajo 0,70 de confianza). Sin licencia publicada: se toman
  ideas, no código.
- [CouncilDataProject/speakerbox](https://github.com/CouncilDataProject/speakerbox) (MIT):
  identificación de oradores por voz, del proyecto Council Data Project.
- [ParlaCAP](https://arxiv.org/abs/2602.16516v1): clasificación de debates parlamentarios con LLM como
  anotador, con validación contra anotadores humanos. Es el modelo de validación a seguir.
- [kalawinka/cto_analysis](https://github.com/kalawinka/cto_analysis): llamados al orden en el
  Bundestag, como referencia para medir el tono.

## Qué no está en el repositorio

Las clasificaciones del piloto por intervención y por congresista no se publican mientras no pasen la
validación humana (concordancia contra una revisión a ciegas). Se conservan en local y entran al
repositorio cuando la rúbrica esté validada. El sitio sí muestra el resultado agregado del piloto, marcado
como clasificación sin revisión humana.

## Licencia

Código bajo licencia MIT (`LICENSE`). Datos, metodología y textos bajo CC BY 4.0 (`LICENSE-DATOS.md`).

## Estado
Piloto con la plenaria de la Cámara del 28 de julio de 2026 (Acta n.º 3, Gaceta 1201 de 2026).
Las clasificaciones del piloto no han tenido revisión humana.
