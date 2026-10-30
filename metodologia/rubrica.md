# Rúbrica de clasificación del tiempo en plenaria — v0.1

Esta rúbrica es pública. Cualquiera puede aplicarla a la misma fuente y debería llegar al mismo resultado.
Si no llega, la rúbrica está mal y se corrige: la versión va en el nombre y cada cambio queda registrado.

## Pregunta que responde

¿Qué parte del tiempo de una sesión plenaria se dedica a las funciones que la ley le asigna al
Congreso, qué parte a procedimiento, qué parte a intervenciones que no tratan el asunto en discusión
y qué parte se pierde sin sesionar?

No mide si una postura es buena o mala, ni si un proyecto conviene. Mide **uso del tiempo** y
**pertinencia**: si lo que se dice trata el punto del orden del día que está en discusión.

## Unidad de análisis

Cada **intervención**: un turno de palabra de un orador, tal como lo registra el acta oficial
(«Intervención del Representante…», «Dirección de Presidencia…», «Secretario General…»).
Si la fuente es el video, la unidad es el mismo turno delimitado por marcas de tiempo.

## Bloques

### 1. Trabajo misional
La intervención ejerce una de las funciones del **Art. 6 de la Ley 5 de 1992**:

| Código | Función | Ejemplos en plenaria |
|---|---|---|
| `constituyente` | Reformar la Constitución por acto legislativo | Debate o votación de un acto legislativo |
| `legislativa` | Elaborar, reformar o derogar leyes | Ponencias, debate del articulado, proposiciones de modificación, votación de un proyecto |
| `control_politico` | Citar y emplazar a ministros y autoridades | Debate de control político, cuestionario a un ministro, moción de censura u observaciones |
| `judicial` | Juzgar excepcionalmente a altos funcionarios | Trámite de acusaciones |
| `electoral` | Elegir funcionarios (Contralor, Procurador, magistrados, etc.) | Postulación, debate y votación de una elección |
| `administrativa` | Organizar el Congreso | Conformación de comisiones, mesas directivas, traslado de sede |
| `control_publico` | Emplazar a particulares a declarar | Citación de particulares |
| `protocolo` | Recibir a jefes de Estado o de Gobierno | Sesión solemne de recepción |

El tono no cambia el bloque. Un debate duro sobre el articulado es trabajo misional.

### 2. Procedimiento
Trámite reglamentario necesario para que la sesión funcione, pero que no es en sí una función:
llamado a lista y registro, verificación de quórum, lectura y aprobación del orden del día y de actas,
anuncio de proyectos, lectura de proposiciones por Secretaría, apertura y cierre de votaciones,
publicación de registros de votación, concesión del uso de la palabra, mociones de orden y de
procedimiento que el Reglamento prevé, himno nacional.

### 3. No pertinente
La intervención no trata el punto del orden del día que está en discusión en ese momento. Subtipos:

| Código | Qué es |
|---|---|
| `fuera_de_tema` | Habla de un asunto distinto al punto en discusión (otro proyecto, coyuntura, región) sin conectarlo con lo que se decide |
| `alusiones_replicas` | Respuesta a una mención personal o réplica entre congresistas que no avanza la decisión |
| `confrontacion` | Ataques personales o partidistas sin argumento sobre el asunto en discusión |
| `cortesias` | Saludos, felicitaciones, cumpleaños, homenajes y agradecimientos que no están en el orden del día |
| `desorden` | Llamados al orden por ruido, intervenciones sin micrófono, discusiones sobre quién tiene la palabra |

Una intervención que mezcla contenido pertinente y no pertinente se clasifica por **lo que predomina**
y se marca `mixta: true`.

### 4. Tiempo muerto
Tiempo en que la plenaria no sesiona:
- **Espera inicial:** de la hora de citación a la hora real de inicio.
- **Recesos y suspensiones.**
- **Fallas técnicas y esperas de quórum** a mitad de la sesión.

Se mide con las horas que registra el acta o con el reloj del video, no con el texto.

## Reglas de desempate
1. Las intervenciones de la Presidencia y de la Secretaría que **conducen** la sesión son `procedimiento`.
   Si la Presidencia opina sobre el fondo de un asunto, se clasifica como cualquier otra intervención.
2. Una proposición se clasifica según **lo que propone**. Por ejemplo, una proposición de debate de
   control político va en `control_politico` y una de conformación de comisiones en `administrativa`.
   Su sola lectura por Secretaría es `procedimiento`.
3. Si un congresista explica su voto sobre el punto en discusión, es `misional`.
4. Ante la duda entre misional y no pertinente, se clasifica como `misional` con `confianza: baja`.
   La auditoría debe errar a favor del congresista.

## Campos que se registran por intervención

```
id, orador, rol, partido (si se conoce), punto_orden_dia, bloque, funcion | subtipo,
tema, mixta, confianza (alta|media|baja), evidencia (cita textual de máx. 25 palabras),
palabras, minutos_estimados | inicio/fin (video)
```

## Cálculo del tiempo
- **Con video:** marcas de tiempo reales de cada intervención.
- **Solo con acta:** minutos ≈ palabras ÷ 140 (ritmo típico de discurso en español). El tiempo de la
  sesión que no se explica por habla (votaciones, esperas, recesos) se reporta aparte como
  «tiempo sin habla registrada». Toda cifra estimada se marca como estimación.

## Indicadores
- **Puntualidad:** hora de citación, apertura del registro, quórum e inicio.
- **% del tiempo por bloque** y por función del Art. 6.
- **% de intervenciones pertinentes** por congresista y por partido, con número de intervenciones.
  Con menos de 3 intervenciones no se publica porcentaje individual.
- **Asuntos evacuados** vs. asuntos del orden del día.

## Principios de publicación
- Cada cifra enlaza a su fuente: página del acta o minuto del video.
- No se usan calificativos sobre personas. Se publica el dato y la evidencia.
- Cualquier congresista o ciudadano puede pedir revisión de una clasificación. Si se acepta, se
  corrige y queda registrada.
