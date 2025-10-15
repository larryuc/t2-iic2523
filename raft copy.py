# ------------------------------------------------------------------------------------
# Pontificia Universidad Católica de Chile
# Escuela de Ingeniería — Departamento de Ciencia de la Computación
# Curso: IIC2523 - Sistemas Distribuidos
# Evaluación: Tarea 2 - Simulación de algoritmos de consenso (Paxos y Raft)
#
# Archivo: raft.py
# Autor: Larry Andrés Uribe Araya
# ------------------------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from database2 import Database


@dataclass
class NodeState:
    active: bool = True
    timeout: int = 0
    term: int = 0
    log: List[Tuple[int, str]] = field(default_factory=list)


class RaftSimulator:
    """Simulador simplificado de Raft adaptado al formato de casos."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.db = Database()
        self.nodes: Dict[str, NodeState] = {}
        self.leader: Optional[str] = None
        self.term: int = 0
        self.commit_index: int = 0
        self.last_applied: int = 0

    @staticmethod
    def _clean(line: str) -> str:
        if "#" in line:
            before, _, _ = line.partition("#")
            line = before
        return line.strip()

    @staticmethod
    def _normalize_key(cmd: str) -> str:
        """Normaliza las claves en los comandos Raft."""
        if not cmd:
            return cmd
        op = cmd.split("-", 1)[0]
        parts = cmd.split("-", 2)
        if len(parts) >= 2:
            key = parts[1].replace("_", " ")
            if op in ("SET", "ADD", "DEL"):
                parts[1] = key
                return "-".join(parts)
        return cmd

    def _active_ids(self) -> List[str]:
        return [nid for nid, st in self.nodes.items() if st.active]

    def _majority(self) -> int:
        """Calcula mayoría sobre TOTAL de nodos del cluster."""
        total = len(self.nodes)
        return (total // 2) + 1

    def _pick_leader(self):
        print(
            "\n[DEBUG] ===== ELECCIÓN DE NUEVO LÍDER (GARANTIZAR PREFIJO COMPROMETIDO) =====")
        activos = self._active_ids()
        print(f"[DEBUG] Activos: {activos} / Total: {len(self.nodes)}")

        if not activos:
            print("[DEBUG] ❌ No hay candidatos activos.")
            self.leader = None
            return

        # Elegir por log más largo (empate → menor timeout)
        candidato = max(
            activos,
            key=lambda nid: (
                len(self.nodes[nid].log), -self.nodes[nid].timeout)
        )

        # Avanza término y fija líder
        self.term += 1
        self.nodes[candidato].term = self.term
        self.leader = candidato

        print(f"[DEBUG] 🏆 Nuevo líder: {self.leader} (term={self.term})")
        print("[DEBUG] Logs ANTES de la elección:")
        for nid, st in self.nodes.items():
            print(
                f"   - {nid}: activo={st.active}, timeout={st.timeout}, term={st.term}, log={st.log}")

        # ===== Reconstruir PREFIJO COMPROMETIDO por mayoría TOTAL (no solo activos) =====
        maj_total = self._majority()
        max_len = max((len(st.log) for st in self.nodes.values()), default=0)
        prefijo_comprometido = []

        for i in range(max_len):
            # Conteo de acciones por posición i en TODOS los nodos
            conteo = {}
            for nid, st in self.nodes.items():
                if len(st.log) > i:
                    action = st.log[i][1]
                    conteo[action] = conteo.get(action, 0) + 1

            if not conteo:
                print(
                    f"[DEBUG] Pos {i}: sin entradas en ningún nodo → cortar prefijo.")
                break

            mejor_action, votos = max(conteo.items(), key=lambda x: x[1])
            print(
                f"[DEBUG] Pos {i}: conteo={conteo} → '{mejor_action}' ({votos}/{maj_total})")

            if votos >= maj_total:
                # término más común entre los que tienen esta acción en i
                terminos = [
                    self.nodes[nid].log[i][0]
                    for nid, st in self.nodes.items()
                    if len(st.log) > i and st.log[i][1] == mejor_action
                ]
                term_comun = max(
                    set(terminos), key=terminos.count) if terminos else self.term
                prefijo_comprometido.append((term_comun, mejor_action))
                print(
                    f"[DEBUG] ✅ Prefijo comprometido incluye pos {i}: '{mejor_action}', term común={term_comun}")
            else:
                print(
                    f"[DEBUG] ⚠️ Sin mayoría TOTAL en pos {i} → detener prefijo.")
                break

        # ===== Asegurar que el líder contenga el prefijo comprometido =====
        lider_log_actual = list(self.nodes[self.leader].log)
        print(
            f"[DEBUG] Log candidato ANTES de forzar prefijo: {lider_log_actual}")
        # Forzamos el prefijo comprometido y luego anexamos el sufijo especulativo
        # del candidato (si existe)
        if len(prefijo_comprometido) > 0:
            sufijo_candidato = lider_log_actual[len(prefijo_comprometido):] if len(
                lider_log_actual) > len(prefijo_comprometido) else []
            nuevo_log_lider = prefijo_comprometido + sufijo_candidato
        else:
            # Si no hubo ningún prefijo con mayoría, deja el log tal como está
            nuevo_log_lider = lider_log_actual

        self.nodes[self.leader].log = nuevo_log_lider
        print(f"[DEBUG] ✔ Prefijo comprometido garantizado en líder.")
        print(
            f"[DEBUG] Log líder FINAL tras elección: {self.nodes[self.leader].log}")
        print("[DEBUG] ===== FIN ELECCIÓN LÍDER =====\n")

    def _recompute_commit_and_apply(self):
        """Recalcula commit_index y aplica a la BD según Raft (directa e indirecta)."""
        if not self.leader or self.leader not in self.nodes:
            print("[DEBUG] ❌ No hay líder válido para commit.\n")
            return

        leader_state = self.nodes[self.leader]
        if not leader_state.active:
            print(f"[DEBUG] ⚠️ Líder {self.leader} inactivo, no se consolida.\n")
            return

        leader_log = leader_state.log
        majority = self._majority()
        print(f"[DEBUG] === RECOMPUTE COMMIT === líder={self.leader}, term={self.term}")
        print(f"[DEBUG] Log líder actual: {leader_log}")
        print(f"[DEBUG] Mayoría requerida (sobre total): {majority}")

        indices_con_mayoria = []
        for i, (_, action) in enumerate(leader_log):
            # Cuenta en TODOS los nodos del cluster (activos o no), por posición i
            count = sum(
                1 for nid, st in self.nodes.items()
                if len(st.log) > i and st.log[i][1] == action
            )
            print(f"[DEBUG]   Entrada {i}: acción={action}, réplica={count}")
            if count >= majority:
                indices_con_mayoria.append(i)

        if not indices_con_mayoria:
            print("[DEBUG] ⚠️ Ninguna entrada alcanzó mayoría.")
            # 🔁 AUN ASÍ, reaplicamos la BD con lo ya comprometido (si lo hay)
            print(f"[DEBUG] 🔁 Reaplicando BD con commit_index vigente={self.commit_index}")
            self.db = Database()
            for _, action in leader_log[:self.commit_index]:
                print(f"[DEBUG] ✅ Aplicando acción consolidada: {action}")
                self.db.apply_action(action)
            print(f"[DEBUG] === FIN RECOMPUTE === commit_index={self.commit_index}\n")
            return

        # Último índice con mayoría cuyo término es el término ACTUAL del líder
        # (consolidación directa)
        idx_term_actual = max(
            (i for i in indices_con_mayoria if leader_log[i][0] == self.term),
            default=-1
        )
        print(f"[DEBUG] Índices con mayoría: {indices_con_mayoria}")
        print(f"[DEBUG] Último índice con término actual={self.term}: {idx_term_actual}")

        # Regla Raft:
        # - Si hay al menos una entrada del término actual con mayoría (directa),
        #   se puede avanzar commit hasta la ÚLTIMA entrada con mayoría (indirecta para previas).
        if idx_term_actual >= 0:
            new_commit = max(self.commit_index, indices_con_mayoria[-1] + 1)
            print("[DEBUG] ✅ Consolidación directa detectada (término actual).")
        else:
            new_commit = self.commit_index
            print("[DEBUG] ℹ️ Sin consolidación directa del término actual; commit_index se mantiene.")

        print(f"[DEBUG] commit_index {self.commit_index} → {new_commit}")
        self.commit_index = new_commit
        self.last_applied = self.commit_index

        # ⛑️ Reaplicar SIEMPRE la BD hasta commit_index (aunque no haya aumentado),
        # para reflejar el log del líder actual tras cambios de liderazgo/propagación.
        print(f"[DEBUG] 🔁 Reaplicando BD con commit_index={self.commit_index}")
        self.db = Database()
        for _, action in leader_log[:self.commit_index]:
            print(f"[DEBUG] ✅ Aplicando acción consolidada: {action}")
            self.db.apply_action(action)

        print(f"[DEBUG] === FIN RECOMPUTE === commit_index={self.commit_index}\n")

    def _send(self, action: str) -> None:
        """El líder agrega la acción a su log."""
        print(f"[SEND] Acción recibida: {action}")
        action = self._normalize_key(action)

        if not self.leader or not self.nodes.get(self.leader, NodeState()).active:
            print(f"[DEBUG] El líder está inactivo. No se procesa el Send.")
            return

        st = self.nodes[self.leader]
        st.log.append((self.term, action))
        print(f"[DEBUG] Log del líder {self.leader}: {st.log}")

    def _spread(self, targets: Optional[List[str]]) -> None:
        """Propaga el log del líder a otros nodos activos."""
        if not self.leader or self.leader not in self.nodes:
            print("[DEBUG] ❌ No hay líder válido en _spread.")
            return

        if not self.nodes[self.leader].active:
            print("[DEBUG] ⚠️ El líder está inactivo en _spread.")
            return

        leader_log = self.nodes[self.leader].log
        if not leader_log:
            print("[DEBUG] ℹ️ Nada que propagar (log vacío en líder).")
            return

        if not targets:
            dests = [nid for nid in self._active_ids() if nid != self.leader]
        else:
            dests = [t for t in targets if t in self._active_ids()
                     and t != self.leader]

        print(
            f"[SPREAD] Desde líder {self.leader} hacia {dests} | log_líder={leader_log}")

        for d in dests:
            dst = self.nodes[d]
            dst.log = [entry for entry in leader_log]
            print(f"[DEBUG] Nodo {d} sincronizado. Log destino: {dst.log}")

        # Recalcular consolidaciones inmediatamente después de propagar
        self._recompute_commit_and_apply()

    def _event_start(self, nid: str) -> None:
        if nid in self.nodes:
            self.nodes[nid].active = True
            print(f"[EVENT] Nodo {nid} iniciado.")

            if not self.leader or not self.nodes.get(self.leader, NodeState()).active:
                self._pick_leader()
                # Después de elegir líder, recalcular consolidaciones
                self._recompute_commit_and_apply()

    def _event_stop(self, nid: str) -> None:
        if nid in self.nodes:
            was_leader = (nid == self.leader)
            self.nodes[nid].active = False
            print(f"[EVENT] Nodo {nid} detenido.")

            if was_leader:
                self._pick_leader()
                # Después de elegir líder, recalcular consolidaciones
                if self.leader:
                    self._recompute_commit_and_apply()

    def _event_log(self, var: str, out: List[str]) -> None:
        self._recompute_commit_and_apply()
        val = self.db.log_value(var)
        print(f"[LOG] {var}={val}")
        out.append(f"{var}={val}")

    def run(self) -> Tuple[List[str], Dict[str, str]]:
        print(f"[RUN] Ejecutando archivo: {self.path}")
        with open(self.path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        lines = [self._clean(x) for x in raw_lines]
        lines = [x for x in lines if x]
        print(f"[DEBUG] Total líneas procesadas: {len(lines)}")

        out: List[str] = []
        if not lines:
            print("[ERROR] Archivo vacío tras limpieza.")
            return out, self.db.snapshot()

        # Parsear nodos
        node_specs = [x.strip() for x in lines[0].split(";") if x.strip()]
        print(f"[INIT] Definición de nodos: {node_specs}")

        for tok in node_specs:
            if "," in tok:
                nid, t = tok.split(",", 1)
                try:
                    timeout = int(t)
                except ValueError:
                    timeout = 0
            else:
                nid, timeout = tok, 0
            self.nodes[nid] = NodeState(True, timeout, 0)
            print(f"[INIT] Nodo {nid} creado (timeout={timeout})")

        # Elegir líder inicial
        self._pick_leader()
        print(f"[DEBUG] Líder inicial: {self.leader} (term={self.term})")

        # Procesar eventos
        for line in lines[1:]:
            if not line:
                continue
            print(f"[EVENT] Procesando línea: {line}")

            if line.startswith("Send;"):
                action = line.split(";", 1)[1].strip()
                self._send(action)

            elif line.startswith("Spread;"):
                inside = line.split(";", 1)[1].strip().strip("[]")
                targets = [t.strip() for t in inside.split(",") if t.strip()]
                self._spread(targets)

            elif line.startswith("Start;"):
                nid = line.split(";", 1)[1].strip()
                self._event_start(nid)

            elif line.startswith("Stop;"):
                nid = line.split(";", 1)[1].strip()
                self._event_stop(nid)

            elif line.startswith("Log;"):
                var = line.split(";", 1)[1].strip()
                self._event_log(var, out)

        self._recompute_commit_and_apply()
        print("[RUN] Ejecución finalizada. Estado final de BD:",
              self.db.snapshot())
        return out, self.db.snapshot()
