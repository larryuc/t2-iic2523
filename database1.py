# ------------------------------------------------------------------------------------
# Pontificia Universidad Católica de Chile
# Escuela de Ingeniería — Departamento de Ciencia de la Computación
# Curso: IIC2523 - Sistemas Distribuidos
# Evaluación: Tarea 2 - Simulación de algoritmos de consenso (Paxos y Raft)
#
# Archivo: database.py
# Autor: Larry Andrés Uribe Araya
#
# ------------------------------------------------------------------------------------
# Declaración de uso de herramientas generativas (política oficial de IA)
# ------------------------------------------------------------------------------------
# Parte del presente código fue desarrollado con asistencia de ChatGPT (GPT-5, OpenAI).
# El código fue revisado, modificado y validado críticamente por el autor antes de su
# inclusión en esta entrega, conforme a las políticas establecidas en el Syllabus del
# curso IIC2523 y al Código de Honor de la Pontificia Universidad Católica de Chile.
# Referencia oficial: https://github.com/IIC2523-UC/Syllabus-2025-2/discussions
#
# Cumple con:
# - Citación explícita del uso de IA (Sección 7 del enunciado)
# - Análisis crítico del código (Sección 10 del enunciado)
# - Restricciones formales (PEP8, ≤100 caracteres por línea, ≤400 líneas por archivo)
# ------------------------------------------------------------------------------------

"""
database.py

Implementa la base de datos de acciones SET, ADD y DEL para la T2 IIC2523.
Incluye el método apply_action() para interpretar comandos de la forma
COMANDO-VARIABLE-VALOR, según las reglas del enunciado oficial.

Reglas:
- ADD intenta sumar enteros si ambos valores son .isdigit()
- Si no, concatena como string.
- DEL elimina la variable si existe; si no, no hace nada.
- SET asigna directamente el valor.
"""

from __future__ import annotations
from typing import Dict


# ------------------------------------------------------------------------------------
# Bloque desarrollado con asistencia de ChatGPT (GPT-5, OpenAI),
# adaptado a la estructura modular solicitada en el enunciado.
# ------------------------------------------------------------------------------------
class Database:
    """Base de datos simple clave→valor (str)."""

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}

    # --------- Helpers ---------
    @staticmethod
    def _is_intlike(s: str) -> bool:
        """True si s representa un entero no negativo (según .isdigit())."""
        return isinstance(s, str) and s.isdigit()

    # --------- API pública ---------
    def set(self, var: str, value: str) -> None:
        """Asigna un valor directamente."""
        self._store[var] = value

    def add(self, var: str, value: str) -> None:
        """Suma o concatena según tipo."""
        if var not in self._store:
            self._store[var] = value
            return

        current = self._store[var]
        if self._is_intlike(current) and self._is_intlike(value):
            self._store[var] = str(int(current) + int(value))
        else:
            self._store[var] = f"{current}{value}"

    def delete(self, var: str) -> None:
        """Elimina una variable si existe."""
        self._store.pop(var, None)

    def snapshot(self) -> Dict[str, str]:
        """Copia del estado actual de la base."""
        return dict(self._store)

    def log_value(self, var: str) -> str:
        """Devuelve el valor o 'Variable no existe'."""
        return self._store.get(var, "Variable no existe")

    def apply_action(self, action: str) -> None:
        """
        Aplica una acción tipo:
            SET-var-valor
            ADD-var-valor
            DEL-var
        """
        parts = action.split("-", 2)
        if not parts:
            return

        cmd = parts[0]
        if cmd == "DEL" and len(parts) >= 2:
            self.delete(parts[1])
            return

        if cmd in ("SET", "ADD") and len(parts) >= 3:
            var, val = parts[1], parts[2]
            if cmd == "SET":
                self.set(var, val)
            else:
                self.add(var, val)
