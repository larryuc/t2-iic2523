import subprocess
import os

COMANDO_PYTHON = "python3"


def ejecutar_tests(modo, ruta_entrada, mostrar_prints, tiempo_maximo):
    if mostrar_prints:
        subprocess.run([COMANDO_PYTHON, "main.py", modo, ruta_entrada], timeout=tiempo_maximo)
    else:
        subprocess.run(
            [COMANDO_PYTHON, "main.py", modo, ruta_entrada],
            timeout=tiempo_maximo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def leer_archivo(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [linea.strip() for linea in f.readlines() if linea.strip() != ""]


def verificar_tests(modo, test):
    archivo_referencia = leer_archivo(os.path.join("logs_esperados", f"{modo}_{test}"))

    try:
        archivo_alumno = leer_archivo(os.path.join("logs", f"{modo}_{test}"))
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo de logs para {modo} {test}")
        return

    index_base_datos_referencia = archivo_referencia.index("BASE DE DATOS")
    index_base_datos_alumno = archivo_alumno.index("BASE DE DATOS")

    print(f"Verificando {modo} -- {test}...")

    correctos_logs = 0
    if index_base_datos_referencia != index_base_datos_alumno:
        print("  ⚠️ Alerta ⚠️ - La sección de Logs no es del mismo tamaño que la de solución")
    for i in range(1, index_base_datos_referencia):
        if i >= len(archivo_alumno):
            print("  ❌ Faltan líneas en el log, se deja de verificar esta parte")
            break

        if archivo_alumno[i] != archivo_referencia[i]:
            print(f"  ❌ Error en línea {i+1}:")
            print(f"       Esperado en la solución: {archivo_referencia[i]}")
            print(f"       Encontrado en la entrega: {archivo_alumno[i]}")
            continue
        correctos_logs += 1

    set_db_alumno = set(archivo_alumno[index_base_datos_alumno+1:])
    set_db_referencia = set(archivo_referencia[index_base_datos_referencia+1:])

    # Ver cuantos datos correctos del alumno están en la base de datos
    # Descontar si el aluno tiene más datos que la solución
    datos_extras = max(0, len(set_db_alumno) - len(set_db_referencia))
    correctos_db = len(set_db_alumno.intersection(set_db_referencia))

    if datos_extras > 0:
        print("  ❌ Alerta - La base de datos del estudiante tiene más datos de lo esperado")

    print(f"  Resultados para {modo} {test}:")
    print(f"  -- Logs correctos: {correctos_logs}/{index_base_datos_referencia - 1}")
    print(f"  -- Datos de la BD correctos: {correctos_db}/{len(set_db_referencia)}")
    print(f"  -- Datos extras en la BD del estudiante: {datos_extras}")

    puntaje_esperado = len(archivo_referencia) - 2
    puntaje_final = max(correctos_logs + correctos_db - datos_extras, 0)
    print(f"  => Puntaje final para {modo} {test}: {puntaje_final} de {puntaje_esperado}")
    print("")


if __name__ == "__main__":
    tests_paxos = [x for x in os.listdir("casos_Paxos") if x.endswith(".txt")]
    tests_raft = [x for x in os.listdir("casos_Raft") if x.endswith(".txt")]

    mostrar_prints = True
    for test in tests_paxos:
        ejecutar_tests(
            modo="Paxos",
            ruta_entrada=os.path.join("casos_Paxos", test),
            mostrar_prints=mostrar_prints,
            tiempo_maximo=1,
        )
        verificar_tests(modo="Paxos", test=test)

    for test in tests_raft:
        ejecutar_tests(
            modo="Raft",
            ruta_entrada=os.path.join("casos_Raft", test),
            mostrar_prints=mostrar_prints,
            tiempo_maximo=1,
        )
        verificar_tests(modo="Raft", test=test)
    print("¡Tests finalizados!")
