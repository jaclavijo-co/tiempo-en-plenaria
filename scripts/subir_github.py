"""Sube a GitHub lo que haya cambiado en el proyecto. Lo usan las rutinas automáticas.

Uso: python scripts/subir_github.py "Mensaje del commit"
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)


def subir(mensaje: str) -> str:
    rama = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if rama != "main":
        return f"la carpeta está en la rama {rama}; las rutinas solo suben desde main"
    git("add", "-A")
    if git("diff", "--cached", "--quiet").returncode == 0:
        return "sin cambios"
    commit = git("commit", "-m", mensaje)
    if commit.returncode != 0:
        return "commit falló: " + commit.stderr.strip()[-200:]
    # otros colaboradores pueden haber subido cambios: se integran antes de subir
    traer = git("pull", "--rebase", "--autostash", "origin", "main")
    if traer.returncode != 0:
        git("rebase", "--abort")
        return "no se pudo integrar con GitHub: " + traer.stderr.strip()[-200:]
    empuje = git("push", "origin", "HEAD:main")
    return "subido" if empuje.returncode == 0 else "push falló: " + empuje.stderr.strip()[-200:]


if __name__ == "__main__":
    print(subir(sys.argv[1]))
