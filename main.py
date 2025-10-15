# ------------------------------------------------------------------------------------
# Pontificia Universidad Católica de Chile
# Escuela de Ingeniería — Departamento de Ciencia de la Computación
# Curso: IIC2523 - Sistemas Distribuidos
# Evaluación: Tarea 2 - Simulación de algoritmos de consenso (Paxos y Raft)
#
# Archivo: main.py
# Autor: Larry Andrés Uribe Araya
# ------------------------------------------------------------------------------------

from sys import argv
from paxos import PaxosSimulator
from raft import RaftSimulator
import os

if __name__ == "__main__":
    if len(argv) < 3:
        print("Uso: python main.py [Paxos|Raft] <ruta_caso>")
        exit(1)

    modo = argv[1]
    path = argv[2]

    if modo == "Paxos":
        sim = PaxosSimulator(path)
    elif modo == "Raft":
        sim = RaftSimulator(path)
    else:
        print("Modo no reconocido. Usa 'Paxos' o 'Raft'.")
        exit(1)

    salida, estado = sim.run()

    # Escribir archivo de logs en carpeta logs/
    nombre_archivo = f"logs/{modo}_{path.split(os.sep)[-1]}"
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write("LOGS\n")

        # Si no hubo líneas de log, se agrega la línea requerida
        if not salida:
            f.write("No hubo logs\n")
        else:
            for linea in salida:
                f.write(linea + "\n")

        f.write("BASE DE DATOS\n")

        # Si la base de datos está vacía, imprimir la línea requerida
        if not estado:
            f.write("No hay datos\n")
        else:
            for clave, valor in estado.items():
                f.write(f"{clave}={valor}\n")
