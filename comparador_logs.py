# ------------------------------------------------------------------------------------
# Pontificia Universidad Católica de Chile
# Escuela de Ingeniería — Departamento de Ciencia de la Computación
# Curso: IIC2523 - Sistemas Distribuidos
# Evaluación: Tarea 2 - Simulación de algoritmos de consenso (Paxos y Raft)
#
# Archivo: comparador_logs.py
# Autor: Larry Andrés Uribe Araya
#
# ------------------------------------------------------------------------------------
# Declaración de uso de herramientas generativas (política oficial de IA)
# ------------------------------------------------------------------------------------
# Este archivo fue desarrollado con asistencia de ChatGPT (GPT-5, OpenAI),
# revisado y modificado críticamente por el autor antes de su inclusión en
# la entrega, conforme a las políticas establecidas en el Syllabus del curso
# IIC2523 y al Código de Honor de la Pontificia Universidad Católica de Chile.
# Referencia oficial: https://github.com/IIC2523-UC/Syllabus-2025-2/discussions
# ------------------------------------------------------------------------------------

"""
comparador_logs.py

Compara las salidas generadas por tu simulador (en `logs/`) con las salidas esperadas
del profesor (en `logs_esperados/`). Muestra un resumen del porcentaje de coincidencia
línea a línea y destaca diferencias.

Uso:
    python3 comparador_logs.py
    python3 comparador_logs.py Paxos
    python3 comparador_logs.py Raft
"""

from __future__ import annotations
import os
import sys
import difflib

# ------------------------------------------------------------------------------------
# Bloque guiado con asistencia de ChatGPT (GPT-5, OpenAI)
# ------------------------------------------------------------------------------------


def read_file(path: str) -> list[str]:
    """Lee un archivo en UTF-8 y devuelve sus líneas sin saltos."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [x.rstrip("\n") for x in f]
    except FileNotFoundError:
        return []


def compare_files(path1: str, path2: str) -> tuple[float, list[str]]:
    """
    Compara dos archivos línea por línea.
    Retorna (porcentaje_coincidencia, diferencias_formateadas)
    """
    lines1 = read_file(path1)
    lines2 = read_file(path2)

    if not lines1 and not lines2:
        return 100.0, ["(Ambos vacíos)"]

    sm = difflib.SequenceMatcher(None, lines1, lines2)
    ratio = sm.ratio() * 100

    diff = list(
        difflib.unified_diff(
            lines2,
            lines1,
            fromfile="esperado",
            tofile="generado",
            lineterm="",
        )
    )

    return ratio, diff


def compare_directories(generated_dir: str, expected_dir: str, prefix_filter: str = "") -> None:
    """
    Compara todos los archivos con el mismo nombre en `generated_dir` y `expected_dir`.
    Si `prefix_filter` es "Paxos" o "Raft", solo compara esos archivos.
    """
    gen_files = [f for f in os.listdir(generated_dir) if f.endswith(".txt")]
    if prefix_filter:
        gen_files = [f for f in gen_files if f.startswith(prefix_filter)]

    if not gen_files:
        print("❌ No se encontraron archivos en", generated_dir)
        return

    total = 0
    correct = 0
    print("────────────────────────────────────────────────────────────")
    print(f" Comparando archivos en '{generated_dir}' vs '{expected_dir}'")
    print("────────────────────────────────────────────────────────────")

    for fname in sorted(gen_files):
        gen_path = os.path.join(generated_dir, fname)
        exp_path = os.path.join(expected_dir, fname)

        if not os.path.exists(exp_path):
            print(f"⚠️  No existe esperado para: {fname}")
            continue

        total += 1
        ratio, diff = compare_files(gen_path, exp_path)

        if ratio == 100.0:
            correct += 1
            print(f"✅ {fname}: {ratio:.1f}% OK")
        else:
            print(f"❌ {fname}: {ratio:.1f}% coincidencia")
            for line in diff[:10]:  # muestra solo las primeras diferencias
                print("   ", line)
            if len(diff) > 10:
                print("   ... (diferencias truncadas)")

    print("────────────────────────────────────────────────────────────")
    if total > 0:
        pct = 100 * correct / total
        print(f"Resumen: {correct}/{total} correctos ({pct:.1f}%)")
    else:
        print("No se encontraron archivos para comparar.")


def main(argv: list[str]) -> int:
    prefix = argv[1] if len(argv) >= 2 else ""
    compare_directories("logs", "logs_esperados", prefix_filter=prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
