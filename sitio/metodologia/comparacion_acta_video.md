# Comparación entre el video y el acta oficial — v0.1

El acta de plenaria es el registro oficial de una sesión, pero es una transcripción editada. Esta
comparación mide qué se dijo en el video que el acta no registra y qué registra el acta que no se
dijo en voz alta.

## Insumos
- Transcripción del audio con marcas de tiempo (`data/descargas/<video_id>/transcripcion.json`).
- Intervenciones del acta segmentadas por orador (`data/processed/<prefijo>_turnos.jsonl`).

## Procedimiento
1. **Alinear.** Se parte cada intervención del acta en frases y se busca cada frase en la
   transcripción por similitud de texto, avanzando siempre hacia adelante en el tiempo. Así cada
   intervención del acta recibe hora de inicio y de fin reales.
2. **Lo que el acta omite.** Tramos de habla en el video sin frase del acta que les corresponda, de
   más de 15 segundos. Cada tramo se clasifica con la rúbrica de pertinencia y se marca su tipo:
   - intervención completa ausente del acta;
   - interrupción o comentario fuera de micrófono;
   - réplica o intercambio entre congresistas;
   - lectura abreviada en el acta («se lee la proposición», sin el texto leído).
3. **Lo que el acta agrega.** Texto del acta que no aparece en el audio: documentos insertados
   (proposiciones, constancias, conceptos) y registros de votación. No se cuenta como tiempo de habla.
4. **Lo que el acta cambia.** Frases alineadas con diferencias de fondo: cambio de cifras, nombres o
   sentido. Las correcciones de estilo no cuentan.

## Indicadores
- Minutos de habla en el video sin registro en el acta, por sesión y por tipo.
- Porcentaje del texto del acta que es documento insertado y no habla.
- Número de cambios de fondo entre lo dicho y lo registrado, cada uno con su minuto de video y su
  página del acta.

## Cuidado al publicar
El acta puede omitir algo por razones legítimas: audio inaudible, intervenciones sin micrófono que la
Secretaría no alcanza a registrar. Se publica el dato con las dos evidencias (minuto del video y
página del acta) y sin atribuir intención a quien elaboró el acta.
