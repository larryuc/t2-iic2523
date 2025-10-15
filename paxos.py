# ------------------------------------------------------------------------------------
# Pontificia Universidad Católica de Chile
# Escuela de Ingeniería — Departamento de Ciencia de la Computación
# Curso: IIC2523 - Sistemas Distribuidos
# Evaluación: Tarea 2 - Simulación de algoritmos de consenso (Paxos y Raft)
#
# Archivo: paxos.py
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

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from database1 import Database


# ------------------------------------------------------------------------------------
# Implementación simplificada de Paxos (alineada al formato de los casos del curso)
# ------------------------------------------------------------------------------------

@dataclass
class AcceptorState:
    active: bool = True
    promised_n: int = 0
    accepted_n: int = 0
    accepted_val: Optional[str] = None


class PaxosSimulator:
    """
    Simulador de Paxos según el enunciado del curso.
    Reglas:
      - Prepare;Proposer;n
      - Accept;Proposer;n;action
      - Learn
      - Start;A / Stop;A
      - Log;var
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self.db = Database()

        self.acceptors: Dict[str, AcceptorState] = {}
        self.proposers: Set[str] = set()
        # (proposer, n) → (ok_acceptors, suggested_val, max_accepted_n)
        self.prepare_info: Dict[Tuple[str, int], Tuple[Set[str], Optional[str], int]] = {}
        self.log_lines: List[str] = []

    # ----------------------- Utilidades -----------------------
    @staticmethod
    def _clean(line: str) -> str:
        if "#" in line:
            line = line.split("#", 1)[0]
        return line.strip()

    def _majority_threshold(self) -> int:
        return (len(self.acceptors) // 2) + 1

    # ----------------------- Eventos --------------------------
    def _event_prepare(self, proposer: str, n: int) -> None:
        ok: Set[str] = set()
        suggested_val: Optional[str] = None
        max_acc_n = -1

        for aid, st in self.acceptors.items():
            if not st.active:
                continue
            if n > st.promised_n:
                st.promised_n = n
                ok.add(aid)
                if st.accepted_val is not None and st.accepted_n > max_acc_n:
                    max_acc_n = st.accepted_n
                    suggested_val = st.accepted_val

        self.prepare_info[(proposer, n)] = (ok, suggested_val, max_acc_n)

    def _event_accept(self, proposer: str, n: int, action: str) -> None:
        key = (proposer, n)
        info = self.prepare_info.get(key)
        if not info:
            return
        ok_set, suggested_val, _ = info
        if len(ok_set) < self._majority_threshold():
            return

        value_to_accept = suggested_val if suggested_val is not None else action
        for aid, st in self.acceptors.items():
            if not st.active:
                continue
            if n >= st.promised_n:
                st.accepted_n = n
                st.accepted_val = value_to_accept

    def _event_learn(self) -> None:
        count: Dict[str, int] = {}
        for st in self.acceptors.values():
            if st.accepted_val is not None:
                count[st.accepted_val] = count.get(st.accepted_val, 0) + 1

        if not count:
            return

        winner, votes = max(count.items(), key=lambda kv: kv[1])
        if votes >= self._majority_threshold():
            self.db.apply_action(winner)
            for st in self.acceptors.values():
                if st.active:
                    st.promised_n = 0
                    st.accepted_n = 0
                    st.accepted_val = None
            self.prepare_info.clear()

    def _event_log(self, var: str) -> None:
        self.log_lines.append(f"{var}={self.db.log_value(var)}")

    def _event_start(self, aid: str) -> None:
        if aid in self.acceptors:
            self.acceptors[aid].active = True

    def _event_stop(self, aid: str) -> None:
        if aid in self.acceptors:
            self.acceptors[aid].active = False

    # ----------------------- Ejecución ------------------------
    def run(self) -> Tuple[List[str], Dict[str, str]]:
        with open(self.path, "r", encoding="utf-8") as f:
            lines = [self._clean(x) for x in f if self._clean(x)]

        if not lines:
            # Sin definiciones → sin logs y BD vacía
            return self.log_lines, self.db.snapshot()

        # Primera línea: aceptores
        acc_line = lines[0]
        acc_ids = [x.strip() for x in acc_line.split(";") if x.strip()]
        self.acceptors = {aid: AcceptorState(active=True) for aid in acc_ids}

        # Segunda línea: proponentes
        if len(lines) >= 2:
            prop_line = lines[1]
            prop_ids = [x.strip() for x in prop_line.split(";") if x.strip()]
            self.proposers = set(prop_ids)
            idx = 2
        else:
            idx = 1
            pass

        # Procesar eventos
        for line in lines[idx:]:
            parts = line.split(";")
            cmd = parts[0]

            if cmd == "Prepare" and len(parts) == 3:
                proposer = parts[1]
                try:
                    n = int(parts[2])
                except ValueError:
                    continue
                if proposer in self.proposers:
                    self._event_prepare(proposer, n)

            elif cmd == "Accept" and len(parts) >= 4:
                proposer = parts[1]
                try:
                    n = int(parts[2])
                except ValueError:
                    continue
                action = ";".join(parts[3:])
                if proposer in self.proposers:
                    self._event_accept(proposer, n, action)

            elif cmd == "Learn":
                self._event_learn()

            elif cmd == "Log" and len(parts) == 2:
                self._event_log(parts[1])

            elif cmd == "Start" and len(parts) == 2:
                self._event_start(parts[1])

            elif cmd == "Stop" and len(parts) == 2:
                self._event_stop(parts[1])

        # Importante:
        # - NO añadimos "No hubo logs" aquí.
        #   Devolvemos lista vacía si no hubo eventos Log para que main imprima:
        #   "No hubo logs" y, además, "No hay datos" cuando el snapshot está vacío.
        return self.log_lines, self.db.snapshot()
