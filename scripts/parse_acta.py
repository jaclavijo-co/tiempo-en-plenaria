"""Segmenta un acta de plenaria (texto extraído de la Gaceta del Congreso) en intervenciones.

Uso:
  python scripts/parse_acta.py <gaceta.txt> <salida.jsonl> --desde "A C TA S" --hasta "PROPOSICIONES"

Cada línea de salida es una intervención: orador, rol, página de la Gaceta, texto y palabras.
"""
import argparse
import json
import re

MARCA_PAGINA = re.compile(r"^=====PAGINA (\d+)=====$")
ENCABEZADO_PAGINA = re.compile(
    r"^(Página \d+|Gaceta del Congreso\s+\d+|"
    r"(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo), \d{1,2} de \w+ de \d{4})$"
)

# Las actas a veces omiten la coma entre el cargo de congresista y el nombre
ROL_CONGRESO = (
    r"Intervención (?:del|de la) (?:honorable )?"
    r"(?:Representante(?: a la Cámara)?|Senadora?(?: de la República)?)"
)
ROL_OTRO = (
    r"Dirección de (?:Presidencia|presidencia|Vicepresidencia)"
    r"|Secretari[oa] General|Subsecretari[oa] General"
    r"|Intervención (?:del|de la) [^,:.]{3,80}?"
)
TOKEN = r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñü’'\-]+"
NOMBRE = rf"(?P<nombre>{TOKEN}(?:\s+(?:de|del|la|las|los|y|{TOKEN})){{1,6}})"
ENCABEZADO = re.compile(
    rf"(?:(?P<rol>{ROL_CONGRESO})\s*[,.]?\s*|(?P<rol_otro>{ROL_OTRO})\s*[,.]\s*){NOMBRE}\s*[:.](?=\s)"
)
SENTINELA = re.compile(r"⟦P(\d+)⟧")


def rol_de(cargo: str) -> str:
    c = cargo.lower()
    if "presidencia" in c:
        return "presidencia"
    if "secretari" in c:
        return "secretaria"
    if "representante" in c or "senador" in c:
        return "congresista"
    if "ministr" in c or "viceministr" in c or "gobierno" in c:
        return "gobierno"
    return "otro"


def cargar_cuerpo(ruta: str, desde: str, hasta: str) -> str:
    lineas = open(ruta, encoding="utf-8").read().splitlines()
    inicio = next(i for i, l in enumerate(lineas) if l.strip().startswith(desde))
    # el acta termina en el primer anexo que aparece después del cierre de la sesión
    cierre = next(i for i, l in enumerate(lineas) if i > inicio and "Se levanta la sesión" in l)
    fin = next(i for i, l in enumerate(lineas) if i > cierre and l.strip() == hasta)
    pagina = max(int(m.group(1)) for l in lineas[: inicio + 1] if (m := MARCA_PAGINA.match(l.strip())))
    partes = [f"⟦P{pagina}⟧"]
    for l in lineas[inicio:fin]:
        s = l.strip()
        if m := MARCA_PAGINA.match(s):
            partes.append(f"⟦P{m.group(1)}⟧")
        elif s and not ENCABEZADO_PAGINA.match(s):
            partes.append(s)
    return re.sub(r"\s+", " ", " ".join(partes))


def segmentar(cuerpo: str):
    # los nombres en mayúsculas son firmas del orden del día, no turnos de palabra
    encabezados = [m for m in ENCABEZADO.finditer(cuerpo) if not m.group("nombre").isupper()]
    preambulo = cuerpo[: encabezados[0].start()]
    yield {"orador": "(Acta)", "cargo": "Preámbulo del acta", "rol": "acta", "texto": preambulo}
    for i, m in enumerate(encabezados):
        fin = encabezados[i + 1].start() if i + 1 < len(encabezados) else len(cuerpo)
        cargo = (m.group("rol") or m.group("rol_otro")).strip()
        yield {
            "orador": m.group("nombre").strip(),
            "cargo": cargo,
            "rol": rol_de(cargo),
            "texto": cuerpo[m.end() : fin],
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--desde", default="A C TA S")
    ap.add_argument("--hasta", default="PROPOSICIONES")
    args = ap.parse_args()

    cuerpo = cargar_cuerpo(args.entrada, args.desde, args.hasta)
    pagina = int(SENTINELA.search(cuerpo).group(1))
    n = 0
    with open(args.salida, "w", encoding="utf-8") as f:
        for n, turno in enumerate(segmentar(cuerpo), start=1):
            paginas = [int(p) for p in SENTINELA.findall(turno["texto"])]
            texto = SENTINELA.sub(" ", turno.pop("texto"))
            texto = re.sub(r"\s+", " ", texto).strip()
            turno.update(id=n, pagina=pagina, texto=texto, palabras=len(texto.split()))
            f.write(json.dumps(turno, ensure_ascii=False) + "\n")
            if paginas:
                pagina = paginas[-1]
    print(f"{n} intervenciones -> {args.salida}")


if __name__ == "__main__":
    main()
