# 🧠 IIC2523 — Tarea 2: Simulación de algoritmos de consenso (Paxos y Raft)

**Autor:** Larry Andrés Uribe Araya  
**Curso:** IIC2523 – Sistemas Distribuidos  
**Semestre:** 2025-2  
**Lenguaje:** Python 3.8.10  
**Fecha de entrega:** Octubre 2025

---

## 📘 Descripción general

Esta tarea implementa **dos algoritmos de consenso distribuidos** — **Paxos** y **Raft** — mediante simulaciones discretas en Python.  
Cada simulador permite ejecutar escenarios definidos en archivos de texto (`test_XX.txt`) que especifican acciones entre nodos, fallos y elecciones de líderes.

El objetivo es modelar el comportamiento de sistemas distribuidos que buscan **acordar un mismo estado final** entre varios nodos, incluso ante fallos o desconexiones parciales.

---

## 🧩 Archivos del proyecto

| Archivo | Descripción |
|----------|--------------|
| `paxos.py` | Implementa la simulación del algoritmo **Paxos**, incluyendo la coordinación entre Proposers, Acceptors y Learners. |
| `database1.py` | Contiene la clase `Database` utilizada por **Paxos**, con soporte para operaciones simples (`SET`, `ADD`, `DEL`). |
| `raft.py` | Implementa el algoritmo **Raft**, incluyendo elecciones de líder, replicación de logs, y reconstrucción del estado comprometido. |
| `database2.py` | Base de datos simplificada para **Raft**, con el mismo conjunto de operaciones y manejo interno de claves normalizadas. |


## ⚙️ Ejecución

Para correr todos los tests:

```bash
"python main.py [Paxos|Raft] <ruta_caso>" 
```




Los resultados se almacenan automáticamente en el directorio `logs/` 

---

## 🧩 Estructura de las acciones

Ambos módulos (`database1.py` y `database2.py`) interpretan instrucciones con el formato:

| Acción | Descripción | Ejemplo |
|--------|--------------|----------|
| `SET-clave-valor` | Asigna un valor a una variable. | `SET-criminal-vecino de la víctima` |
| `ADD-clave-valor` | Concatena o suma valores. | `ADD-crimen-por romance fallido` |
| `DEL-clave` | Elimina una variable existente. | `DEL-arma homicida` |

---

## 🧩 Lógica de consenso (resumen conceptual)

**Paxos**  
- Utiliza fases de *prepare* y *accept* para alcanzar consenso entre múltiples propuestas.  
- Cada valor propuesto debe ser aceptado por una mayoría de nodos antes de aplicarse en la base de datos.  
- `database1.py` mantiene el estado final acordado.

**Raft**  
- Divide el consenso en pasos claros: *elección de líder*, *replicación de logs* y *compromiso de entradas*.  
- En caso de fallas, los nuevos líderes reconstruyen un log común basado en mayoría.  
- `database2.py` aplica secuencialmente las acciones comprometidas, asegurando consistencia global.

---

## 💻 Requisitos

- Python **3.8.10**  
- No se requieren librerías externas.

---

## 📚 Resultados esperados

Los tests automáticos verifican:
- la **consistencia de los logs** en todos los nodos,  
- la **coherencia de los datos en la base de datos final**, y  
- la **ausencia de datos adicionales** no comprometidos.

Los resultados exitosos se reportan como:

```
✅ Paxos_test_01.txt: 100.0% OK
✅ Raft_test_04.txt: 100.0% OK
...
```

---

## 🤖 Uso de herramientas de Inteligencia Artificial

Durante el desarrollo de esta tarea se utilizó **ChatGPT (modelo GPT-5, OpenAI)** como **asistente de apoyo técnico**, únicamente para:

- depurar errores de sintaxis y lógica,  
- revisar la coherencia del pseudocódigo del consenso,  
- y redactar documentación técnica (README y comentarios de depuración).

**Todas las decisiones de diseño, implementación y depuración final fueron realizadas por el autor.**  
La herramienta de IA no escribió el código base de los algoritmos ni reemplazó la comprensión o justificación teórica de Paxos o Raft.

Esta colaboración cumple con las **políticas de integridad académica de la Escuela de Ingeniería UC**, citando explícitamente el uso de IA como apoyo técnico y documental.

---
