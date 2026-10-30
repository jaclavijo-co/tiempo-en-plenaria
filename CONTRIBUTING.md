# Cómo colaborar

Este proyecto mide cómo usa el tiempo el Congreso de Colombia en sus plenarias, con fuentes oficiales y
método abierto. Cualquier ciudadano puede revisar, corregir o construir sobre él.

## Principios

- **Toda cifra tiene evidencia.** Cada dato enlaza al documento oficial (página del acta, orden del día) o
  al minuto del video de donde sale.
- **Se describe, no se califica.** Nada de adjetivos sobre congresistas o partidos. Se publica el dato y su
  fuente.
- **Misma regla para todos.** La rúbrica se aplica igual a todos los partidos. Ante la duda, se clasifica a
  favor del congresista.
- **Solo información pública del ejercicio del cargo.** No se recogen datos personales que no estén en
  documentos oficiales o en las transmisiones públicas.

## Formas de colaborar

| Quiero… | Qué hacer |
|---|---|
| Reportar una cifra o clasificación equivocada | Abre un *issue* con el id de la intervención, la página del acta o el minuto del video, y por qué crees que está mal. |
| Proponer un cambio a la rúbrica | Abre un *issue* con la regla actual, la regla propuesta y al menos dos intervenciones reales donde cambia el resultado. Los cambios se versionan (v0.1, v0.2…). |
| Revisar clasificaciones a mano | Pide una muestra de validación. La revisión es a ciegas: clasificas sin ver lo que dijo el modelo. |
| Agregar una fuente | Por ejemplo, los órdenes del día de la Cámara. Abre un *pull request* con el script que la descarga y una muestra del resultado. |
| Hacer un análisis complementario | Los datos están en `publicacion/` y en el sitio (CSV), descritos en `DICCIONARIO-DE-DATOS.md`. Cita la fuente y la fecha de corte. |
| Conectar otro proyecto ciudadano | Cuéntalo en *Discussions*: qué datos tienen y cuál sería la llave común (sesión, proyecto de ley, video o gaceta). |

## Cómo trabajar en el repositorio

- Trabaja en una rama y abre un *pull request* hacia `main`. Las rutinas automáticas suben a `main`, así que
  no escribas a mano en lo que ellas generan: `data/catalogo/`, `data/descargas/`, `publicacion/`,
  `sitio/datos/` y `reportes/semanal/`. Si algo ahí está mal, corrige el script que lo produce.
- No subas audios ni PDF completos: se vuelven a descargar de su fuente oficial (ver `.gitignore`).
- Nunca subas llaves, contraseñas ni *cookies*.
- Las descargas de YouTube van de a un video, con pausas largas y sin cuentas ni trucos para saltar sus
  controles (`scripts/descargador_lento.py`). Una contribución que cambie eso no se acepta.

## Montaje

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
```

El `README.md` explica la estructura, los scripts y las rutinas automáticas.

Para correr las rutinas automáticas en tu Mac: `bash scripts/launchd/instalar.sh`.

## Licencia

Al contribuir aceptas que tu código se publique bajo la licencia MIT (`LICENSE`) y tus datos, análisis y
textos bajo CC BY 4.0 (`LICENSE-DATOS.md`).
