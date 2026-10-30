#!/bin/bash
# Instala o reinstala las rutinas automáticas del proyecto en el Mac de quien lo ejecuta.
# Uso: bash scripts/launchd/instalar.sh [descargador] [detector] [semanal]   (sin argumentos: las tres)
# Para quitarlas: launchctl bootout gui/$(id -u)/personal.auditoria-plenarias.<nombre>
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
DESTINO="$HOME/Library/LaunchAgents"
rutinas=("$@")
[ ${#rutinas[@]} -eq 0 ] && rutinas=(descargador detector semanal)
mkdir -p "$DESTINO" "$RAIZ/data/rutinas" "$RAIZ/data/descargas"
for n in "${rutinas[@]}"; do
  etiqueta="personal.auditoria-plenarias.$n"
  sed -e "s#__RAIZ__#$RAIZ#g" -e "s#__HOME__#$HOME#g" "$RAIZ/scripts/launchd/$etiqueta.plist" > "$DESTINO/$etiqueta.plist"
  launchctl bootout "gui/$(id -u)/$etiqueta" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$DESTINO/$etiqueta.plist"
  echo "instalada: $n"
done
