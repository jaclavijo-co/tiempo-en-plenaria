# Diccionario de datos

Qué contiene cada archivo de datos del proyecto y qué significa cada campo. Las fechas van en formato
ISO (`AAAA-MM-DD`) y hora de Colombia. Los archivos los generan los scripts y las rutinas: si encuentras un
error, corrige el script, no el archivo.

Para cruzar con otros datos, las llaves estables son:
- **Sesión:** `camara` + `fecha` (una plenaria por cámara y día; las sesiones de Congreso pleno van aparte).
- **Video:** `video_id` de YouTube (Canal Congreso Colombia).
- **Proyecto de ley:** `id` con el formato `PL 061/2025 S` o `PAL 012/2025 S` (tipo, número/año, cámara de radicación).
- **Acta:** número de `gaceta` del Congreso de 2026.

## Datos del informe (`publicacion/`, copiados en `sitio/datos/`)

### `sesiones.csv`: una fila por plenaria
| Campo | Qué es |
|---|---|
| `camara` | `Senado` o `Cámara` |
| `fecha` | Fecha de la sesión |
| `tipo` | `plenaria`, `oposicion` (sesión del estatuto de la oposición) o `congreso_pleno` |
| `estado` | `realizada` (hay video completo en Canal Congreso), `aplazada` (según comunicado oficial) o `sin_video` |
| `hora_citacion` | Hora a la que se citó, tomada del orden del día oficial. Solo Senado |
| `proyectos_agendados` | Proyectos en el orden del día de esa sesión. Solo Senado |
| `video_min` | Minutos de transmisión (suma de las partes si hubo varias) |
| `acta` | `sí` si su acta ya apareció publicada en la Gaceta del Congreso; si no, `no` |
| `gaceta` | Número de la Gaceta del Congreso de 2026 que publica el acta |
| `publicada` | Fecha de esa Gaceta |
| `rezago_dias` | Días entre la sesión y la publicación del acta |
| `nota` | Motivo de un aplazamiento o cambio de hora, citando el comunicado de la Secretaría General del Senado |

### `agenda_senado.csv`: una fila por proyecto agendado en la plenaria del Senado
| Campo | Qué es |
|---|---|
| `id` | Identificador del proyecto (ver llaves arriba) |
| `titulo` | Título oficial tal como aparece en el orden del día |
| `veces` | Órdenes del día de plenaria del Senado, hasta la fecha de corte, en los que aparece |
| `primera`, `ultima` | Fechas de la primera y la última aparición |

Que un proyecto deje de aparecer no dice por qué: pudo aprobarse, archivarse o retirarse. Eso se confirma en las actas.

### `piloto_camara_2026-07-28.csv`: uso del tiempo en la plenaria piloto
| Campo | Qué es |
|---|---|
| `tramo` | `espera` (de la citación a la apertura del registro), `misional`, `procedimiento`, `no_pertinente` (bloques de la rúbrica), `sin_habla` (tiempo en sesión que el texto del acta no explica) y `retraso_inicio` (de la citación al inicio formal; no se suma a los demás) |
| `minutos` | Minutos estimados a partir del acta (palabras ÷ 140) |

Clasificación hecha por un modelo de lenguaje con la rúbrica v0.1, todavía sin validación humana.

### `corte.csv`: fechas de corte del informe
| Campo | Qué es |
|---|---|
| `inicio` | Inicio del período (instalación del Congreso, 2026-07-20) |
| `fin` | Última plenaria transmitida que está en el catálogo |
| `gaceta_hasta` | Fecha de la Gaceta más reciente revisada |
| `gaceta_num_max` | Número de la Gaceta más reciente revisada |
| `actualizado` | Día en que se generaron los datos |

## Catálogos (`data/catalogo/`)

### `plenarias.csv`: videos de plenarias en Canal Congreso
`camara`, `fecha`, `video_id`, `duracion_min`, `titulo` (título original del video). Crece cada día con el detector.

### `gacetas_2026.jsonl`: índice de cada número de la Gaceta del Congreso de 2026
Una línea JSON por número revisado.

| Campo | Qué es |
|---|---|
| `gaceta` | Número |
| `entidad` | `Senado` o `Cámara`, según el encabezado |
| `fecha_publicacion` | Fecha del número |
| `tiene_actas_de_plenaria` | Si el índice anuncia actas de plenaria |
| `actas` | Lista de actas detectadas: `numero`, `fecha_sesion`, `plenaria` (verdadero si es de plenaria y no de comisión) y `contexto` (texto del índice) |
| `indice` | Primeros 4.000 caracteres del texto de la primera página |
| `error` | Si el número no se pudo leer (por ejemplo, un PDF no optimizado para web) |

Los números que todavía no están en la copia pública consultada no se registran: se vuelven a buscar cada lunes.

## Datos procesados (`data/processed/`)

### `senado_ordenes_del_dia.json`
- `sesiones`: una entrada por orden del día del Senado, con `fecha`, `tipo`, `documento` (archivo en
  `data/raw/orden_del_dia_senado/`), `hora_citacion`, `proyectos` (`id`, `camara` de origen si viene de la
  Cámara, `titulo`), `menciones_control_politico` y `video` (videos del catálogo de esa fecha). El campo
  `aplazada` está en desuso; los aplazamientos están en `publicacion/sesiones.csv`.
- `proyectos`: cada proyecto con `veces_en_orden_del_dia` (todas las sesiones, incluidas las convocadas
  después de la fecha de corte), `primera` y `ultima`.
- `fechas_sin_orden_del_dia`: fechas con video del Senado sin orden del día publicado.

### `<cámara>_<fecha>_turnos.jsonl`: acta segmentada por orador
Una línea por intervención: `id` (orden en el acta), `orador`, `cargo` (como lo escribe el acta), `rol`
(`congresista`, `presidencia`, `secretaria`, `gobierno`, `otro` o `acta` para el preámbulo), `pagina` (de la
Gaceta), `texto` y `palabras`.

## Video y transcripción (`data/descargas/`)

- `cola.csv`: `orden`, `camara`, `fecha`, `video_id`, `duracion_min` y `estado` (`pendiente`, `descargado`,
  `transcrito` o `error`).
- `estado.json`: estado del descargador (`proximo_intento`, `bloqueos_seguidos`, `detenido`).
- `<video_id>/transcripcion.json`: `video_id`, `modelo` (Whisper usado) y `segmentos` con `inicio` y `fin`
  en segundos desde el comienzo del video, y `texto`.
- `<video_id>/audio.*` no se publica: se descarga de nuevo desde YouTube si hace falta.

## Fuentes originales (`data/raw/`)

PDF de los órdenes del día y comunicados de la Secretaría General del Senado, tal como se descargaron. Los
PDF completos de la Gaceta no se guardan; se consultan por su número.
